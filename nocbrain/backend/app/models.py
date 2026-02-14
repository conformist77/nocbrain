from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class IncidentStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    AVERAGE = "average"
    HIGH = "high"
    DISASTER = "disaster"


# Request Models
class LoginRequest(BaseModel):
    username: str
    password: str


class IncidentAnalyzeRequest(BaseModel):
    pass


class IncidentCloseRequest(BaseModel):
    pass


# Response Models
class Token(BaseModel):
    access_token: str
    token_type: str


class AlertResponse(BaseModel):
    id: UUID
    host: str
    severity: str
    message: str
    timestamp: datetime
    raw_payload: Optional[Dict[str, Any]] = None
    incident_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: UUID
    host: str
    created_at: datetime
    status: IncidentStatus
    root_cause_summary: Optional[str] = None
    llm_explanation: Optional[str] = None
    updated_at: Optional[datetime] = None
    alerts: List[AlertResponse] = []
    
    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int


# Internal Models
class ZabbixProblem(BaseModel):
    eventid: str
    objectid: str
    name: str
    severity: str
    host: str
    clock: str
    value: str
    acknowledged: str
    status: str


class LLMResponse(BaseModel):
    root_cause: str
    confidence: float
    reasoning: str
