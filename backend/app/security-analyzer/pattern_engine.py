"""
NOCbRAIN Security Pattern Engine
Pattern matching engine for XDR/SIEM log analysis and threat detection
"""

import re
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import ipaddress
from collections import defaultdict, deque

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ThreatType(Enum):
    """Threat types for classification"""
    BRUTE_FORCE = "brute_force"
    LATERAL_MOVEMENT = "lateral_movement"
    MALWARE = "malware"
    INTRUSION = "intrusion"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    C2_COMMUNICATION = "c2_communication"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


class SeverityLevel(Enum):
    """Severity levels for threats"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class SecurityPattern:
    """Security pattern definition"""
    name: str
    threat_type: ThreatType
    severity: SeverityLevel
    description: str
    patterns: List[str]  # Regex patterns
    conditions: Dict[str, Any]  # Additional conditions
    time_window: int = 300  # Time window in seconds
    threshold: int = 1  # Minimum occurrences
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        
        # Compile regex patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.patterns]


@dataclass
class SecurityEvent:
    """Security event data"""
    timestamp: datetime
    source_ip: str
    target_ip: Optional[str]
    event_type: str
    message: str
    severity: str
    user: Optional[str] = None
    process: Optional[str] = None
    raw_log: str = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "target_ip": self.target_ip,
            "event_type": self.event_type,
            "message": self.message,
            "severity": self.severity,
            "user": self.user,
            "process": self.process,
            "raw_log": self.raw_log
        }


class PatternEngine:
    """Main pattern matching engine for security analysis"""
    
    def __init__(self):
        self.patterns: List[SecurityPattern] = []
        self.event_history: deque = deque(maxlen=10000)  # Rolling window
        self.ip_reputation: Dict[str, Dict[str, Any]] = {}
        self.user_behavior: Dict[str, Dict[str, Any]] = {}
        self.detection_stats = {
            "total_events": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "patterns_matched": defaultdict(int)
        }
        
        # Initialize default patterns
        self._load_default_patterns()
        
        logger.info("Security Pattern Engine initialized")
    
    def _load_default_patterns(self):
        """Load default security patterns"""
        default_patterns = [
            # Brute Force Patterns
            SecurityPattern(
                name="SSH Brute Force",
                threat_type=ThreatType.BRUTE_FORCE,
                severity=SeverityLevel.HIGH,
                description="Multiple failed SSH login attempts",
                patterns=[
                    r"Failed password for .* from (\d+\.\d+\.\d+\.\d+)",
                    r"authentication failure.*rhost=(\d+\.\d+\.\d+\.\d+)",
                    r"Invalid user .* from (\d+\.\d+\.\d+\.\d+)"
                ],
                conditions={"source_ip": "extract", "threshold": 5},
                time_window=300,
                threshold=5,
                tags=["ssh", "authentication", "brute_force"]
            ),
            
            SecurityPattern(
                name="RDP Brute Force",
                threat_type=ThreatType.BRUTE_FORCE,
                severity=SeverityLevel.HIGH,
                description="Multiple failed RDP login attempts",
                patterns=[
                    r"Failed logon.*Source Network Address: (\d+\.\d+\.\d+\.\d+)",
                    r"Logon failure.*Source Network Address: (\d+\.\d+\.\d+\.\d+)",
                    r"RDP.*failed.*from (\d+\.\d+\.\d+\.\d+)"
                ],
                conditions={"source_ip": "extract", "threshold": 10},
                time_window=300,
                threshold=10,
                tags=["rdp", "authentication", "brute_force"]
            ),
            
            # Lateral Movement Patterns
            SecurityPattern(
                name="Lateral Movement - Unusual Admin Access",
                threat_type=ThreatType.LATERAL_MOVEMENT,
                severity=SeverityLevel.CRITICAL,
                description="Administrator account accessing multiple systems",
                patterns=[
                    r"User '.*' logged in from (\d+\.\d+\.\d+\.\d+)",
                    r"sudo: .* : TTY=.* ; PWD=.* ; USER=root ; COMMAND=.*",
                    r"Administrator.*logon.*from (\d+\.\d+\.\d+\.\d+)"
                ],
                conditions={"user": "extract", "admin_users": ["root", "administrator", "admin"]},
                time_window=600,
                threshold=3,
                tags=["lateral_movement", "privilege_escalation", "admin"]
            ),
            
            SecurityPattern(
                name="Lateral Movement - Port Scanning",
                threat_type=ThreatType.LATERAL_MOVEMENT,
                severity=SeverityLevel.MEDIUM,
                description="Port scanning activity detected",
                patterns=[
                    r"port scan detected from (\d+\.\d+\.\d+\.\d+)",
                    r"nmap scan from (\d+\.\d+\.\d+\.\d+)",
                    r"multiple connection attempts from (\d+\.\d+\.\d+\.\d+)"
                ],
                conditions={"source_ip": "extract", "port_count": "extract"},
                time_window=60,
                threshold=20,
                tags=["lateral_movement", "reconnaissance", "port_scan"]
            ),
            
            # Malware Patterns
            SecurityPattern(
                name="Malware - Suspicious Process",
                threat_type=ThreatType.MALWARE,
                severity=SeverityLevel.CRITICAL,
                description="Suspicious process execution detected",
                patterns=[
                    r"suspicious process: (.*) launched",
                    r"malware detected: (.*)",
                    r"virus found in (.*)",
                    r"trojan.*process (.*)"
                ],
                conditions={"process": "extract"},
                time_window=1,
                threshold=1,
                tags=["malware", "process", "antivirus"]
            ),
            
            SecurityPattern(
                name="Malware - C2 Communication",
                threat_type=ThreatType.C2_COMMUNICATION,
                severity=SeverityLevel.CRITICAL,
                description="Command and control communication detected",
                patterns=[
                    r"C2 communication to (\d+\.\d+\.\d+\.\d+)",
                    r"botnet connection to (\d+\.\d+\.\d+\.\d+)",
                    r"malware C2 server: (\d+\.\d+\.\d+\.\d+)"
                ],
                conditions={"target_ip": "extract"},
                time_window=300,
                threshold=1,
                tags=["malware", "c2", "communication"]
            ),
            
            # Intrusion Patterns
            SecurityPattern(
                name="Intrusion - SQL Injection",
                threat_type=ThreatType.INTRUSION,
                severity=SeverityLevel.HIGH,
                description="SQL injection attempt detected",
                patterns=[
                    r"SQL injection attempt: (.*)",
                    r"union select.*from.*",
                    r"'.*or.*1=1.*--",
                    r"waitfor delay.*"
                ],
                conditions={"payload": "extract"},
                time_window=1,
                threshold=1,
                tags=["intrusion", "sql_injection", "web_attack"]
            ),
            
            SecurityPattern(
                name="Intrusion - XSS Attempt",
                threat_type=ThreatType.INTRUSION,
                severity=SeverityLevel.MEDIUM,
                description="Cross-site scripting attempt detected",
                patterns=[
                    r"<script.*>.*</script>",
                    r"javascript:",
                    r"onload=.*",
                    r"onerror=.*"
                ],
                conditions={"payload": "extract"},
                time_window=1,
                threshold=1,
                tags=["intrusion", "xss", "web_attack"]
            ),
            
            # Data Exfiltration Patterns
            SecurityPattern(
                name="Data Exfiltration - Large Transfer",
                threat_type=ThreatType.DATA_EXFILTRATION,
                severity=SeverityLevel.HIGH,
                description="Large data transfer detected",
                patterns=[
                    r"large file transfer: (.*) size (\d+)",
                    r"data exfiltration: (.*) (\d+) bytes",
                    r"unusual upload: (.*) size (\d+)"
                ],
                conditions={"file_size": "extract", "threshold": 104857600},  # 100MB
                time_window=300,
                threshold=1,
                tags=["data_exfiltration", "data_transfer"]
            ),
            
            # Anomalous Behavior Patterns
            SecurityPattern(
                name="Anomaly - Unusual Login Time",
                threat_type=ThreatType.ANOMALOUS_BEHAVIOR,
                severity=SeverityLevel.MEDIUM,
                description="Login at unusual time",
                patterns=[
                    r"User (.*) logged in at (\d{2}:\d{2}:\d{2})",
                    r"login.*user: (.*) time: (\d{2}:\d{2}:\d{2})"
                ],
                conditions={"user": "extract", "time": "extract", "unusual_hours": [22, 23, 0, 1, 2, 3, 4, 5]},
                time_window=300,
                threshold=1,
                tags=["anomaly", "login", "behavior"]
            )
        ]
        
        self.patterns.extend(default_patterns)
        logger.info(f"Loaded {len(default_patterns)} default security patterns")
    
    async def analyze_log(self, log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a single log entry for security threats"""
        try:
            # Parse log into SecurityEvent
            event = self._parse_log_event(log_data)
            
            # Add to history
            self.event_history.append(event)
            
            # Update statistics
            self.detection_stats["total_events"] += 1
            
            # Check against all patterns
            threats = []
            
            for pattern in self.patterns:
                try:
                    matches = await self._check_pattern(event, pattern)
                    if matches:
                        threat = await self._create_threat_alert(event, pattern, matches)
                        threats.append(threat)
                        self.detection_stats["threats_detected"] += 1
                        self.detection_stats["patterns_matched"][pattern.name] += 1
                        
                except Exception as e:
                    logger.error(f"Error checking pattern {pattern.name}: {e}")
            
            # Update IP reputation
            await self._update_ip_reputation(event, threats)
            
            # Update user behavior
            await self._update_user_behavior(event, threats)
            
            return threats
            
        except Exception as e:
            logger.error(f"Failed to analyze log: {e}")
            return []
    
    async def analyze_batch(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple log entries"""
        all_threats = []
        
        for log_data in logs:
            threats = await self.analyze_log(log_data)
            all_threats.extend(threats)
        
        return all_threats
    
    async def _check_pattern(self, event: SecurityEvent, pattern: SecurityPattern) -> List[Dict[str, Any]]:
        """Check if event matches security pattern"""
        matches = []
        
        for compiled_pattern in pattern.compiled_patterns:
            match = compiled_pattern.search(event.message)
            if match:
                match_data = {
                    "pattern": pattern.name,
                    "matched_text": match.group(0),
                    "groups": match.groups(),
                    "timestamp": event.timestamp
                }
                matches.append(match_data)
        
        if matches:
            # Check additional conditions
            if await self._check_conditions(event, pattern, matches):
                return matches
        
        return []
    
    async def _check_conditions(self, event: SecurityEvent, pattern: SecurityPattern, matches: List[Dict[str, Any]]) -> bool:
        """Check additional pattern conditions"""
        try:
            # Time window check
            if pattern.time_window > 0:
                recent_events = [
                    e for e in self.event_history
                    if (event.timestamp - e.timestamp).total_seconds() <= pattern.time_window
                ]
                
                # Count matching events in time window
                matching_count = 0
                for recent_event in recent_events:
                    for compiled_pattern in pattern.compiled_patterns:
                        if compiled_pattern.search(recent_event.message):
                            matching_count += 1
                            break
                
                if matching_count < pattern.threshold:
                    return False
            
            # Additional condition checks
            if "source_ip" in pattern.conditions:
                # Check if source IP is in reputation database
                if event.source_ip in self.ip_reputation:
                    ip_rep = self.ip_reputation[event.source_ip]
                    if ip_rep.get("malicious", False):
                        return True
            
            if "user" in pattern.conditions:
                # Check for admin users
                admin_users = pattern.conditions.get("admin_users", [])
                if event.user and event.user.lower() in [u.lower() for u in admin_users]:
                    return True
            
            if "unusual_hours" in pattern.conditions:
                # Check for unusual login times
                unusual_hours = pattern.conditions.get("unusual_hours", [])
                if event.timestamp.hour in unusual_hours:
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking conditions for pattern {pattern.name}: {e}")
            return False
    
    async def _create_threat_alert(self, event: SecurityEvent, pattern: SecurityPattern, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create threat alert from pattern match"""
        return {
            "alert_id": f"threat_{int(event.timestamp.timestamp())}_{pattern.name.replace(' ', '_')}",
            "threat_type": pattern.threat_type.value,
            "severity": pattern.severity.value,
            "pattern_name": pattern.name,
            "description": pattern.description,
            "source_event": event.to_dict(),
            "matches": matches,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": pattern.tags,
            "confidence": self._calculate_confidence(event, pattern, matches),
            "mitigation_advice": self._get_mitigation_advice(pattern.threat_type)
        }
    
    def _calculate_confidence(self, event: SecurityEvent, pattern: SecurityPattern, matches: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for threat detection"""
        base_confidence = 0.5
        
        # Increase confidence based on pattern severity
        severity_multiplier = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4,
            SeverityLevel.INFO: 0.2
        }
        
        base_confidence *= severity_multiplier.get(pattern.severity, 0.5)
        
        # Increase confidence based on IP reputation
        if event.source_ip in self.ip_reputation:
            ip_rep = self.ip_reputation[event.source_ip]
            if ip_rep.get("malicious", False):
                base_confidence += 0.3
            elif ip_rep.get("suspicious", False):
                base_confidence += 0.1
        
        # Increase confidence based on user behavior
        if event.user and event.user in self.user_behavior:
            user_behavior = self.user_behavior[event.user]
            if user_behavior.get("anomalous", False):
                base_confidence += 0.2
        
        # Cap confidence at 1.0
        return min(base_confidence, 1.0)
    
    def _get_mitigation_advice(self, threat_type: ThreatType) -> List[str]:
        """Get mitigation advice for threat type"""
        advice_map = {
            ThreatType.BRUTE_FORCE: [
                "Block source IP address",
                "Implement rate limiting",
                "Enable account lockout policies",
                "Review authentication logs"
            ],
            ThreatType.LATERAL_MOVEMENT: [
                "Isolate affected systems",
                "Review user privileges",
                "Audit network segmentation",
                "Enable multi-factor authentication"
            ],
            ThreatType.MALWARE: [
                "Isolate infected systems",
                "Run antivirus scans",
                "Review process logs",
                "Update security signatures"
            ],
            ThreatType.INTRUSION: [
                "Block malicious IPs",
                "Review firewall rules",
                "Patch vulnerable systems",
                "Monitor for further activity"
            ],
            ThreatType.DATA_EXFILTRATION: [
                "Block data transfers",
                "Review access logs",
                "Enable DLP controls",
                "Audit data access permissions"
            ],
            ThreatType.C2_COMMUNICATION: [
                "Block C2 server IPs",
                "Review network traffic",
                "Implement DNS filtering",
                "Monitor outbound connections"
            ],
            ThreatType.ANOMALOUS_BEHAVIOR: [
                "Review user activity",
                "Verify legitimate access",
                "Monitor for further anomalies",
                "Update behavior baselines"
            ]
        }
        
        return advice_map.get(threat_type, ["Review security logs", "Monitor system activity"])
    
    def _parse_log_event(self, log_data: Dict[str, Any]) -> SecurityEvent:
        """Parse log data into SecurityEvent"""
        # Extract timestamp
        timestamp_str = log_data.get("timestamp", datetime.utcnow().isoformat())
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = timestamp_str
        
        # Extract IP addresses
        source_ip = log_data.get("source_ip", "")
        target_ip = log_data.get("target_ip", "")
        
        # If not provided, try to extract from message
        if not source_ip:
            ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
            ips = re.findall(ip_pattern, log_data.get("message", ""))
            source_ip = ips[0] if ips else ""
        
        return SecurityEvent(
            timestamp=timestamp,
            source_ip=source_ip,
            target_ip=target_ip,
            event_type=log_data.get("event_type", "unknown"),
            message=log_data.get("message", ""),
            severity=log_data.get("severity", "info"),
            user=log_data.get("user"),
            process=log_data.get("process"),
            raw_log=log_data.get("raw_log")
        )
    
    async def _update_ip_reputation(self, event: SecurityEvent, threats: List[Dict[str, Any]]):
        """Update IP reputation based on events and threats"""
        if not event.source_ip:
            return
        
        if event.source_ip not in self.ip_reputation:
            self.ip_reputation[event.source_ip] = {
                "first_seen": event.timestamp,
                "last_seen": event.timestamp,
                "event_count": 0,
                "threat_count": 0,
                "malicious": False,
                "suspicious": False
            }
        
        # Update reputation
        rep = self.ip_reputation[event.source_ip]
        rep["last_seen"] = event.timestamp
        rep["event_count"] += 1
        
        if threats:
            rep["threat_count"] += len(threats)
            
            # Mark as malicious if high severity threats detected
            for threat in threats:
                if threat["severity"] <= 2:  # Critical or High
                    rep["malicious"] = True
                elif threat["severity"] <= 3:  # Medium
                    rep["suspicious"] = True
    
    async def _update_user_behavior(self, event: SecurityEvent, threats: List[Dict[str, Any]]):
        """Update user behavior baseline"""
        if not event.user:
            return
        
        if event.user not in self.user_behavior:
            self.user_behavior[event.user] = {
                "first_seen": event.timestamp,
                "last_seen": event.timestamp,
                "login_count": 0,
                "unique_ips": set(),
                "threat_count": 0,
                "anomalous": False,
                "typical_hours": set()
            }
        
        # Update behavior
        behavior = self.user_behavior[event.user]
        behavior["last_seen"] = event.timestamp
        behavior["login_count"] += 1
        
        if event.source_ip:
            behavior["unique_ips"].add(event.source_ip)
        
        if threats:
            behavior["threat_count"] += len(threats)
            behavior["anomalous"] = True
        
        # Track typical login hours
        behavior["typical_hours"].add(event.timestamp.hour)
        
        # Check for anomalous behavior
        if len(behavior["unique_ips"]) > 5:  # Login from many IPs
            behavior["anomalous"] = True
        
        if behavior["threat_count"] > 0:
            behavior["anomalous"] = True
    
    async def get_threat_summary(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get threat summary for time window"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
            
            recent_threats = []
            recent_events = [
                event for event in self.event_history
                if event.timestamp >= cutoff_time
            ]
            
            # Count threats by type
            threat_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for event in recent_events:
                # This would require storing threats with events
                # For now, return basic statistics
                pass
            
            return {
                "time_window": time_window,
                "total_events": len(recent_events),
                "threat_counts": dict(threat_counts),
                "severity_counts": dict(severity_counts),
                "ip_reputation": {
                    ip: rep for ip, rep in self.ip_reputation.items()
                    if rep["last_seen"] >= cutoff_time
                },
                "user_behavior": {
                    user: {**behavior, "unique_ips": len(behavior["unique_ips"])}
                    for user, behavior in self.user_behavior.items()
                    if behavior["last_seen"] >= cutoff_time
                },
                "detection_stats": self.detection_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get threat summary: {e}")
            return {"error": str(e)}
    
    async def add_custom_pattern(self, pattern: SecurityPattern) -> Dict[str, Any]:
        """Add custom security pattern"""
        try:
            self.patterns.append(pattern)
            logger.info(f"Added custom pattern: {pattern.name}")
            return {
                "status": "success",
                "pattern": pattern.name,
                "total_patterns": len(self.patterns)
            }
        except Exception as e:
            logger.error(f"Failed to add custom pattern: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get pattern engine statistics"""
        return {
            **self.detection_stats,
            "total_patterns": len(self.patterns),
            "event_history_size": len(self.event_history),
            "ip_reputation_size": len(self.ip_reputation),
            "user_behavior_size": len(self.user_behavior),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance
pattern_engine = PatternEngine()
