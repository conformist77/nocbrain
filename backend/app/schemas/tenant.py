"""
NOCbRAIN Tenant Schemas
Pydantic models for multi-tenant API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class TenantAnalysisRequest(BaseModel):
    """Request for tenant log analysis"""
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


class TenantAnalysisResponse(BaseModel):
    """Response for tenant log analysis"""
    log_id: str
    tenant_id: str
    status: str
    event_type: str
    priority: str
    processing_time: float
    ai_response: Dict[str, Any]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "log_id": "log_123",
                "tenant_id": "tenant-uuid",
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


class TenantDashboardResponse(BaseModel):
    """Response for tenant dashboard"""
    tenant_id: str
    time_window: int
    total_logs_analyzed: int
    threats_detected: int
    knowledge_base_coverage: float
    knowledge_documents: int
    reasoning_engine_stats: Dict[str, Any]
    security_stats: Dict[str, Any]
    knowledge_stats: Dict[str, Any]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "time_window": 3600,
                "total_logs_analyzed": 1250,
                "threats_detected": 15,
                "knowledge_base_coverage": 75.5,
                "knowledge_documents": 150,
                "reasoning_engine_stats": {
                    "total_processed": 1250,
                    "successful": 1200,
                    "failed": 50,
                    "average_processing_time": 0.85
                },
                "security_stats": {
                    "total_events": 800,
                    "threats_detected": 15,
                    "false_positives": 2,
                    "active_patterns": 12
                },
                "knowledge_stats": {
                    "total_documents": 150,
                    "knowledge_types": ["system", "network", "security"],
                    "collection_name": "nocbrain_tenant_tenant-uuid"
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class TenantStatsResponse(BaseModel):
    """Response for tenant statistics"""
    tenant_id: str
    time_window: int
    reasoning_engine: Dict[str, Any]
    security_analyzer: Dict[str, Any]
    knowledge_manager: Dict[str, Any]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "time_window": 3600,
                "reasoning_engine": {
                    "total_processed": 1250,
                    "successful": 1200,
                    "failed": 50,
                    "average_processing_time": 0.85,
                    "queue_sizes": {
                        "main_queue": 3,
                        "security_queue": 1
                    }
                },
                "security_analyzer": {
                    "total_events": 800,
                    "threats_detected": 15,
                    "false_positives": 2,
                    "patterns_matched": {
                        "SSH Brute Force": 8,
                        "Port Scanning": 5
                    }
                },
                "knowledge_manager": {
                    "total_documents": 150,
                    "knowledge_types": ["system", "network", "security"],
                    "collection_name": "nocbrain_tenant_tenant-uuid"
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class TenantKnowledgeQueryRequest(BaseModel):
    """Request for tenant knowledge query"""
    query: str = Field(..., min_length=1, max_length=1000)
    knowledge_type: Optional[str] = Field(None, description="Filter by knowledge type")
    top_k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_global: bool = Field(default=True, description="Include global knowledge")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "How to troubleshoot high CPU usage on Linux servers",
                "knowledge_type": "system",
                "top_k": 5,
                "similarity_threshold": 0.7,
                "include_global": True
            }
        }


class TenantKnowledgeQueryResponse(BaseModel):
    """Response for tenant knowledge query"""
    tenant_id: str
    query: str
    results: List[Dict[str, Any]]
    total_results: int
    knowledge_type: Optional[str]
    include_global: bool
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "query": "How to troubleshoot high CPU usage",
                "results": [
                    {
                        "content": "Check top command...",
                        "metadata": {
                            "source": "knowledge-base/linux-troubleshooting.md",
                            "knowledge_type": "system",
                            "tenant_id": "global",
                            "is_global": True
                        },
                        "similarity_score": 0.85,
                        "source": "global"
                    }
                ],
                "total_results": 5,
                "knowledge_type": "system",
                "include_global": True,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class TenantKnowledgeAddRequest(BaseModel):
    """Request to add tenant knowledge"""
    content: str = Field(..., min_length=10, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    knowledge_type: Optional[str] = Field(None, description="Knowledge type classification")
    is_global: bool = Field(default=False, description="Make knowledge global (superuser only)")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "To troubleshoot high CPU usage on Linux servers:\n1. Use 'top' command\n2. Check for runaway processes",
                "metadata": {
                    "source": "team-knowledge",
                    "author": "senior-admin",
                    "category": "troubleshooting"
                },
                "knowledge_type": "system",
                "is_global": False
            }
        }


class TenantSecurityAnalysisRequest(BaseModel):
    """Request for tenant security analysis"""
    log_data: Dict[str, Any] = Field(..., description="Security log data to analyze")
    
    class Config:
        schema_extra = {
            "example": {
                "log_data": {
                    "id": "sec_log_123",
                    "timestamp": "2024-02-14T10:30:00Z",
                    "source_ip": "192.168.1.100",
                    "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                    "severity": "warning",
                    "event_type": "authentication"
                }
            }
        }


class TenantSecurityAnalysisResponse(BaseModel):
    """Response for tenant security analysis"""
    tenant_id: str
    log_id: str
    threats_detected: int
    threats: List[Dict[str, Any]]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "log_id": "sec_log_123",
                "threats_detected": 1,
                "threats": [
                    {
                        "alert_id": "threat_1707924600_ssh_brute_force",
                        "threat_type": "brute_force",
                        "severity": 2,
                        "pattern_name": "SSH Brute Force",
                        "confidence": 0.8
                    }
                ],
                "timestamp": "2024-02-14T10:30:01Z"
            }
        }


class TenantSecuritySummaryResponse(BaseModel):
    """Response for tenant security summary"""
    tenant_id: str
    time_window: int
    total_events: int
    threat_counts: Dict[str, int]
    severity_counts: Dict[str, int]
    ip_reputation: Dict[str, Dict[str, Any]]
    user_behavior: Dict[str, Dict[str, Any]]
    detection_stats: Dict[str, Any]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "time_window": 3600,
                "total_events": 150,
                "threat_counts": {
                    "brute_force": 8,
                    "lateral_movement": 3,
                    "malware": 1
                },
                "severity_counts": {
                    "critical": 2,
                    "high": 6,
                    "medium": 4
                },
                "ip_reputation": {
                    "192.168.1.100": {
                        "first_seen": "2024-02-14T09:00:00Z",
                        "last_seen": "2024-02-14T10:30:00Z",
                        "event_count": 15,
                        "threat_count": 8,
                        "malicious": True
                    }
                },
                "user_behavior": {
                    "root": {
                        "first_seen": "2024-02-14T08:00:00Z",
                        "last_seen": "2024-02-14T10:30:00Z",
                        "login_count": 25,
                        "unique_ips": 3,
                        "threat_count": 5,
                        "anomalous": True
                    }
                },
                "detection_stats": {
                    "total_events": 1500,
                    "threats_detected": 25,
                    "false_positives": 3
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class TenantHealthResponse(BaseModel):
    """Response for tenant health check"""
    status: str
    tenant_id: str
    reasoning_engine: Optional[Dict[str, Any]] = None
    knowledge_manager: Optional[Dict[str, Any]] = None
    security_analyzer: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    error: Optional[str] = None
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "tenant_id": "tenant-uuid",
                "reasoning_engine": {
                    "is_running": True,
                    "total_processed": 1250
                },
                "knowledge_manager": {
                    "total_documents": 150,
                    "collection_name": "nocbrain_tenant_tenant-uuid"
                },
                "security_analyzer": {
                    "total_events": 800,
                    "threats_detected": 15
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class TenantKnowledgeStatsResponse(BaseModel):
    """Response for tenant knowledge statistics"""
    tenant_id: str
    total_documents: int
    knowledge_types: List[str]
    collection_name: str
    is_global: bool
    last_updated: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "total_documents": 150,
                "knowledge_types": ["system", "network", "security"],
                "collection_name": "nocbrain_tenant_tenant-uuid",
                "is_global": False,
                "last_updated": "2024-02-14T10:30:00Z"
            }
        }


class TenantBatchAnalysisRequest(BaseModel):
    """Request for batch tenant log analysis"""
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


class TenantBatchAnalysisResponse(BaseModel):
    """Response for batch tenant log analysis"""
    tenant_id: str
    results: List[TenantAnalysisResponse]
    total_processed: int
    successful: int
    failed: int
    processing_time: float
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "tenant-uuid",
                "results": [
                    {
                        "log_id": "log_1",
                        "tenant_id": "tenant-uuid",
                        "status": "success",
                        "event_type": "system",
                        "priority": "high",
                        "processing_time": 0.85
                    }
                ],
                "total_processed": 2,
                "successful": 2,
                "failed": 0,
                "processing_time": 1.23,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }
