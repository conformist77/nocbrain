#!/usr/bin/env python3
"""
NOCbRAIN Security Agent
Real-time security monitoring and threat detection
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import hashlib
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: str
    event_type: str
    severity: str
    source_ip: str
    target: str
    description: str
    raw_log: str
    confidence: float
    metadata: Dict[str, Any]

class SecurityAgent:
    """Main security agent class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_endpoint = config.get('api_endpoint', 'http://localhost:8000/api/v1')
        self.agent_id = config.get('agent_id', 'security-agent-001')
        self.log_sources = config.get('log_sources', [])
        self.thresholds = config.get('thresholds', {})
        
        # Security tracking
        self.failed_logins = defaultdict(lambda: deque(maxlen=50))
        self.suspicious_ips = defaultdict(int)
        self.port_scan_attempts = defaultdict(list)
        self.known_malicious_ips = set()
        
        # Load threat intelligence
        self.load_threat_intelligence()
        
        logger.info(f"Security Agent {self.agent_id} initialized")
    
    def load_threat_intelligence(self):
        """Load known malicious IPs and threat patterns"""
        # Sample threat intelligence (in production, load from external feeds)
        self.known_malicious_ips.update([
            '192.168.1.100',  # Example malicious IP
            '10.0.0.50',      # Example malicious IP
        ])
        
        # Common attack patterns
        self.attack_patterns = {
            'sql_injection': [
                r"union\s+select",
                r"or\s+1\s*=\s*1",
                r"drop\s+table",
                r"insert\s+into",
                r"delete\s+from"
            ],
            'xss': [
                r"<script[^>]*>",
                r"javascript:",
                r"onload\s*=",
                r"onerror\s*="
            ],
            'command_injection': [
                r";\s*ls",
                r";\s*cat",
                r";\s*rm",
                r"`.*`",
                r"\$\(",
                r"&&\s*"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c"
            ]
        }
        
        logger.info(f"Loaded {len(self.known_malicious_ips)} malicious IPs")
    
    async def parse_log_entry(self, log_line: str) -> Optional[Dict[str, Any]]:
        """Parse a log entry and extract relevant information"""
        try:
            # Common log formats
            patterns = [
                # Apache/Nginx access log
                r'(?P<ip>\d+\.\d+\.\d+\.\d+).*?\[(?P<timestamp>.*?)\].*?"(?P<method>\w+)\s+(?P<url>[^"]+).*?"(?P<status>\d+)',
                # SSH auth log
                r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+).*?sshd.*?from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)',
                # Firewall log
                r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+).*?SRC=(?P<ip>\d+\.\d+\.\d+\.\d+).*?DST=(?P<dest>\d+\.\d+\.\d+\.\d+).*?PROTO=(?P<protocol>\w+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, log_line, re.IGNORECASE)
                if match:
                    return match.groupdict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            return None
    
    def detect_brute_force(self, ip: str, timestamp: str) -> Optional[SecurityEvent]:
        """Detect brute force attacks"""
        try:
            current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Add to failed logins
            self.failed_logins[ip].append(current_time)
            
            # Check for multiple failed attempts in short time
            recent_attempts = [
                t for t in self.failed_logins[ip] 
                if current_time - t < timedelta(minutes=5)
            ]
            
            if len(recent_attempts) >= self.thresholds.get('failed_login_threshold', 5):
                return SecurityEvent(
                    timestamp=timestamp,
                    event_type='brute_force',
                    severity='high',
                    source_ip=ip,
                    target='ssh',
                    description=f'Brute force attack detected from {ip}',
                    raw_log='',
                    confidence=min(1.0, len(recent_attempts) / 10.0),
                    metadata={
                        'attempts': len(recent_attempts),
                        'time_window': '5 minutes'
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting brute force: {e}")
            return None
    
    def detect_port_scan(self, ip: str, port: int, timestamp: str) -> Optional[SecurityEvent]:
        """Detect port scanning attempts"""
        try:
            current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Track port access attempts
            self.port_scan_attempts[ip].append((port, current_time))
            
            # Clean old attempts
            self.port_scan_attempts[ip] = [
                (p, t) for p, t in self.port_scan_attempts[ip]
                if current_time - t < timedelta(minutes=1)
            ]
            
            # Check for multiple port accesses
            unique_ports = len(set(p for p, _ in self.port_scan_attempts[ip]))
            
            if unique_ports >= self.thresholds.get('port_scan_threshold', 10):
                return SecurityEvent(
                    timestamp=timestamp,
                    event_type='port_scan',
                    severity='medium',
                    source_ip=ip,
                    target='multiple_ports',
                    description=f'Port scanning detected from {ip}',
                    raw_log='',
                    confidence=min(1.0, unique_ports / 20.0),
                    metadata={
                        'ports_scanned': unique_ports,
                        'time_window': '1 minute'
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting port scan: {e}")
            return None
    
    def detect_web_attack(self, log_data: Dict[str, Any], log_line: str) -> List[SecurityEvent]:
        """Detect web-based attacks"""
        events = []
        
        try:
            url = log_data.get('url', '')
            method = log_data.get('method', '')
            ip = log_data.get('ip', '')
            timestamp = datetime.utcnow().isoformat()
            
            # Check for various attack patterns
            for attack_type, patterns in self.attack_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, url, re.IGNORECASE):
                        severity = 'high' if attack_type in ['sql_injection', 'command_injection'] else 'medium'
                        
                        event = SecurityEvent(
                            timestamp=timestamp,
                            event_type=attack_type,
                            severity=severity,
                            source_ip=ip,
                            target=url,
                            description=f'{attack_type.replace("_", " ").title()} attempt detected',
                            raw_log=log_line,
                            confidence=0.8,
                            metadata={
                                'method': method,
                                'pattern_matched': pattern,
                                'attack_type': attack_type
                            }
                        )
                        events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error detecting web attack: {e}")
            return []
    
    def analyze_with_ai(self, event: SecurityEvent) -> Dict[str, Any]:
        """Analyze security event with AI (simplified version)"""
        try:
            analysis = {
                'threat_level': 'low',
                'recommended_actions': [],
                'context': {},
                'correlation': []
            }
            
            # Determine threat level based on event
            if event.severity == 'critical':
                analysis['threat_level'] = 'critical'
                analysis['recommended_actions'].extend([
                    'Block source IP immediately',
                    'Isolate affected system',
                    'Notify security team'
                ])
            elif event.severity == 'high':
                analysis['threat_level'] = 'high'
                analysis['recommended_actions'].extend([
                    'Monitor source IP closely',
                    'Review access logs',
                    'Consider temporary block'
                ])
            elif event.severity == 'medium':
                analysis['threat_level'] = 'medium'
                analysis['recommended_actions'].extend([
                    'Log for further analysis',
                    'Update firewall rules if needed'
                ])
            
            # Add context based on event type
            if event.event_type == 'brute_force':
                analysis['context'] = {
                    'attack_vector': 'authentication',
                    'common_targets': ['SSH', 'RDP', 'Web applications'],
                    'mitigation': 'Rate limiting, account lockout'
                }
            elif event.event_type == 'port_scan':
                analysis['context'] = {
                    'attack_vector': 'reconnaissance',
                    'common_targets': 'Open ports',
                    'mitigation': 'Firewall rules, port knocking'
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {'threat_level': 'unknown', 'recommended_actions': [], 'context': {}}
    
    async def send_to_api(self, event: SecurityEvent, analysis: Dict[str, Any]) -> bool:
        """Send security event to central API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Agent-ID': self.agent_id
            }
            
            data = {
                'agent_id': self.agent_id,
                'event': event.__dict__,
                'analysis': analysis,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = requests.post(
                f"{self.api_endpoint}/security/events",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully sent security event to API")
                return True
            else:
                logger.warning(f"API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending event to API: {e}")
            return False
    
    async def monitor_logs(self):
        """Monitor log sources for security events"""
        logger.info("Starting log monitoring")
        
        # Simulate log monitoring (in production, would read from actual log files)
        sample_logs = [
            '192.168.1.100 - - [14/Feb/2026:10:30:00 +0000] "GET /admin/login HTTP/1.1" 401',
            '192.168.1.100 - - [14/Feb/2026:10:30:01 +0000] "POST /admin/login HTTP/1.1" 401',
            '192.168.1.100 - - [14/Feb/2026:10:30:02 +0000] "POST /admin/login HTTP/1.1" 401',
            '192.168.1.100 - - [14/Feb/2026:10:30:03 +0000] "POST /admin/login HTTP/1.1" 401',
            '192.168.1.100 - - [14/Feb/2026:10:30:04 +0000] "POST /admin/login HTTP/1.1" 401',
            '192.168.1.101 - - [14/Feb/2026:10:30:05 +0000] "GET /search?q=union+select+*+from+users HTTP/1.1" 200',
        ]
        
        for log_line in sample_logs:
            try:
                # Parse log entry
                log_data = await self.parse_log_entry(log_line)
                if not log_data:
                    continue
                
                # Detect security events
                events = []
                
                # Check for brute force
                if log_data.get('status') == '401':
                    brute_force_event = self.detect_brute_force(
                        log_data.get('ip', ''),
                        datetime.utcnow().isoformat()
                    )
                    if brute_force_event:
                        events.append(brute_force_event)
                
                # Check for web attacks
                web_events = self.detect_web_attack(log_data, log_line)
                events.extend(web_events)
                
                # Process detected events
                for event in events:
                    # Analyze with AI
                    analysis = self.analyze_with_ai(event)
                    
                    # Send to API
                    await self.send_to_api(event, analysis)
                    
                    logger.info(f"Detected {event.event_type} from {event.source_ip}")
                
                # Small delay between processing
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing log line: {e}")
    
    async def start(self):
        """Start the security agent"""
        logger.info(f"Starting security agent {self.agent_id}")
        
        try:
            await self.monitor_logs()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            logger.info("Security agent stopped")

async def main():
    """Main function to run the security agent"""
    # Load configuration
    config = {
        'agent_id': 'security-agent-001',
        'api_endpoint': 'http://localhost:8000/api/v1',
        'log_sources': ['/var/log/auth.log', '/var/log/nginx/access.log'],
        'thresholds': {
            'failed_login_threshold': 5,
            'port_scan_threshold': 10
        }
    }
    
    # Create and start agent
    agent = SecurityAgent(config)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\nShutting down security agent...")

if __name__ == "__main__":
    asyncio.run(main())
