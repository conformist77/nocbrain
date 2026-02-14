import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RunbookService:
    """Service for managing runbooks and standard operating procedures"""
    
    def __init__(self):
        self.runbooks = {
            "high_cpu": {
                "title": "High CPU Usage",
                "symptoms": ["CPU usage > 80%", "Slow response times"],
                "steps": [
                    "Check top processes: top -c",
                    "Identify CPU-intensive processes",
                    "Check for runaway processes",
                    "Review application logs",
                    "Consider scaling resources"
                ],
                "commands": [
                    "top -c",
                    "ps aux --sort=-%cpu | head -10",
                    "iostat 1 5",
                    "df -h"
                ]
            },
            "memory_pressure": {
                "title": "Memory Pressure",
                "symptoms": ["Memory usage > 80%", "OOM killer events"],
                "steps": [
                    "Check memory usage: free -h",
                    "Identify memory-intensive processes",
                    "Check for memory leaks",
                    "Review swap usage",
                    "Consider adding memory"
                ],
                "commands": [
                    "free -h",
                    "ps aux --sort=-%mem | head -10",
                    "vmstat 1 5",
                    "cat /proc/meminfo"
                ]
            },
            "disk_space": {
                "title": "Disk Space Issues",
                "symptoms": ["Disk usage > 85%", "Write failures"],
                "steps": [
                    "Check disk usage: df -h",
                    "Find large files: find / -size +1G",
                    "Clear log files if needed",
                    "Archive old data",
                    "Add storage capacity"
                ],
                "commands": [
                    "df -h",
                    "du -sh /* | sort -hr | head -10",
                    "find /var/log -name '*.log' -size +100M",
                    "ls -la /tmp"
                ]
            },
            "network_connectivity": {
                "title": "Network Connectivity Issues",
                "symptoms": ["Packet loss", "High latency", "Connection timeouts"],
                "steps": [
                    "Test basic connectivity: ping",
                    "Check network interfaces: ip addr",
                    "Review firewall rules",
                    "Check DNS resolution",
                    "Test port connectivity"
                ],
                "commands": [
                    "ping -c 4 8.8.8.8",
                    "ip addr show",
                    "iptables -L",
                    "nslookup google.com",
                    "telnet target-host 80"
                ]
            }
        }
    
    def get_runbook(self, issue_type: str) -> Dict[str, Any]:
        """Get runbook for specific issue type"""
        return self.runbooks.get(issue_type, {})
    
    def search_runbooks(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """Search runbooks based on symptoms"""
        matching_runbooks = []
        
        for key, runbook in self.runbooks.items():
            symptom_matches = 0
            for symptom in symptoms:
                if any(symptom.lower() in s.lower() for s in runbook["symptoms"]):
                    symptom_matches += 1
            
            if symptom_matches > 0:
                matching_runbooks.append({
                    "runbook": runbook,
                    "relevance_score": symptom_matches / len(symptoms),
                    "matched_symptoms": symptom_matches
                })
        
        # Sort by relevance score
        matching_runbooks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matching_runbooks
    
    def get_remediation_steps(self, alert_messages: List[str]) -> Dict[str, Any]:
        """Get remediation steps based on alert messages"""
        # Simple keyword matching for now
        all_symptoms = []
        
        for message in alert_messages:
            message_lower = message.lower()
            if "cpu" in message_lower:
                all_symptoms.append("High CPU usage")
            if "memory" in message_lower or "oom" in message_lower:
                all_symptoms.append("Memory pressure")
            if "disk" in message_lower or "space" in message_lower:
                all_symptoms.append("Disk space issues")
            if "network" in message_lower or "connectivity" in message_lower:
                all_symptoms.append("Network connectivity issues")
        
        # Get matching runbooks
        matching_runbooks = self.search_runbooks(all_symptoms)
        
        if matching_runbooks:
            best_match = matching_runbooks[0]
            return {
                "recommended_runbook": best_match["runbook"],
                "relevance_score": best_match["relevance_score"],
                "alternative_runbooks": matching_runbooks[1:3] if len(matching_runbooks) > 1 else []
            }
        else:
            return {
                "recommended_runbook": None,
                "message": "No specific runbook found for these symptoms"
            }
