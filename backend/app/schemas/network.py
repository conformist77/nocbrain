from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    SERVER = "server"
    ACCESS_POINT = "access_point"
    LOAD_BALANCER = "load_balancer"
    OTHER = "other"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class SNMPVersion(str, Enum):
    V1 = "1"
    V2C = "2c"
    V3 = "3"


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    ip_address: str = Field(..., regex=r'^(\d{1,3}\.){3}\d{1,3}$')
    device_type: DeviceType
    description: Optional[str] = None
    location: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None


class DeviceCreate(DeviceBase):
    snmp_community: Optional[str] = None
    snmp_port: int = Field(default=161, ge=1, le=65535)
    snmp_version: SNMPVersion = SNMPVersion.V2C
    snmp_username: Optional[str] = None
    snmp_password: Optional[str] = None
    snmp_security_level: Optional[str] = None
    monitoring_enabled: bool = True


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = Field(None, regex=r'^(\d{1,3}\.){3}\d{1,3}$')
    device_type: Optional[DeviceType] = None
    description: Optional[str] = None
    location: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    snmp_community: Optional[str] = None
    snmp_port: Optional[int] = Field(None, ge=1, le=65535)
    snmp_version: Optional[SNMPVersion] = None
    snmp_username: Optional[str] = None
    snmp_password: Optional[str] = None
    snmp_security_level: Optional[str] = None
    monitoring_enabled: Optional[bool] = None


class DeviceResponse(DeviceBase):
    id: int
    status: DeviceStatus
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    monitoring_enabled: bool
    snmp_configured: bool
    
    class Config:
        from_attributes = True


class SNMPConfig(BaseModel):
    community: Optional[str] = None
    port: int = Field(default=161, ge=1, le=65535)
    version: SNMPVersion = SNMPVersion.V2C
    username: Optional[str] = None
    password: Optional[str] = None
    security_level: Optional[str] = None
    auth_protocol: Optional[str] = None
    priv_protocol: Optional[str] = None


class NetworkScanRequest(BaseModel):
    ip_range: str = Field(..., description="CIDR notation, e.g., 192.168.1.0/24")
    scan_type: str = Field(default="ping", description="ping, snmp, or comprehensive")
    timeout: int = Field(default=5, ge=1, le=60)
    max_concurrent: int = Field(default=50, ge=1, le=1000)


class DiscoveredDevice(BaseModel):
    ip_address: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    open_ports: List[int] = []
    snmp_available: bool = False
    response_time: Optional[float] = None


class NetworkScanResult(BaseModel):
    scan_id: str
    ip_range: str
    total_ips: int
    reachable_ips: int
    discovered_devices: List[DiscoveredDevice]
    scan_duration: float
    timestamp: datetime


class NetworkNode(BaseModel):
    id: str
    name: str
    ip_address: str
    device_type: DeviceType
    status: DeviceStatus
    vendor: Optional[str] = None
    model: Optional[str] = None
    position: Optional[Dict[str, float]] = None  # x, y coordinates for visualization


class NetworkEdge(BaseModel):
    source: str
    target: str
    connection_type: str
    bandwidth: Optional[str] = None
    latency: Optional[float] = None
    utilization: Optional[float] = None


class NetworkTopologyResponse(BaseModel):
    nodes: List[NetworkNode]
    edges: List[NetworkEdge]
    last_updated: datetime


class MetricData(BaseModel):
    timestamp: datetime
    value: float
    unit: str


class DeviceMetrics(BaseModel):
    device_id: int
    device_name: str
    cpu_utilization: Optional[List[MetricData]] = []
    memory_utilization: Optional[List[MetricData]] = []
    bandwidth_in: Optional[List[MetricData]] = []
    bandwidth_out: Optional[List[MetricData]] = []
    interface_status: Optional[Dict[str, Any]] = {}
    error_rates: Optional[List[MetricData]] = []


class NetworkMetricsResponse(BaseModel):
    time_range: str
    total_devices: int
    online_devices: int
    offline_devices: int
    devices_with_warnings: int
    critical_devices: int
    overall_health: str
    metrics: List[DeviceMetrics]
    summary: Dict[str, Any] = {}


class NetworkAlert(BaseModel):
    id: str
    device_id: int
    device_name: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
