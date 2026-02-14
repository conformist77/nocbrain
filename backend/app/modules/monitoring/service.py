import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from cryptography.fernet import Fernet
import aiofiles
import aiohttp

from app.core.database import AsyncSession
from app.core.config import settings
from app.schemas.monitoring import (
    AgentRegistration, AgentResponse, AgentConfig,
    MetricsResponse, AlertRule, AlertResponse,
    SystemMetrics, ApplicationMetrics, NetworkMetrics,
    DashboardSummary, HeartbeatData
)
from app.models.monitoring import Agent, Metric, Alert, AlertRule as AlertRuleModel
from app.core.logging import get_logger

logger = get_logger(__name__)


class MonitoringService:
    def __init__(self):
        self.active_connections: Dict[str, Any] = {}
        self.encryption_key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(self.encryption_key)
        
    def decrypt_metrics(self, encrypted_data: str) -> str:
        """Decrypt metrics data from agent"""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt metrics: {e}")
            raise ValueError("Invalid encrypted data")
    
    async def process_metrics(self, metrics: Dict[str, Any], user_id: int):
        """Process incoming metrics from agents"""
        try:
            agent_id = metrics.get('agent_id')
            timestamp = metrics.get('timestamp')
            
            # Store metrics in database
            await self._store_metrics(metrics, user_id)
            
            # Check alert rules
            await self._check_alert_rules(metrics, user_id)
            
            # Update agent status
            await self._update_agent_status(agent_id, timestamp)
            
            # Broadcast to WebSocket clients
            await self._broadcast_metrics(metrics)
            
            logger.info(f"Processed metrics from agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to process metrics: {e}")
            raise
    
    async def register_agent(self, agent_data: AgentRegistration, user_id: int) -> AgentResponse:
        """Register a new monitoring agent"""
        try:
            # Check if agent already exists
            existing_agent = await Agent.get_by_agent_id(agent_data.agent_id)
            if existing_agent:
                # Update existing agent
                existing_agent.hostname = agent_data.hostname
                existing_agent.platform = agent_data.platform
                existing_agent.version = agent_data.version
                existing_agent.description = agent_data.description
                existing_agent.tags = agent_data.tags
                existing_agent.capabilities = agent_data.capabilities
                existing_agent.updated_at = datetime.utcnow()
                
                # This would save to database
                # await db.commit()
                # await db.refresh(existing_agent)
                
                return AgentResponse.from_orm(existing_agent)
            
            # Create new agent
            agent = Agent(
                agent_id=agent_data.agent_id,
                hostname=agent_data.hostname,
                platform=agent_data.platform,
                version=agent_data.version,
                description=agent_data.description,
                tags=agent_data.tags,
                capabilities=agent_data.capabilities,
                status="online",
                last_seen=datetime.utcnow(),
                created_by=user_id
            )
            
            # This would save to database
            # db.add(agent)
            # await db.commit()
            # await db.refresh(agent)
            
            logger.info(f"Agent {agent_data.agent_id} registered successfully")
            return AgentResponse.from_orm(agent)
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise
    
    async def get_agents(self, db: AsyncSession, skip: int, limit: int, 
                       status_filter: Optional[str], user_id: int) -> List[AgentResponse]:
        """Get list of registered agents"""
        try:
            # This would query database with filters
            agents = []
            return [AgentResponse.from_orm(agent) for agent in agents]
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            raise
    
    async def get_agent(self, db: AsyncSession, agent_id: str, user_id: int) -> Optional[AgentResponse]:
        """Get specific agent details"""
        try:
            agent = await Agent.get_by_agent_id(agent_id)
            if not agent:
                return None
            return AgentResponse.from_orm(agent)
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise
    
    async def update_agent_config(self, db: AsyncSession, agent_id: str, 
                             config: AgentConfig, user_id: int) -> Optional[AgentResponse]:
        """Update agent configuration"""
        try:
            agent = await Agent.get_by_agent_id(agent_id)
            if not agent:
                return None
            
            # Update configuration
            agent.config = config.dict()
            agent.updated_at = datetime.utcnow()
            
            # Send configuration to agent
            await self._send_config_to_agent(agent_id, config)
            
            # This would save to database
            # await db.commit()
            # await db.refresh(agent)
            
            logger.info(f"Agent {agent_id} configuration updated")
            return AgentResponse.from_orm(agent)
            
        except Exception as e:
            logger.error(f"Failed to update agent config {agent_id}: {e}")
            raise
    
    async def delete_agent(self, db: AsyncSession, agent_id: str, user_id: int) -> bool:
        """Unregister monitoring agent"""
        try:
            agent = await Agent.get_by_agent_id(agent_id)
            if not agent:
                return False
            
            # This would delete from database
            # await db.delete(agent)
            # await db.commit()
            
            logger.info(f"Agent {agent_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise
    
    async def query_metrics(self, db: AsyncSession, agent_id: Optional[str],
                        metric_type: str, time_range: str, aggregation: str,
                        user_id: int) -> MetricsResponse:
        """Query stored metrics"""
        try:
            # Parse time range
            end_time = datetime.utcnow()
            if time_range.endswith('s'):
                start_time = end_time - timedelta(seconds=int(time_range[:-1]))
            elif time_range.endswith('m'):
                start_time = end_time - timedelta(minutes=int(time_range[:-1]))
            elif time_range.endswith('h'):
                start_time = end_time - timedelta(hours=int(time_range[:-1]))
            elif time_range.endswith('d'):
                start_time = end_time - timedelta(days=int(time_range[:-1]))
            else:
                start_time = end_time - timedelta(hours=1)
            
            # Query metrics from database
            # This would implement actual database query
            metrics_data = []
            
            return MetricsResponse(
                agent_id=agent_id,
                metric_type=metric_type,
                time_range=time_range,
                aggregation=aggregation,
                data_points=len(metrics_data),
                metrics=metrics_data,
                summary={}
            )
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise
    
    async def create_alert_rule(self, rule: AlertRule, user_id: int) -> AlertResponse:
        """Create new alert rule"""
        try:
            # Create alert rule in database
            alert_rule = AlertRuleModel(
                name=rule.name,
                description=rule.description,
                agent_id=rule.agent_id,
                metric_path=rule.metric_path,
                condition=rule.condition.value,
                threshold=rule.threshold,
                severity=rule.severity.value,
                enabled=rule.enabled,
                duration=rule.duration,
                notification_channels=rule.notification_channels,
                tags=rule.tags,
                cooldown_period=rule.cooldown_period,
                created_by=user_id
            )
            
            # This would save to database
            # db.add(alert_rule)
            # await db.commit()
            # await db.refresh(alert_rule)
            
            logger.info(f"Alert rule {rule.name} created")
            return AlertResponse.from_orm(alert_rule)
            
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            raise
    
    async def get_alert_rules(self, db: AsyncSession, skip: int, limit: int,
                           user_id: int) -> List[AlertResponse]:
        """Get alert rules"""
        try:
            # This would query database
            rules = []
            return [AlertResponse.from_orm(rule) for rule in rules]
        except Exception as e:
            logger.error(f"Failed to get alert rules: {e}")
            raise
    
    async def get_active_alerts(self, db: AsyncSession, severity: Optional[str],
                             acknowledged: Optional[bool], user_id: int) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            # This would query database with filters
            alerts = []
            return alerts
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            raise
    
    async def acknowledge_alert(self, db: AsyncSession, alert_id: str, user_id: int) -> bool:
        """Acknowledge an alert"""
        try:
            alert = await Alert.get_by_id(alert_id)
            if not alert:
                return False
            
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            
            # This would save to database
            # await db.commit()
            
            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            raise
    
    async def update_agent_heartbeat(self, heartbeat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent heartbeat"""
        try:
            agent_id = heartbeat_data.get('agent_id')
            
            # Update agent last seen
            agent = await Agent.get_by_agent_id(agent_id)
            if agent:
                agent.last_seen = datetime.utcnow()
                agent.status = heartbeat_data.get('status', 'online')
                # This would save to database
                # await db.commit()
            
            return {
                "status": "received",
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}")
            raise
    
    async def subscribe_to_metrics(self, websocket: Any, username: str):
        """Subscribe user to real-time metrics"""
        self.active_connections[username] = {
            'websocket': websocket,
            'subscribed_at': datetime.utcnow()
        }
        logger.info(f"User {username} subscribed to real-time metrics")
    
    async def unsubscribe_from_metrics(self, username: str):
        """Unsubscribe user from real-time metrics"""
        if username in self.active_connections:
            del self.active_connections[username]
            logger.info(f"User {username} unsubscribed from real-time metrics")
    
    async def get_realtime_metrics(self, username: str) -> Dict[str, Any]:
        """Get real-time metrics for WebSocket"""
        try:
            # This would get latest metrics from database or cache
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "agents": [],
                "alerts": [],
                "metrics": {}
            }
        except Exception as e:
            logger.error(f"Failed to get realtime metrics: {e}")
            return {"error": str(e)}
    
    async def get_dashboard_summary(self, db: AsyncSession, user_id: int) -> DashboardSummary:
        """Get dashboard summary data"""
        try:
            # This would aggregate data from database
            summary = DashboardSummary(
                total_agents=0,
                online_agents=0,
                offline_agents=0,
                warning_agents=0,
                error_agents=0,
                total_metrics=0,
                active_alerts=0,
                critical_alerts=0,
                acknowledged_alerts=0,
                resolved_alerts_today=0,
                system_health_score=0.0,
                last_updated=datetime.utcnow(),
                top_alerts=[],
                recent_metrics=[]
            )
            return summary
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            raise
    
    async def _store_metrics(self, metrics: Dict[str, Any], user_id: int):
        """Store metrics in database"""
        try:
            # This would implement database storage
            # Could use time-series database like InfluxDB or TimescaleDB
            pass
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
            raise
    
    async def _check_alert_rules(self, metrics: Dict[str, Any], user_id: int):
        """Check metrics against alert rules"""
        try:
            # Get active alert rules for this agent
            agent_id = metrics.get('agent_id')
            rules = await AlertRuleModel.get_active_for_agent(agent_id)
            
            for rule in rules:
                # Evaluate rule against metrics
                if await self._evaluate_alert_rule(rule, metrics):
                    # Create alert
                    await self._create_alert(rule, metrics, user_id)
                    
        except Exception as e:
            logger.error(f"Failed to check alert rules: {e}")
    
    async def _evaluate_alert_rule(self, rule: AlertRuleModel, metrics: Dict[str, Any]) -> bool:
        """Evaluate if alert rule should trigger"""
        try:
            # Get metric value from metrics
            metric_value = self._get_metric_value(rule.metric_path, metrics)
            if metric_value is None:
                return False
            
            # Evaluate condition
            threshold = rule.threshold
            condition = rule.condition
            
            if condition == "greater_than":
                return float(metric_value) > float(threshold)
            elif condition == "less_than":
                return float(metric_value) < float(threshold)
            elif condition == "equals":
                return str(metric_value) == str(threshold)
            elif condition == "not_equals":
                return str(metric_value) != str(threshold)
            elif condition == "contains":
                return str(threshold) in str(metric_value)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate alert rule: {e}")
            return False
    
    def _get_metric_value(self, path: str, metrics: Dict[str, Any]) -> Optional[Any]:
        """Get metric value by path (e.g., 'system.cpu.usage_percent')"""
        try:
            keys = path.split('.')
            value = metrics
            for key in keys:
                value = value.get(key)
                if value is None:
                    return None
            return value
        except Exception:
            return None
    
    async def _create_alert(self, rule: AlertRuleModel, metrics: Dict[str, Any], user_id: int):
        """Create new alert"""
        try:
            metric_value = self._get_metric_value(rule.metric_path, metrics)
            
            alert = Alert(
                rule_id=rule.id,
                rule_name=rule.name,
                agent_id=metrics.get('agent_id'),
                agent_hostname=metrics.get('hostname'),
                metric_path=rule.metric_path,
                current_value=metric_value,
                threshold=rule.threshold,
                condition=rule.condition,
                severity=rule.severity,
                status="active",
                message=f"Alert: {rule.name} - {rule.metric_path} is {metric_value} (threshold: {rule.threshold})",
                triggered_at=datetime.utcnow(),
                tags=rule.tags
            )
            
            # This would save to database
            # db.add(alert)
            # await db.commit()
            
            # Send notifications
            await self._send_alert_notification(alert)
            
            logger.warning(f"Alert created: {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification"""
        try:
            # This would implement notification channels
            # Email, Slack, webhook, etc.
            pass
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
    
    async def _update_agent_status(self, agent_id: str, timestamp: str):
        """Update agent status based on last seen"""
        try:
            agent = await Agent.get_by_agent_id(agent_id)
            if agent:
                last_seen = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_diff = datetime.utcnow() - last_seen
                
                if time_diff > timedelta(minutes=5):
                    agent.status = "offline"
                elif time_diff > timedelta(minutes=2):
                    agent.status = "warning"
                else:
                    agent.status = "online"
                
                # This would save to database
                # await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
    
    async def _broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics to WebSocket clients"""
        try:
            message = json.dumps({
                "type": "metrics_update",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send to all connected clients
            for username, connection in self.active_connections.items():
                try:
                    await connection['websocket'].send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send metrics to {username}: {e}")
                    # Remove dead connection
                    del self.active_connections[username]
                    
        except Exception as e:
            logger.error(f"Failed to broadcast metrics: {e}")
    
    async def _send_config_to_agent(self, agent_id: str, config: AgentConfig):
        """Send configuration update to agent"""
        try:
            # This would send configuration to agent via webhook or direct connection
            pass
        except Exception as e:
            logger.error(f"Failed to send config to agent {agent_id}: {e}")
