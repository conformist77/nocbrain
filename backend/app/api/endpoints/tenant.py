"""
NOCbRAIN Tenant API Endpoints
Multi-tenant dashboard and management APIs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.security import get_current_active_user, check_permissions
from app.models.user import User
from app.core.logic.knowledge_manager import knowledge_manager
from app.core.logic.reasoning_engine import reasoning_engine
from app.security_analyzer.pattern_engine import pattern_engine
from app.middleware.tenant import get_tenant_id, get_tenant_context
from app.schemas.tenant import (
    TenantDashboardResponse,
    TenantStatsResponse,
    TenantAnalysisRequest,
    TenantAnalysisResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/analyze-log", response_model=TenantAnalysisResponse)
async def analyze_tenant_log(
    request: TenantAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:analyze"]))
) -> Any:
    """Analyze log entry with tenant isolation"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(request)
        tenant_id = tenant_context["tenant_id"]
        
        # Add tenant_id to log data
        log_data = request.log_data.copy()
        log_data["tenant_id"] = tenant_id
        
        # Process log through reasoning engine with tenant isolation
        result = await reasoning_engine.process_log(log_data, tenant_id)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process log: {result['error']}"
            )
        
        response = TenantAnalysisResponse(
            log_id=log_data.get("id", "unknown"),
            tenant_id=tenant_id,
            status=result["status"],
            event_type=result["event_type"],
            priority=result["priority"],
            processing_time=result.get("processing_time", 0.0),
            ai_response=result.get("ai_response", {}),
            timestamp=result["timestamp"]
        )
        
        # Log analysis in background
        background_tasks.add_task(
            _log_tenant_analysis,
            current_user.id,
            tenant_id,
            log_data,
            result
        )
        
        logger.info(f"Log analyzed for tenant {tenant_id} by user {current_user.username}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze tenant log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze log entry"
        )


@router.get("/dashboard", response_model=TenantDashboardResponse)
async def get_tenant_dashboard(
    time_window: int = 3600,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:read"]))
) -> Any:
    """Get tenant-specific dashboard data"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Get reasoning engine stats for tenant
        reasoning_stats = await reasoning_engine.get_tenant_stats(tenant_id)
        
        # Get security stats for tenant
        security_stats = await pattern_engine.get_tenant_stats(tenant_id, time_window)
        
        # Get knowledge stats for tenant
        knowledge_stats = await knowledge_manager.get_tenant_stats(tenant_id)
        
        # Calculate metrics
        total_logs_analyzed = reasoning_stats.get("total_processed", 0)
        threats_detected = security_stats.get("threats_detected", 0)
        knowledge_coverage = knowledge_stats.get("total_documents", 0)
        
        # Calculate coverage percentage (based on knowledge types)
        knowledge_types = knowledge_stats.get("knowledge_types", [])
        coverage_percentage = min(100, (knowledge_coverage / len(knowledge_types)) * 100) if knowledge_types else 0
        
        response = TenantDashboardResponse(
            tenant_id=tenant_id,
            time_window=time_window,
            total_logs_analyzed=total_logs_analyzed,
            threats_detected=threats_detected,
            knowledge_base_coverage=coverage_percentage,
            knowledge_documents=knowledge_coverage,
            reasoning_engine_stats=reasoning_stats,
            security_stats=security_stats,
            knowledge_stats=knowledge_stats,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Dashboard retrieved for tenant {tenant_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get tenant dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant dashboard"
        )


@router.get("/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    time_window: int = 3600,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:read"]))
) -> Any:
    """Get detailed tenant statistics"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Get stats from all components
        reasoning_stats = await reasoning_engine.get_tenant_stats(tenant_id)
        security_stats = await pattern_engine.get_tenant_stats(tenant_id, time_window)
        knowledge_stats = await knowledge_manager.get_tenant_stats(tenant_id)
        
        response = TenantStatsResponse(
            tenant_id=tenant_id,
            time_window=time_window,
            reasoning_engine=reasoning_stats,
            security_analyzer=security_stats,
            knowledge_manager=knowledge_stats,
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Stats retrieved for tenant {tenant_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get tenant stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant statistics"
        )


@router.post("/knowledge/query")
async def query_tenant_knowledge(
    query: str,
    knowledge_type: Optional[str] = None,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    include_global: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:knowledge:read"]))
) -> Any:
    """Query knowledge base with tenant isolation"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Query knowledge with tenant isolation
        results = await knowledge_manager.query_knowledge(
            query=query,
            tenant_id=tenant_id,
            knowledge_type=knowledge_type,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            include_global=include_global
        )
        
        # Filter results for tenant
        filtered_results = []
        for result in results:
            metadata = result["metadata"]
            
            # Allow if it's tenant's own document or global
            if (metadata.get("tenant_id") == tenant_id or 
                metadata.get("is_global", False)):
                filtered_results.append(result)
        
        logger.info(f"Knowledge query completed for tenant {tenant_id}: {len(filtered_results)} results")
        return {
            "tenant_id": tenant_id,
            "query": query,
            "results": filtered_results,
            "total_results": len(filtered_results),
            "knowledge_type": knowledge_type,
            "include_global": include_global,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to query tenant knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query knowledge base"
        )


@router.post("/knowledge/add")
async def add_tenant_knowledge(
    content: str,
    metadata: Dict[str, Any],
    knowledge_type: Optional[str] = None,
    is_global: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:knowledge:write"]))
) -> Any:
    """Add knowledge with tenant isolation"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Check if user can add global knowledge
        if is_global and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can add global knowledge"
            )
        
        # Add metadata about the user and tenant
        metadata["added_by"] = current_user.username
        metadata["added_at"] = datetime.utcnow().isoformat()
        metadata["tenant_id"] = tenant_id
        
        # Add to knowledge manager
        result = await knowledge_manager.add_knowledge(
            content=content,
            metadata=metadata,
            tenant_id="global" if is_global else tenant_id,
            knowledge_type=knowledge_type,
            is_global=is_global
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add knowledge: {result['error']}"
            )
        
        logger.info(f"Knowledge added for tenant {tenant_id}: {result['chunks']} chunks")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add tenant knowledge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add knowledge"
        )


