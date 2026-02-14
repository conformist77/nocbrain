"""
NOCbRAIN Core Engine API Endpoints
Main API endpoints for RAG-powered NOC operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.core.security import get_current_active_user, check_permissions
from app.models.user import User
from app.core.logic.knowledge_manager import knowledge_manager
from app.core.logic.reasoning_engine import reasoning_engine
from app.schemas.core_engine import (
    LogAnalysisRequest, LogAnalysisResponse, 
    KnowledgeQueryRequest, KnowledgeQueryResponse,
    IncidentRequest, IncidentResponse,
    SystemStatusResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/core", tags=["core-engine"])


@router.post("/analyze-log", response_model=LogAnalysisResponse)
async def analyze_log(
    request: LogAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["core:analyze"]))
) -> Any:
    """Analyze log entry using RAG and AI reasoning"""
    try:
        # Process log through reasoning engine
        result = await reasoning_engine.process_log(request.log_data)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process log: {result['error']}"
            )
        
        # Build response
        response = LogAnalysisResponse(
            log_id=request.log_data.get("id", "unknown"),
            status=result["status"],
            event_type=result["event_type"],
            priority=result["priority"],
            processing_time=result.get("processing_time", 0.0),
            ai_response=result.get("ai_response", {}),
            timestamp=result["timestamp"]
        )
        
        # Log analysis in background
        background_tasks.add_task(
            _log_analysis_result,
            current_user.id,
            request.log_data,
            result
        )
        
        logger.info(f"Log analyzed for user {current_user.username}: {result['event_type']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze log entry"
        )


@router.post("/analyze-batch", response_model=List[LogAnalysisResponse])
async def analyze_batch_logs(
    logs: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["core:analyze"]))
) -> Any:
    """Analyze multiple log entries in batch"""
    try:
        # Process logs through reasoning engine
        results = await reasoning_engine.batch_process_logs(logs)
        
        # Build responses
        responses = []
        for i, result in enumerate(results):
            if result["status"] == "success":
                response = LogAnalysisResponse(
                    log_id=logs[i].get("id", f"batch_{i}"),
                    status=result["status"],
                    event_type=result["event_type"],
                    priority=result["priority"],
                    processing_time=result.get("processing_time", 0.0),
                    ai_response=result.get("ai_response", {}),
                    timestamp=result["timestamp"]
                )
                responses.append(response)
        
        # Log batch analysis in background
        background_tasks.add_task(
            _log_batch_analysis_result,
            current_user.id,
            logs,
            results
        )
        
        logger.info(f"Batch analysis completed for user {current_user.username}: {len(logs)} logs")
        return responses
        
    except Exception as e:
        logger.error(f"Failed to analyze batch logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze batch logs"
        )


@router.post("/knowledge/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(
    request: KnowledgeQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["knowledge:read"]))
) -> Any:
    """Query knowledge base for relevant information"""
    try:
        # Query knowledge manager
        results = await knowledge_manager.query_knowledge(
            query=request.query,
            knowledge_type=request.knowledge_type,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        response = KnowledgeQueryResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            knowledge_type=request.knowledge_type,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Knowledge query completed for user {current_user.username}: {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Failed to query knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query knowledge base"
        )


@router.post("/knowledge/add")
async def add_knowledge(
    content: str,
    metadata: Dict[str, Any],
    knowledge_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["knowledge:write"]))
) -> Any:
    """Add new knowledge to the vector store"""
    try:
        # Add metadata about the user
        metadata["added_by"] = current_user.username
        metadata["added_at"] = datetime.utcnow().isoformat()
        
        # Add to knowledge manager
        result = await knowledge_manager.add_knowledge(
            content=content,
            metadata=metadata,
            knowledge_type=knowledge_type
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add knowledge: {result['error']}"
            )
        
        logger.info(f"Knowledge added by user {current_user.username}: {result['chunks']} chunks")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add knowledge"
        )


@router.post("/incident/generate-plan", response_model=IncidentResponse)
async def generate_noc_action_plan(
    request: IncidentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["incident:manage"]))
) -> Any:
    """Generate comprehensive NOC Action Plan for incident"""
    try:
        # Generate action plan through reasoning engine
        result = await reasoning_engine.generate_noc_action_plan(request.incident_data)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate action plan: {result['error']}"
            )
        
        response = IncidentResponse(
            incident_id=request.incident_data.get("id", "unknown"),
            status=result["status"],
            noc_action_plan=result.get("noc_action_plan", ""),
            knowledge_used=result.get("knowledge_used", []),
            timestamp=result["timestamp"]
        )
        
        # Log incident plan generation
        background_tasks.add_task(
            _log_incident_plan,
            current_user.id,
            request.incident_data,
            result
        )
        
        logger.info(f"NOC action plan generated for user {current_user.username}: incident {request.incident_data.get('id')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate NOC action plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate NOC action plan"
        )


@router.post("/incident/search-similar")
async def search_similar_incidents(
    incident_description: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["incident:read"]))
) -> Any:
    """Search for similar historical incidents"""
    try:
        results = await reasoning_engine.search_similar_incidents(
            incident_description=incident_description,
            limit=limit
        )
        
        logger.info(f"Similar incidents search completed for user {current_user.username}: {len(results)} results")
        return {
            "query": incident_description,
            "results": results,
            "total_results": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to search similar incidents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search similar incidents"
        )


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["system:read"]))
) -> Any:
    """Get comprehensive system status"""
    try:
        # Get stats from all components
        reasoning_stats = await reasoning_engine.get_stats()
        knowledge_stats = await knowledge_manager.get_knowledge_stats()
        
        response = SystemStatusResponse(
            status="healthy",
            reasoning_engine=reasoning_stats,
            knowledge_manager=knowledge_stats,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )


@router.post("/knowledge/index")
async def index_knowledge_base(
    background_tasks: BackgroundTasks,
    force_reindex: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["knowledge:admin"]))
) -> Any:
    """Index the entire knowledge base"""
    try:
        # Run indexing in background
        background_tasks.add_task(
            _index_knowledge_base_task,
            current_user.id,
            force_reindex
        )
        
        return {
            "status": "started",
            "message": "Knowledge base indexing started in background",
            "force_reindex": force_reindex,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start knowledge base indexing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start knowledge base indexing"
        )


@router.get("/health")
async def health_check() -> Any:
    """Health check endpoint"""
    try:
        # Check all components
        reasoning_stats = await reasoning_engine.get_stats()
        knowledge_stats = await knowledge_manager.get_knowledge_stats()
        
        # Determine overall health
        if not reasoning_stats.get("is_running", False):
            return {
                "status": "unhealthy",
                "reason": "Reasoning engine is not running",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if knowledge_stats.get("total_documents", 0) == 0:
            return {
                "status": "warning",
                "reason": "Knowledge base is empty",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "healthy",
            "reasoning_engine": reasoning_stats,
            "knowledge_manager": knowledge_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "reason": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Background tasks
async def _log_analysis_result(user_id: int, log_data: Dict[str, Any], result: Dict[str, Any]):
    """Log analysis result to database"""
    try:
        # This would log to audit table
        logger.info(f"Log analysis result for user {user_id}: {result['event_type']}")
    except Exception as e:
        logger.error(f"Failed to log analysis result: {e}")


async def _log_batch_analysis_result(user_id: int, logs: List[Dict[str, Any]], results: List[Dict[str, Any]]):
    """Log batch analysis result to database"""
    try:
        # This would log to audit table
        logger.info(f"Batch analysis result for user {user_id}: {len(logs)} logs processed")
    except Exception as e:
        logger.error(f"Failed to log batch analysis result: {e}")


async def _log_incident_plan(user_id: int, incident_data: Dict[str, Any], result: Dict[str, Any]):
    """Log incident plan generation to database"""
    try:
        # This would log to audit table
        logger.info(f"Incident plan generated for user {user_id}: incident {incident_data.get('id')}")
    except Exception as e:
        logger.error(f"Failed to log incident plan: {e}")


async def _index_knowledge_base_task(user_id: int, force_reindex: bool):
    """Background task to index knowledge base"""
    try:
        logger.info(f"Starting knowledge base indexing for user {user_id}")
        
        result = await knowledge_manager.index_knowledge_base(force_reindex=force_reindex)
        
        logger.info(f"Knowledge base indexing completed: {result}")
        
    except Exception as e:
        logger.error(f"Knowledge base indexing failed: {e}")
