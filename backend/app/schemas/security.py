"""
NOCbRAIN Security Analysis Schemas
Pydantic models for security analysis API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ThreatType(str, Enum):
    BRUTE_FORCE = "brute_force"
    LATERAL_MOVEMENT = "lateral_movement"
    MALWARE = "malware"
    INTRUSION = "intrusion"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    C2_COMMUNICATION = "c2_communication"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class LogAnalysisRequest(BaseModel):
    """Request for security log analysis"""
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


class LogAnalysisResponse(BaseModel):
    """Response for security log analysis"""
    log_id: str
    threats_detected: int
    threats: List[Dict[str, Any]]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "log_id": "sec_log_123",
                "threats_detected": 1,
                "threats": [
                    {
                        "alert_id": "threat_1707924600_ssh_brute_force",
                        "threat_type": "brute_force",
                        "severity": 2,
                        "pattern_name": "SSH Brute Force",
                        "description": "Multiple failed SSH login attempts",
                        "source_event": {
                            "timestamp": "2024-02-14T10:30:00Z",
                            "source_ip": "192.168.1.100",
                            "message": "Failed password for root from 192.168.1.100 port 22 ssh2",
                            "severity": "warning"
                        },
                        "matches": [
                            {
                                "pattern": "SSH Brute Force",
                                "matched_text": "Failed password for root from 192.168.1.100",
                                "groups": ("192.168.1.100",),
                                "timestamp": "2024-02-14T10:30:00Z"
                            }
                        ],
                        "timestamp": "2024-02-14T10:30:01Z",
                        "tags": ["ssh", "authentication", "brute_force"],
                        "confidence": 0.8,
                        "mitigation_advice": [
                            "Block source IP address",
                            "Implement rate limiting",
                            "Enable account lockout policies"
                        ]
                    }
                ],
                "timestamp": "2024-02-14T10:30:01Z"
            }
        }


class ThreatAlertRequest(BaseModel):
    """Request for threat alert"""
    alert_id: str
    threat_type: ThreatType
    severity: SeverityLevel
    description: str
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "alert_id": "threat_1707924600_ssh_brute_force",
                "threat_type": "brute_force",
                "severity": "high",
                "description": "SSH brute force attack detected",
                "source_ip": "192.168.1.100",
                "target_ip": "192.168.1.10",
                "evidence": [
                    {
                        "timestamp": "2024-02-14T10:30:00Z",
                        "message": "Failed password for root from 192.168.1.100",
                        "severity": "warning"
                    }
                ]
            }
        }


class ThreatAlertResponse(BaseModel):
    """Response for threat alert"""
    alert_id: str
    status: str
    threat_type: ThreatType
    severity: SeverityLevel
    description: str
    mitigation_advice: List[str]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "alert_id": "threat_1707924600_ssh_brute_force",
                "status": "active",
                "threat_type": "brute_force",
                "severity": "high",
                "description": "SSH brute force attack detected",
                "mitigation_advice": [
                    "Block source IP address",
                    "Implement rate limiting",
                    "Enable account lockout policies"
                ],
                "timestamp": "2024-02-14T10:30:01Z"
            }
        }


class SecurityStatsResponse(BaseModel):
    """Response for security statistics"""
    total_events: int
    threats_detected: int
    false_positives: int
    total_patterns: int
    event_history_size: int
    ip_reputation_size: int
    user_behavior_size: int
    patterns_matched: Dict[str, int]
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "total_events": 1500,
                "threats_detected": 25,
                "false_positives": 3,
                "total_patterns": 12,
                "event_history_size": 10000,
                "ip_reputation_size": 150,
                "user_behavior_size": 45,
                "patterns_matched": {
                    "SSH Brute Force": 8,
                    "Lateral Movement - Unusual Admin Access": 5,
                    "Port Scanning": 12
                },
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class PatternRequest(BaseModel):
    """Request for security pattern"""
    name: str = Field(..., min_length=1, max_length=100)
    threat_type: ThreatType
    severity: SeverityLevel
    description: str = Field(..., min_length=10, max_length=500)
    patterns: List[str] = Field(..., min_items=1, max_items=10)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    time_window: int = Field(default=300, ge=60, le=3600)
    threshold: int = Field(default=1, ge=1, le=100)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Custom SSH Brute Force",
                "threat_type": "brute_force",
                "severity": "high",
                "description": "Detect SSH brute force attacks with custom patterns",
                "patterns": [
                    r"Failed password for .* from (\d+\.\d+\.\d+\.\d+)",
                    r"authentication failure.*rhost=(\d+\.\d+\.\d+\.\d+)"
                ],
                "conditions": {
                    "source_ip": "extract",
                    "threshold": 5
                },
                "time_window": 300,
                "threshold": 5,
                "tags": ["ssh", "authentication", "custom"]
            }
        }


class PatternResponse(BaseModel):
    """Response for security pattern"""
    status: str
    pattern_name: str
    total_patterns: int
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "pattern_name": "Custom SSH Brute Force",
                "total_patterns": 13,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class ThreatSummaryResponse(BaseModel):
    """Response for threat summary"""
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


class BatchAnalysisRequest(BaseModel):
    """Request for batch security log analysis"""
    logs: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100)
    
    class Config:
        schema_extra = {
            "example": {
                "logs": [
                    {
                        "id": "sec_log_1",
                        "timestamp": "2024-02-14T10:30:00Z",
                        "source_ip": "192.168.1.100",
                        "message": "Failed password for root from 192.168.1.100",
                        "severity": "warning"
                    },
                    {
                        "id": "sec_log_2",
                        "timestamp": "2024-02-14T10:31:00Z",
                        "source_ip": "192.168.1.101",
                        "message": "Port scan detected from 192.168.1.101",
                        "severity": "warning"
                    }
                ]
            }
        }


class BatchAnalysisResponse(BaseModel):
    """Response for batch security log analysis"""
    results: List[LogAnalysisResponse]
    total_processed: int
    total_threats: int
    processing_time: float
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {
                        "log_id": "sec_log_1",
                        "threats_detected": 1,
                        "threats": []
                    }
                ],
                "total_processed": 2,
                "total_threats": 2,
                "processing_time": 1.23,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }


class TestDetectionRequest(BaseModel):
    """Request for threat detection testing"""
    test_type: str = Field(..., description="Type of test to run")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "test_type": "brute_force_detection",
                "parameters": {
                    "source_ip": "192.168.1.100",
                    "attempts": 5
                }
            }
        }


class TestDetectionResponse(BaseModel):
    """Response for threat detection testing"""
    test_type: str
    test_logs: int
    threats_detected: int
    threats: List[Dict[str, Any]]
    success: bool
    timestamp: str
    
    class Config:
        schema_extra = {
            "example": {
                "test_type": "brute_force_detection",
                "test_logs": 5,
                "threats_detected": 1,
                "threats": [],
                "success": True,
                "timestamp": "2024-02-14T10:30:00Z"
            }
        }
