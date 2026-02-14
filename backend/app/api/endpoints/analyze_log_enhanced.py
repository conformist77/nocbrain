#!/usr/bin/env python3
"""
NOCbRAIN Enhanced API Endpoint
Updated /analyze-log endpoint with tenant_id and structured NOC Action Plans
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.logic.reasoning_engine import reasoning_engine
from app.core.logic.knowledge_manager import knowledge_manager
from app.core.logic.security_analyzer import security_analyzer
from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter()

class LogAnalysisRequest(BaseModel):
    """Request model for log analysis with tenant isolation"""
    log_content: str = Field(..., description="The log content to analyze")
    tenant_id: str = Field(..., description="Tenant identifier for data isolation")
    include_global_knowledge: bool = Field(True, description="Include global knowledge in results")
    category_filter: Optional[str] = Field(None, description="Filter knowledge by category")
    priority_level: str = Field("medium", description="Analysis priority level")

class ActionStep(BaseModel):
    """Single step in NOC action plan"""
    step_number: int = Field(..., description="Step sequence number")
    action: str = Field(..., description="Action to perform")
    command: Optional[str] = Field(None, description="Command to execute")
    expected_result: str = Field(..., description="Expected result of this step")
    safety_check: Optional[str] = Field(None, description="Safety check before execution")
    estimated_time: str = Field(..., description="Estimated time to complete")

class NOCActionPlan(BaseModel):
    """Structured NOC Action Plan"""
    title: str = Field(..., description="Action plan title")
    priority: str = Field(..., description="Priority level (low/medium/high/critical)")
    estimated_resolution_time: str = Field(..., description="Estimated time to resolve")
    required_tools: List[str] = Field(..., description="Tools needed for resolution")
    safety_checks: List[str] = Field(..., description="Safety checks to perform")
    verification_steps: List[str] = Field(..., description="Steps to verify resolution")
    action_steps: List[ActionStep] = Field(..., description="Detailed action steps")
    rollback_plan: Optional[str] = Field(None, description="Rollback plan if needed")

class KnowledgeSource(BaseModel):
    """Knowledge source reference"""
    content: str = Field(..., description="Knowledge content")
    source: str = Field(..., description="Source document")
    category: str = Field(..., description="Knowledge category")
    relevance_score: float = Field(..., description="Relevance to the issue")
    tenant_id: str = Field(..., description="Tenant ID of the knowledge source")

class LogAnalysisResponse(BaseModel):
    """Response model for log analysis"""
    tenant_id: str = Field(..., description="Tenant identifier")
    analysis_timestamp: str = Field(..., description="When analysis was performed")
    issue_summary: str = Field(..., description="Summary of the identified issue")
    severity: str = Field(..., description="Issue severity level")
    action_plan: NOCActionPlan = Field(..., description="Structured NOC action plan")
    knowledge_sources: List[KnowledgeSource] = Field(..., description="Relevant knowledge sources")
    security_analysis: Optional[Dict[str, Any]] = Field(None, description="Security analysis results")
    recommendations: List[str] = Field(..., description="Additional recommendations")

@router.post("/analyze-log", response_model=LogAnalysisResponse)
async def analyze_log_with_tenant(
    request: LogAnalysisRequest,
    token: str = Depends(security)
):
    """
    Analyze log with strict tenant isolation and structured NOC Action Plan
    
    This endpoint provides:
    - Strict multi-tenant data isolation
    - Combined global and tenant-specific knowledge
    - Structured NOC Action Plans
    - Security analysis integration
    - Real-time troubleshooting guidance
    """
    
    try:
        logger.info(f"Analyzing log for tenant {request.tenant_id}")
        
        # Step 1: Analyze log with reasoning engine
        reasoning_result = await reasoning_engine.analyze_log(
            log_content=request.log_content,
            tenant_id=request.tenant_id,
            priority=request.priority_level
        )
        
        # Step 2: Search relevant knowledge with strict tenant isolation
        knowledge_results = await knowledge_manager.search_knowledge(
            tenant_id=request.tenant_id,
            query=reasoning_result.get("issue_description", ""),
            category=request.category_filter,
            limit=5,
            include_global=request.include_global_knowledge
        )
        
        # Step 3: Perform security analysis if needed
        security_result = None
        if any(keyword in request.log_content.lower() for keyword in ["attack", "breach", "unauthorized", "malicious"]):
            security_result = await security_analyzer.analyze_security_event(
                log_content=request.log_content,
                tenant_id=request.tenant_id
            )
        
        # Step 4: Generate structured NOC Action Plan
        action_plan = await _generate_noc_action_plan(
            reasoning_result=reasoning_result,
            knowledge_results=knowledge_results,
            security_result=security_result,
            tenant_id=request.tenant_id
        )
        
        # Step 5: Format knowledge sources
        knowledge_sources = [
            KnowledgeSource(
                content=result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"],
                source=result["metadata"].get("source", "unknown"),
                category=result["metadata"].get("category", "general"),
                relevance_score=result["score"],
                tenant_id=result["tenant_id"]
            )
            for result in knowledge_results
        ]
        
        # Step 6: Generate recommendations
        recommendations = await _generate_recommendations(
            reasoning_result=reasoning_result,
            knowledge_results=knowledge_results,
            security_result=security_result
        )
        
        # Build response
        response = LogAnalysisResponse(
            tenant_id=request.tenant_id,
            analysis_timestamp=datetime.utcnow().isoformat(),
            issue_summary=reasoning_result.get("issue_summary", "Issue analysis completed"),
            severity=reasoning_result.get("severity", "medium"),
            action_plan=action_plan,
            knowledge_sources=knowledge_sources,
            security_analysis=security_result,
            recommendations=recommendations
        )
        
        logger.info(f"Analysis completed for tenant {request.tenant_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing log for tenant {request.tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Log analysis failed: {str(e)}"
        )

async def _generate_noc_action_plan(
    reasoning_result: Dict[str, Any],
    knowledge_results: List[Dict[str, Any]],
    security_result: Optional[Dict[str, Any]],
    tenant_id: str
) -> NOCActionPlan:
    """Generate structured NOC Action Plan based on analysis results"""
    
    issue_type = reasoning_result.get("issue_type", "unknown")
    severity = reasoning_result.get("severity", "medium")
    
    # Determine priority and timing based on severity
    priority_map = {
        "low": ("low", "30 minutes"),
        "medium": ("medium", "15 minutes"),
        "high": ("high", "5 minutes"),
        "critical": ("critical", "immediate")
    }
    
    priority, estimated_time = priority_map.get(severity, ("medium", "15 minutes"))
    
    # Generate action steps based on issue type and knowledge
    action_steps = []
    
    if issue_type == "network_connectivity":
        action_steps = [
            ActionStep(
                step_number=1,
                action="Verify physical connectivity",
                command="show interfaces status",
                expected_result="Interface status shows up/up",
                safety_check="Verify no maintenance window is active",
                estimated_time="2 minutes"
            ),
            ActionStep(
                step_number=2,
                action="Check layer 2 configuration",
                command="show vlan brief",
                expected_result="VLAN configuration is correct",
                safety_check="Document current VLAN assignments",
                estimated_time="3 minutes"
            ),
            ActionStep(
                step_number=3,
                action="Verify routing configuration",
                command="show ip route",
                expected_result="Routing table contains expected routes",
                safety_check="Backup current routing configuration",
                estimated_time="5 minutes"
            )
        ]
    elif issue_type == "security_incident":
        action_steps = [
            ActionStep(
                step_number=1,
                action="Isolate affected systems",
                command="block ip [malicious_ip]",
                expected_result="Malicious IP is blocked",
                safety_check="Verify legitimate traffic is not affected",
                estimated_time="1 minute"
            ),
            ActionStep(
                step_number=2,
                action="Analyze attack vector",
                command="show log | include [attack_pattern]",
                expected_result="Attack pattern identified",
                safety_check="Preserve forensic evidence",
                estimated_time="10 minutes"
            )
        ]
    else:
        # Generic troubleshooting steps
        action_steps = [
            ActionStep(
                step_number=1,
                action="Gather diagnostic information",
                command="show logging",
                expected_result="Relevant log entries collected",
                safety_check="Ensure logging buffer is not full",
                estimated_time="3 minutes"
            ),
            ActionStep(
                step_number=2,
                action="Apply relevant knowledge base solution",
                command="Refer to knowledge base",
                expected_result="Solution from knowledge base applied",
                safety_check="Test in non-production environment first",
                estimated_time="10 minutes"
            )
        ]
    
    # Determine required tools
    required_tools = []
    if "network" in issue_type:
        required_tools.extend(["Network Analyzer", "Ping", "Traceroute"])
    if "security" in issue_type:
        required_tools.extend(["Security Scanner", "Firewall", "IDS"])
    required_tools.extend(["Terminal/SSH", "Log Analyzer"])
    
    # Generate safety checks
    safety_checks = [
        "Verify maintenance window if required",
        "Backup current configuration",
        "Document all changes",
        "Test in lab environment first"
    ]
    
    # Generate verification steps
    verification_steps = [
        "Verify service is operational",
        "Check monitoring dashboards",
        "Confirm user access restored",
        "Document resolution in ticketing system"
    ]
    
    # Generate rollback plan
    rollback_plan = "Restore from backup configuration if issue persists after changes"
    
    return NOCActionPlan(
        title=f"Resolution Plan for {issue_type.replace('_', ' ').title()}",
        priority=priority,
        estimated_resolution_time=estimated_time,
        required_tools=required_tools,
        safety_checks=safety_checks,
        verification_steps=verification_steps,
        action_steps=action_steps,
        rollback_plan=rollback_plan
    )

async def _generate_recommendations(
    reasoning_result: Dict[str, Any],
    knowledge_results: List[Dict[str, Any]],
    security_result: Optional[Dict[str, Any]]
) -> List[str]:
    """Generate additional recommendations based on analysis"""
    
    recommendations = []
    
    # Add recommendations based on reasoning
    if reasoning_result.get("severity") == "critical":
        recommendations.append("Escalate to senior network administrator immediately")
        recommendations.append("Consider implementing emergency maintenance procedures")
    
    # Add recommendations based on knowledge results
    if knowledge_results:
        best_match = knowledge_results[0]  # Highest scoring result
        if best_match["score"] > 0.8:
            recommendations.append(f"High-confidence solution found in {best_match['metadata'].get('source', 'knowledge base')}")
    
    # Add security recommendations
    if security_result:
        if security_result.get("threat_level") == "high":
            recommendations.append("Implement additional security monitoring")
            recommendations.append("Review access logs for related activities")
    
    # Add general recommendations
    recommendations.extend([
        "Update documentation with lessons learned",
        "Consider implementing preventive monitoring",
        "Schedule regular system health checks"
    ])
    
    return recommendations[:5]  # Limit to top 5 recommendations

@router.get("/analyze-log/status")
async def get_analysis_status():
    """Get current analysis service status"""
    return {
        "service": "Log Analysis API",
        "status": "operational",
        "features": {
            "multi_tenant_isolation": True,
            "global_knowledge_integration": True,
            "structured_action_plans": True,
            "security_analysis": True,
            "real_time_analysis": True
        },
        "supported_categories": [
            "networking",
            "virtualization", 
            "orchestration",
            "security",
            "infrastructure"
        ],
        "tenant_isolation": "strict",
        "knowledge_sources": "global + tenant-specific"
    }
