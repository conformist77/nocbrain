from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any, Dict, Optional
from datetime import datetime, timedelta
import json
import asyncio

from app.core.database import get_db
from app.core.security import get_current_active_user, check_permissions
from app.models.user import User
from app.schemas.monitoring import (
    MetricsRequest, MetricsResponse, AgentRegistration,
    AgentResponse, AgentConfig, AlertRule, AlertResponse
)
from app.modules.monitoring.service import MonitoringService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
monitoring_service = MonitoringService()

@router.post("/metrics", response_model=Dict[str, Any])
async def receive_metrics(
    metrics_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:write"]))
) -> Any:
    """Receive metrics from monitoring agents"""
    try:
        # Decrypt metrics data if encrypted
        if 'data' in metrics_data:
            decrypted_data = monitoring_service.decrypt_metrics(metrics_data['data'])
            metrics = json.loads(decrypted_data)
        else:
            metrics = metrics_data
        
        # Process metrics in background
        background_tasks.add_task(
            monitoring_service.process_metrics,
            metrics,
            current_user.id
        )
        
        logger.info(f"Metrics received from agent {metrics.get('agent_id')}")
        
        return {
            "status": "received",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": metrics.get('agent_id')
        }
        
    except Exception as e:
        logger.error(f"Failed to process metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process metrics"
        )

@router.post("/heartbeat")
async def receive_heartbeat(
    heartbeat_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Receive heartbeat from monitoring agents"""
    try:
        result = await monitoring_service.update_agent_heartbeat(heartbeat_data)
        logger.debug(f"Heartbeat received from agent {heartbeat_data.get('agent_id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to process heartbeat: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process heartbeat"
        )

@router.post("/agents/register", response_model=AgentResponse)
async def register_agent(
    agent_data: AgentRegistration,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:write"]))
) -> Any:
    """Register a new monitoring agent"""
    try:
        agent = await monitoring_service.register_agent(agent_data, current_user.id)
        logger.info(f"Agent {agent.id} registered by user {current_user.username}")
        return agent
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/agents", response_model=List[AgentResponse])
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:read"]))
) -> Any:
    """Get list of registered monitoring agents"""
    try:
        agents = await monitoring_service.get_agents(
            db, skip, limit, status_filter, current_user.id
        )
        return agents
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agents"
        )

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:read"]))
) -> Any:
    """Get specific agent details"""
    try:
        agent = await monitoring_service.get_agent(db, agent_id, current_user.id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent"
        )

@router.put("/agents/{agent_id}/config", response_model=AgentResponse)
async def update_agent_config(
    agent_id: str,
    config: AgentConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:write"]))
) -> Any:
    """Update agent configuration"""
    try:
        agent = await monitoring_service.update_agent_config(
            db, agent_id, config, current_user.id
        )
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        logger.info(f"Agent {agent_id} config updated by user {current_user.username}")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent config {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:delete"]))
) -> Any:
    """Unregister monitoring agent"""
    try:
        success = await monitoring_service.delete_agent(db, agent_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        logger.info(f"Agent {agent_id} deleted by user {current_user.username}")
        return {"message": "Agent deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/metrics/query", response_model=MetricsResponse)
async def query_metrics(
    agent_id: Optional[str] = None,
    metric_type: str = "system",
    time_range: str = "1h",
    aggregation: str = "avg",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:read"]))
) -> Any:
    """Query stored metrics"""
    try:
        metrics = await monitoring_service.query_metrics(
            db, agent_id, metric_type, time_range, aggregation, current_user.id
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to query metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query metrics"
        )

@router.post("/alerts/rules", response_model=AlertResponse)
async def create_alert_rule(
    rule: AlertRule,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:write"]))
) -> Any:
    """Create new alert rule"""
    try:
        alert_rule = await monitoring_service.create_alert_rule(rule, current_user.id)
        logger.info(f"Alert rule {alert_rule.id} created by user {current_user.username}")
        return alert_rule
    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/alerts/rules", response_model=List[AlertResponse])
async def get_alert_rules(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:read"]))
) -> Any:
    """Get alert rules"""
    try:
        rules = await monitoring_service.get_alert_rules(db, skip, limit, current_user.id)
        return rules
    except Exception as e:
        logger.error(f"Failed to get alert rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert rules"
        )

@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_active_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:read"]))
) -> Any:
    """Get active alerts"""
    try:
        alerts = await monitoring_service.get_active_alerts(
            db, severity, acknowledged, current_user.id
        )
        return alerts
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:write"]))
) -> Any:
    """Acknowledge an alert"""
    try:
        success = await monitoring_service.acknowledge_alert(
            db, alert_id, current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        logger.info(f"Alert {alert_id} acknowledged by user {current_user.username}")
        return {"message": "Alert acknowledged successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.websocket("/realtime")
async def websocket_monitoring(
    websocket: WebSocket,
    token: str = None
):
    """Real-time monitoring via WebSocket"""
    await websocket.accept()
    
    try:
        # Authenticate WebSocket connection
        if token:
            from app.core.security import verify_token
            payload = verify_token(token)
            username = payload.get("sub")
            logger.info(f"WebSocket monitoring connection established for user: {username}")
        else:
            await websocket.close(code=4001, reason="Authentication required")
            return
        
        # Subscribe to real-time metrics
        await monitoring_service.subscribe_to_metrics(websocket, username)
        
        # Keep connection alive
        while True:
            try:
                # Send real-time data
                data = await monitoring_service.get_realtime_metrics(username)
                await websocket.send_json(data)
                await asyncio.sleep(5)  # Send updates every 5 seconds
            except Exception as e:
                logger.error(f"Error sending WebSocket metrics: {e}")
                await websocket.send_json({"error": str(e)})
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket monitoring client disconnected")
        await monitoring_service.unsubscribe_from_metrics(username)
    except Exception as e:
        logger.error(f"WebSocket monitoring error: {e}")
        await websocket.close(code=4000, reason="Internal server error")

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["monitoring:read"]))
) -> Any:
    """Get dashboard summary data"""
    try:
        summary = await monitoring_service.get_dashboard_summary(db, current_user.id)
        return summary
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard summary"
        )
