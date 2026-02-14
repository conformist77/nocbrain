"""
NOCbRAIN Reasoning Engine
Core AI reasoning loop for processing logs and generating NOC Action Plans
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import logging

from app.core.logic.knowledge_manager import knowledge_manager
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PriorityLevel(Enum):
    """Priority levels for processing"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class EventType(Enum):
    """Event types for classification"""
    SYSTEM = "system"
    NETWORK = "network"
    SECURITY = "security"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"


class ReasoningEngine:
    """Main reasoning engine for NOCbRAIN"""
    
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.security_queue = asyncio.Queue()  # High priority queue
        self.is_running = False
        self.processing_stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "security_events": 0,
            "average_processing_time": 0.0
        }
        
        logger.info("Reasoning Engine initialized")
    
    async def start(self):
        """Start the reasoning engine"""
        if self.is_running:
            logger.warning("Reasoning engine is already running")
            return
        
        self.is_running = True
        
        # Start processing tasks
        asyncio.create_task(self._process_security_queue())
        asyncio.create_task(self._process_main_queue())
        
        logger.info("Reasoning engine started")
    
    async def stop(self):
        """Stop the reasoning engine"""
        self.is_running = False
        logger.info("Reasoning engine stopped")
    
    async def process_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a log entry through the reasoning engine"""
        try:
            start_time = datetime.utcnow()
            
            # Classify the log
            event_type, priority = self._classify_log(log_data)
            
            # Add to appropriate queue
            if event_type == EventType.SECURITY or priority == PriorityLevel.CRITICAL:
                await self.security_queue.put({
                    "log_data": log_data,
                    "event_type": event_type,
                    "priority": priority,
                    "timestamp": start_time
                })
            else:
                await self.processing_queue.put({
                    "log_data": log_data,
                    "event_type": event_type,
                    "priority": priority,
                    "timestamp": start_time
                })
            
            return {
                "status": "queued",
                "event_type": event_type.value,
                "priority": priority.name,
                "queue": "security" if event_type == EventType.SECURITY else "main",
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process log: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _process_security_queue(self):
        """Process high-priority security events"""
        while self.is_running:
            try:
                # Get from security queue with shorter timeout
                queue_item = await asyncio.wait_for(
                    self.security_queue.get(), 
                    timeout=1.0
                )
                
                result = await self._process_log_item(queue_item, is_security=True)
                await self._update_stats(result, is_security=True)
                
                # Mark task as done
                self.security_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in security queue processing: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_main_queue(self):
        """Process regular events"""
        while self.is_running:
            try:
                # Get from main queue
                queue_item = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                result = await self._process_log_item(queue_item, is_security=False)
                await self._update_stats(result, is_security=False)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in main queue processing: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_log_item(self, queue_item: Dict[str, Any], is_security: bool) -> Dict[str, Any]:
        """Process a single log item"""
        try:
            log_data = queue_item["log_data"]
            event_type = queue_item["event_type"]
            priority = queue_item["priority"]
            start_time = queue_item["timestamp"]
            
            # Extract relevant information
            log_content = self._extract_log_content(log_data)
            
            # Build context from log metadata
            context = [
                {
                    "type": "source",
                    "content": f"Source: {log_data.get('source', 'unknown')}"
                },
                {
                    "type": "timestamp",
                    "content": f"Timestamp: {log_data.get('timestamp', datetime.utcnow().isoformat())}"
                },
                {
                    "type": "severity",
                    "content": f"Severity: {log_data.get('severity', 'unknown')}"
                }
            ]
            
            # Add device/host information if available
            if "device" in log_data:
                context.append({
                    "type": "device",
                    "content": f"Device: {log_data['device']}"
                })
            
            if "host" in log_data:
                context.append({
                    "type": "host",
                    "content": f"Host: {log_data['host']}"
                })
            
            # Generate AI response using RAG
            ai_response = await knowledge_manager.generate_response(
                query=log_content,
                context=context,
                knowledge_type=event_type.value
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Build result
            result = {
                "status": "success",
                "log_id": log_data.get("id", "unknown"),
                "event_type": event_type.value,
                "priority": priority.name,
                "processing_time": processing_time,
                "ai_response": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "is_security": is_security
            }
            
            logger.info(f"Processed {event_type.value} event in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process log item: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "is_security": is_security
            }
    
    def _classify_log(self, log_data: Dict[str, Any]) -> tuple[EventType, PriorityLevel]:
        """Classify log event type and priority"""
        content = log_data.get("content", "").lower()
        source = log_data.get("source", "").lower()
        severity = log_data.get("severity", "").lower()
        
        # Security classification (highest priority)
        security_keywords = [
            "failed login", "brute force", "intrusion", "malware",
            "lateral movement", "unauthorized", "breach", "attack",
            "suspicious", "anomaly", "threat", "vulnerability"
        ]
        
        if any(keyword in content for keyword in security_keywords):
            return EventType.SECURITY, PriorityLevel.CRITICAL
        
        # Network events
        network_keywords = [
            "interface", "router", "switch", "firewall", "vlan",
            "routing", "bgp", "ospf", "packet", "bandwidth"
        ]
        
        if any(keyword in content for keyword in network_keywords):
            if "down" in content or "error" in content or "failed" in content:
                return EventType.NETWORK, PriorityLevel.HIGH
            else:
                return EventType.NETWORK, PriorityLevel.MEDIUM
        
        # System events
        system_keywords = [
            "cpu", "memory", "disk", "process", "service",
            "daemon", "kernel", "system", "boot"
        ]
        
        if any(keyword in content for keyword in system_keywords):
            if "critical" in severity or "error" in content:
                return EventType.SYSTEM, PriorityLevel.HIGH
            elif "warning" in severity:
                return EventType.SYSTEM, PriorityLevel.MEDIUM
            else:
                return EventType.SYSTEM, PriorityLevel.LOW
        
        # Application events
        if "application" in content or "app" in content:
            return EventType.APPLICATION, PriorityLevel.MEDIUM
        
        # Infrastructure events
        infra_keywords = [
            "vm", "virtualization", "container", "kubernetes",
            "docker", "proxmox", "vmware", "cloud"
        ]
        
        if any(keyword in content for keyword in infra_keywords):
            return EventType.INFRASTRUCTURE, PriorityLevel.MEDIUM
        
        # Default classification
        return EventType.SYSTEM, PriorityLevel.INFO
    
    def _extract_log_content(self, log_data: Dict[str, Any]) -> str:
        """Extract relevant content from log data"""
        content_parts = []
        
        # Main content
        if "content" in log_data:
            content_parts.append(log_data["content"])
        
        # Add structured fields
        for field in ["message", "description", "summary"]:
            if field in log_data and log_data[field]:
                content_parts.append(f"{field}: {log_data[field]}")
        
        # Add error details
        if "error" in log_data:
            content_parts.append(f"Error: {log_data['error']}")
        
        return " | ".join(content_parts)
    
    async def _update_stats(self, result: Dict[str, Any], is_security: bool):
        """Update processing statistics"""
        self.processing_stats["total_processed"] += 1
        
        if result["status"] == "success":
            self.processing_stats["successful"] += 1
        else:
            self.processing_stats["failed"] += 1
        
        if is_security:
            self.processing_stats["security_events"] += 1
        
        # Update average processing time
        if "processing_time" in result:
            current_avg = self.processing_stats["average_processing_time"]
            new_time = result["processing_time"]
            total_processed = self.processing_stats["total_processed"]
            
            # Calculate new average
            self.processing_stats["average_processing_time"] = (
                (current_avg * (total_processed - 1) + new_time) / total_processed
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get reasoning engine statistics"""
        return {
            **self.processing_stats,
            "queue_sizes": {
                "main_queue": self.processing_queue.qsize(),
                "security_queue": self.security_queue.qsize()
            },
            "is_running": self.is_running,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def generate_noc_action_plan(
        self, 
        incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive NOC Action Plan for incident"""
        try:
            # Build incident query
            incident_query = f"""
            Incident: {incident_data.get('title', 'Unknown')}
            Description: {incident_data.get('description', '')}
            Affected Systems: {incident_data.get('affected_systems', [])}
            Symptoms: {incident_data.get('symptoms', [])}
            """
            
            # Build context
            context = [
                {"type": "incident", "content": f"Incident ID: {incident_data.get('id', 'unknown')}"},
                {"type": "severity", "content": f"Severity: {incident_data.get('severity', 'unknown')}"},
                {"type": "impact", "content": f"Impact: {incident_data.get('impact', 'unknown')}"}
            ]
            
            # Generate AI response
            ai_response = await knowledge_manager.generate_response(
                query=incident_query,
                context=context
            )
            
            return {
                "status": "success",
                "incident_id": incident_data.get("id"),
                "noc_action_plan": ai_response.get("response"),
                "knowledge_used": ai_response.get("knowledge_results", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate NOC action plan: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def batch_process_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple logs in batch"""
        results = []
        
        for log in logs:
            result = await self.process_log(log)
            results.append(result)
        
        return results
    
    async def search_similar_incidents(
        self, 
        incident_description: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar historical incidents"""
        try:
            # Query knowledge base for similar incidents
            results = await knowledge_manager.query_knowledge(
                query=incident_description,
                knowledge_type="incident_report",
                top_k=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar incidents: {e}")
            return []


# Global instance
reasoning_engine = ReasoningEngine()