@router.get("/knowledge/stats")
async def get_tenant_knowledge_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:knowledge:read"]))
) -> Any:
    """Get tenant knowledge statistics"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Get stats
        stats = await knowledge_manager.get_tenant_stats(tenant_id)
        
        logger.info(f"Knowledge stats retrieved for tenant {tenant_id}")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get tenant knowledge stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get knowledge statistics"
        )


@router.post("/security/analyze")
async def analyze_tenant_security(
    log_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:security:analyze"]))
) -> Any:
    """Analyze security event with tenant isolation"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Add tenant_id to log data
        log_data["tenant_id"] = tenant_id
        
        # Analyze through pattern engine
        threats = await pattern_engine.analyze_log(log_data)
        
        # Filter threats for tenant
        tenant_threats = []
        for threat in threats:
            # Add tenant context to threat
            threat["tenant_id"] = tenant_id
            tenant_threats.append(threat)
        
        logger.info(f"Security analysis completed for tenant {tenant_id}: {len(tenant_threats)} threats")
        return {
            "tenant_id": tenant_id,
            "log_id": log_data.get("id", "unknown"),
            "threats_detected": len(tenant_threats),
            "threats": tenant_threats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze tenant security: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze security event"
        )


@router.get("/security/summary")
async def get_tenant_security_summary(
    time_window: int = 3600,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:security:read"]))
) -> Any:
    """Get tenant security summary"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Get threat summary
        summary = await pattern_engine.get_tenant_threat_summary(tenant_id, time_window)
        
        logger.info(f"Security summary retrieved for tenant {tenant_id}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get tenant security summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security summary"
        )


@router.get("/health")
async def tenant_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["tenant:read"]))
) -> Any:
    """Health check for tenant services"""
    try:
        # Get tenant context
        tenant_context = get_tenant_context(current_user)
        tenant_id = tenant_context["tenant_id"]
        
        # Check all components
        reasoning_stats = await reasoning_engine.get_tenant_stats(tenant_id)
        knowledge_stats = await knowledge_manager.get_tenant_stats(tenant_id)
        security_stats = await pattern_engine.get_tenant_stats(tenant_id)
        
        # Determine overall health
        if not reasoning_stats.get("is_running", False):
            return {
                "status": "unhealthy",
                "tenant_id": tenant_id,
                "reason": "Reasoning engine is not running"
            }
        
        return {
            "status": "healthy",
            "tenant_id": tenant_id,
            "reasoning_engine": {
                "is_running": reasoning_stats.get("is_running", False),
                "total_processed": reasoning_stats.get("total_processed", 0)
            },
            "knowledge_manager": {
                "total_documents": knowledge_stats.get("total_documents", 0),
                "collection_name": knowledge_stats.get("collection_name", "unknown")
            },
            "security_analyzer": {
                "total_events": security_stats.get("total_events", 0),
                "threats_detected": security_stats.get("threats_detected", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Tenant health check failed: {e}")
        return {
            "status": "error",
            "tenant_id": tenant_context.get("tenant_id", "unknown"),
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Background tasks
async def _log_tenant_analysis(user_id: int, tenant_id: str, log_data: Dict[str, Any], result: Dict[str, Any]):
    """Log tenant analysis result to database"""
    try:
        logger.info(f"Tenant analysis result for user {user_id}, tenant {tenant_id}: {result['event_type']}")
    except Exception as e:
        logger.error(f"Failed to log tenant analysis result: {e}")
