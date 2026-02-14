"""
NOCbRAIN Core Engine Schemas
Pydantic models for core engine API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class PriorityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventType(str, Enum):
    SYSTEM = "system"
    NETWORK = "network"
    SECURITY = "security"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"


class LogAnalysisRequest(BaseModel):
    """Request for log analysis"""
    log_data: Dict[str, Any] = Field(..., description="Log data to analyze")
    
    class Config:
        schema_extra = {
            "example": {
                "log_data": {
                    "id": "log_123",
                    "timestamp": "2024-02-14T10:30:00Z",
                    "source": "zabbix",
                    "content": "CPU usage on server web-01 is 95%",
                    "severity": "high",
                    "host": "web-01"
                }
            }
        }


class LogAnalysisResponse(BaseModel):
    """Response for log analysis"""
    log_id: str
    status: str
    event_type: EventType
    priority: PriorityLevel
    processing_time: float
    ai_response: Dict[str, Any]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "log_id": "log_123",
                "status": "success",
                "event_type": "system",
                "priority": "high",
                "processing_time": 1.23,
                "ai_response": {
                    "status": "success",
                    "response": "NOC Action Plan: 1. Check CPU processes...",
                    "knowledge_results": []
                },
                "timestamp": "2024-02-14T10:30:01Z"
            }
        }


class KnowledgeQueryRequest(BaseModel):
    """Request for knowledge base query"""
    query: str = Field(..., min_length=1, max_length=1000)
    knowledge_type: Optional[str] = Field(None, description="Filter by knowledge type")
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "query": "How to troubleshoot high CPU usage on Linux servers",
                "knowledge_type": "system",
                "top_k": 5,
                "similarity_threshold": 0.7
            }
        }


class KnowledgeQueryResponse(BaseModel):
    """Response for knowledge base query"""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    knowledge_type: Optional[str]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "query": "How to troubleshoot high CPU usage",
                "results": [
                    {
                        "content": "Check top command...",
                        "metadata": {
                            "source": "knowledge-base/linux-troubleshooting.md",
                            "knowledge_type": "system"
                        },
                        "similarity_score": 0.85
                    }
                ],
                "total_results": 5,
                "knowledge_type": "system",
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class IncidentRequest(BaseModel):
    """Request for NOC action plan generation"""
    incident_data: Dict[str, Any] = Field(..., description="Incident data")
    
    class Config:
        schema_extra = {
            "example": {
                "incident_data": {
                    "id": "incident_456",
                    "title": "Web Server High CPU Usage",
                    "description": "Multiple web servers showing CPU usage above 90%",
                    "affected_systems": ["web-01", "web-02", "web-03"],
                    "severity": "high",
                    "symptoms": ["Slow response times", "Increased error rates"]
                }
            }
        }


class IncidentResponse(BaseModel):
    """Response for NOC action plan"""
    incident_id: str
    status: str
    noc_action_plan: str
    knowledge_used: List[Dict[str, Any]]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "incident_id": "incident_456",
                "status": "success",
                "noc_action_plan": "## NOC Action Plan\n\n### 1. Immediate Assessment\n- CPU usage is critical on web servers\n- User experience is degraded\n\n### 2. Root Cause Analysis\n- Check for runaway processes\n- Review application logs\n- Analyze traffic patterns\n\n### 3. Step-by-Step Resolution\n1. SSH to affected servers\n2. Run 'top' to identify processes\n3. Kill or restart problematic processes\n4. Monitor CPU usage\n5. Verify application functionality\n\n### 4. Verification Steps\n- CPU usage below 80%\n- Application response time normal\n- No user complaints\n\n### 5. Prevention Measures\n- Implement CPU monitoring alerts\n- Set up auto-scaling\n- Optimize application performance",
                "knowledge_used": [
                    {
                        "content": "High CPU troubleshooting steps...",
                        "metadata": {"knowledge_type": "system"},
                        "similarity_score": 0.92
                    }
                ],
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class SystemStatusResponse(BaseModel):
    """Response for system status"""
    status: str
    reasoning_engine: Dict[str, Any]
    knowledge_manager: Dict[str, Any]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "reasoning_engine": {
                    "total_processed": 1250,
                    "successful": 1200,
                    "failed": 50,
                    "security_events": 25,
                    "average_processing_time": 0.85,
                    "queue_sizes": {
                        "main_queue": 3,
                        "security_queue": 1
                    },
                    "is_running": True
                },
                "knowledge_manager": {
                    "total_documents": 5000,
                    "knowledge_types": ["system", "network", "security", "application"],
                    "collection_name": "nocbrain_knowledge",
                    "last_updated": "2024-02-14T10:00:00Z"
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response for health check"""
    status: str
    reason: Optional[str] = None
    reasoning_engine: Optional[Dict[str, Any]] = None
    knowledge_manager: Optional[Dict[str, Any]] = None
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "reasoning_engine": {
                    "is_running": True,
                    "total_processed": 1250
                },
                "knowledge_manager": {
                    "total_documents": 5000
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class KnowledgeIndexRequest(BaseModel):
    """Request for knowledge base indexing"""
    force_reindex: bool = Field(default=False, description="Force complete reindex")
    
    class Config:
        schema_extra = {
            "example": {
                "force_reindex": False
            }
        }


class KnowledgeIndexResponse(BaseModel):
    """Response for knowledge base indexing"""
    status: str
    message: str
    force_reindex: bool
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "started",
                "message": "Knowledge base indexing started in background",
                "force_reindex": False,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class SimilarIncidentsRequest(BaseModel):
    """Request for similar incidents search"""
    incident_description: str = Field(..., min_length=10, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    
    class Config:
        schema_extra = {
            "example": {
                "incident_description": "Web servers showing high CPU usage and slow response times",
                "limit": 5
            }
        }


class SimilarIncidentsResponse(BaseModel):
    """Response for similar incidents search"""
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Web servers high CPU usage",
                "results": [
                    {
                        "content": "Previous incident with similar symptoms...",
                        "metadata": {
                            "knowledge_type": "incident_report",
                            "incident_id": "incident_123",
                            "resolution_time": "2 hours"
                        },
                        "similarity_score": 0.88
                    }
                ],
                "total_results": 3,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class AddKnowledgeRequest(BaseModel):
    """Request to add knowledge"""
    content: str = Field(..., min_length=10, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    knowledge_type: Optional[str] = Field(None, description="Knowledge type classification")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "To troubleshoot high CPU usage on Linux servers:\n1. Use 'top' command to identify processes\n2. Check for runaway processes\n3. Review system logs\n4. Monitor resource usage",
                "metadata": {
                    "source": "team-knowledge",
                    "author": "senior-admin",
                    "category": "troubleshooting"
                },
                "knowledge_type": "system"
            }
        }


class AddKnowledgeResponse(BaseModel):
    """Response for adding knowledge"""
    status: str
    chunks: int
    knowledge_type: str
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "chunks": 3,
                "knowledge_type": "system",
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class BatchAnalysisRequest(BaseModel):
    """Request for batch log analysis"""
    logs: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100)
    
    class Config:
        schema_extra = {
            "example": {
                "logs": [
                    {
                        "id": "log_1",
                        "timestamp": "2024-02-14T10:30:00Z",
                        "source": "zabbix",
                        "content": "CPU usage on web-01 is 95%",
                        "severity": "high"
                    },
                    {
                        "id": "log_2",
                        "timestamp": "2024-02-14T10:31:00Z",
                        "source": "zabbix",
                        "content": "Memory usage on db-01 is 87%",
                        "severity": "medium"
                    }
                ]
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Response for batch log analysis"""
    results: List[LogAnalysisResponse]
    total_processed: int
    successful: int
    failed: int
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "log_id": "log_1",
                        "status": "success",
                        "event_type": "system",
                        "priority": "high",
                        "processing_time": 0.85
                    }
                ],
                "total_processed": 2,
                "successful": 2,
                "failed": 0,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }
