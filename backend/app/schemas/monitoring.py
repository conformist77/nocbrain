from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MetricType(str, Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    NETWORK = "network"
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCondition(str, Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    REGEX = "regex"


class AgentRegistration(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., min_length=1, max_length=50)
    version: str = Field(default="1.0.0")
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(default_factory=list)
    capabilities: Optional[List[str]] = Field(default_factory=list)


class AgentConfig(BaseModel):
    collection_interval: int = Field(default=60, ge=10, le=3600, description="Collection interval in seconds")
    metrics_enabled: List[str] = Field(default_factory=list, description="List of enabled metrics")
    alert_rules_enabled: bool = Field(default=True)
    encryption_enabled: bool = Field(default=True)
    compression_enabled: bool = Field(default=True)
    custom_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)
    network_timeout: int = Field(default=30, ge=5, le=300)
    retry_attempts: int = Field(default=3, ge=1, le=10)


class AgentResponse(BaseModel):
    id: str
    agent_id: str
    hostname: str
    platform: str
    version: str
    status: AgentStatus
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    tags: List[str] = []
    capabilities: List[str] = []
    config: Optional[AgentConfig] = None
    metrics_count: int = 0
    alerts_count: int = 0
    
    class Config:
        from_attributes = True


class MetricsRequest(BaseModel):
    agent_id: Optional[str] = None
    metric_type: MetricType = MetricType.SYSTEM
    time_range: str = Field(default="1h", regex=r'^\d+[smhdw]$')
    aggregation: str = Field(default="avg", regex=r'^(avg|sum|min|max|count)$')
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MetricData(BaseModel):
    timestamp: datetime
    value: Union[float, int, str]
    unit: Optional[str] = None
    tags: Optional[Dict[str, str]] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    agent_id: Optional[str]
    metric_type: MetricType
    time_range: str
    aggregation: str
    data_points: int
    metrics: List[MetricData]
    summary: Dict[str, Any] = {}


class AlertRule(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    agent_id: Optional[str] = None
    metric_path: str = Field(..., description="Path to the metric, e.g., 'system.cpu.usage_percent'")
    condition: AlertCondition
    threshold: Union[float, int, str]
    severity: AlertSeverity
    enabled: bool = Field(default=True)
    duration: int = Field(default=300, ge=0, description="Duration in seconds")
    notification_channels: List[str] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    cooldown_period: int = Field(default=900, ge=0, description="Cooldown period in seconds")


class AlertResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    agent_id: Optional[str]
    agent_hostname: Optional[str]
    metric_path: str
    current_value: Union[float, int, str]
    threshold: Union[float, int, str]
    condition: AlertCondition
    severity: AlertSeverity
    status: str  # active, acknowledged, resolved
    message: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    duration: Optional[int] = None  # Duration in seconds
    notification_sent: bool = False
    tags: List[str] = []
    
    class Config:
        from_attributes = True


class SystemMetrics(BaseModel):
    timestamp: datetime
    agent_id: str
    hostname: str
    platform: str
    uptime: float
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]
    processes: Dict[str, Any]
    load_average: List[float] = []


class ApplicationMetrics(BaseModel):
    timestamp: datetime
    agent_id: str
    hostname: str
    applications: Dict[str, Dict[str, Any]]


class NetworkMetrics(BaseModel):
    timestamp: datetime
    agent_id: str
    hostname: str
    interfaces: Dict[str, Dict[str, Any]]
    connections: Dict[str, Any]
    bandwidth: Dict[str, Any]
    latency: Dict[str, Any]


class CustomMetrics(BaseModel):
    timestamp: datetime
    agent_id: str
    hostname: str
    metrics: Dict[str, Any]


class HeartbeatData(BaseModel):
    agent_id: str
    hostname: str
    platform: str
    timestamp: datetime
    status: str
    version: str
    uptime: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


class DashboardSummary(BaseModel):
    total_agents: int
    online_agents: int
    offline_agents: int
    warning_agents: int
    error_agents: int
    total_metrics: int
    active_alerts: int
    critical_alerts: int
    acknowledged_alerts: int
    resolved_alerts_today: int
    system_health_score: float  # 0-100
    last_updated: datetime
    top_alerts: List[AlertResponse] = []
    recent_metrics: List[Dict[str, Any]] = []


class NotificationChannel(BaseModel):
    id: str
    name: str
    type: str  # email, slack, webhook, sms
    config: Dict[str, Any]
    enabled: bool = True
    rate_limit: Optional[int] = None  # Max notifications per hour
    last_notification: Optional[datetime] = None


class MetricsExport(BaseModel):
    format: str = Field(default="json", regex=r'^(json|csv|xml|prometheus)$')
    time_range: str = Field(default="24h", regex=r'^\d+[smhdw]$')
    agents: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentDeployment(BaseModel):
    agent_id: str
    target_hosts: List[str]  # IP addresses or hostnames
    deployment_config: AgentConfig
    installation_script: Optional[str] = None
    deployment_method: str = Field(default="ssh", regex=r'^(ssh|winrm|manual)$')
    credentials: Optional[Dict[str, str]] = None
    rollback_enabled: bool = Field(default=True)


class DeploymentStatus(BaseModel):
    deployment_id: str
    agent_id: str
    status: str  # pending, running, completed, failed, rolled_back
    target_hosts: List[str]
    successful_deployments: List[str]
    failed_deployments: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    logs: List[str] = []
    error_message: Optional[str] = None
