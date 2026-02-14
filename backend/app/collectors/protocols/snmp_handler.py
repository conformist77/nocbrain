"""
NOCbRAIN SNMP Protocol Handler
Handles SNMP communication with network devices for Zabbix integration
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, getCmd, getNextCmd, bulkCmd,
    SnmpException, error
)
from pysnmp.proto.rfc1902 import Integer, OctetString, Gauge32

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SNMPDevice:
    """SNMP device configuration"""
    host: str
    community: str = "public"
    version: int = 2  # SNMPv2c
    port: int = 161
    timeout: int = 3
    retries: int = 2
    device_type: str = "unknown"
    oids: List[str] = None
    
    def __post_init__(self):
        if self.oids is None:
            self.oids = self._get_default_oids()
    
    def _get_default_oids(self) -> List[str]:
        """Get default OIDs based on device type"""
        common_oids = [
            "1.3.6.1.2.1.1.1.0",  # sysDescr
            "1.3.6.1.2.1.1.3.0",  # sysUpTime
            "1.3.6.1.2.1.1.5.0",  # sysName
            "1.3.6.1.2.1.2.2.1.10",  # ifInOctets
            "1.3.6.1.2.1.2.2.1.16",  # ifOutOctets
            "1.3.6.1.2.1.2.1.0",   # ifNumber
        ]
        
        if self.device_type.lower() == "cisco":
            common_oids.extend([
                "1.3.6.1.4.1.9.2.1.1.0",  # cpuUtilization
                "1.3.6.1.4.1.9.9.109.1.1.1.1.3.1",  # memPoolUsed
                "1.3.6.1.4.1.9.9.109.1.1.1.1.4.1",  # memPoolFree
            ])
        elif self.device_type.lower() == "juniper":
            common_oids.extend([
                "1.3.6.1.4.1.2636.3.1.13.1.8",  # jnxOperatingCPU
                "1.3.6.1.4.1.2636.3.1.13.1.11", # jnxOperatingBuffer
            ])
        
        return common_oids


class SNMPHandler:
    """Main SNMP protocol handler"""
    
    def __init__(self):
        self.snmp_engine = SnmpEngine()
        self.active_connections: Dict[str, SNMPDevice] = {}
        self.collection_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
        logger.info("SNMP Handler initialized")
    
    async def add_device(self, device: SNMPDevice) -> Dict[str, Any]:
        """Add a new SNMP device for monitoring"""
        try:
            # Test connectivity
            test_result = await self.test_connection(device)
            
            if test_result["status"] == "success":
                self.active_connections[device.host] = device
                logger.info(f"Added SNMP device: {device.host}")
                return {
                    "status": "success",
                    "device": device.host,
                    "device_type": device.device_type,
                    "test_result": test_result
                }
            else:
                logger.error(f"Failed to connect to {device.host}: {test_result['error']}")
                return {
                    "status": "error",
                    "device": device.host,
                    "error": test_result["error"]
                }
                
        except Exception as e:
            logger.error(f"Failed to add device {device.host}: {e}")
            return {
                "status": "error",
                "device": device.host,
                "error": str(e)
            }
    
    async def remove_device(self, host: str) -> Dict[str, Any]:
        """Remove SNMP device from monitoring"""
        try:
            if host in self.active_connections:
                del self.active_connections[host]
                logger.info(f"Removed SNMP device: {host}")
                return {"status": "success", "device": host}
            else:
                return {"status": "error", "device": host, "error": "Device not found"}
                
        except Exception as e:
            logger.error(f"Failed to remove device {host}: {e}")
            return {"status": "error", "device": host, "error": str(e)}
    
    async def test_connection(self, device: SNMPDevice) -> Dict[str, Any]:
        """Test SNMP connectivity to device"""
        try:
            start_time = datetime.utcnow()
            
            # Try to get system description
            result = await self._get_snmp_value(
                device, 
                "1.3.6.1.2.1.1.1.0"  # sysDescr
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "response_time": response_time,
                    "system_description": result["value"],
                    "device_type": device.device_type
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Connection test failed for {device.host}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "device": device.host
            }
    
    async def collect_metrics(self, host: str) -> Dict[str, Any]:
        """Collect SNMP metrics from device"""
        try:
            if host not in self.active_connections:
                return {
                    "status": "error",
                    "device": host,
                    "error": "Device not found in active connections"
                }
            
            device = self.active_connections[host]
            start_time = datetime.utcnow()
            
            # Collect all configured OIDs
            metrics = {}
            errors = []
            
            for oid in device.oids:
                try:
                    result = await self._get_snmp_value(device, oid)
                    
                    if result["status"] == "success":
                        # Parse OID name and store value
                        oid_name = self._get_oid_name(oid)
                        metrics[oid_name] = {
                            "value": result["value"],
                            "oid": oid,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        errors.append(f"OID {oid}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"OID {oid}: {str(e)}")
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update statistics
            self._update_stats(True, response_time)
            
            return {
                "status": "success",
                "device": host,
                "device_type": device.device_type,
                "metrics": metrics,
                "errors": errors,
                "response_time": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect metrics from {host}: {e}")
            self._update_stats(False, 0)
            return {
                "status": "error",
                "device": host,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def collect_interface_stats(self, host: str) -> Dict[str, Any]:
        """Collect detailed interface statistics"""
        try:
            if host not in self.active_connections:
                return {"status": "error", "device": host, "error": "Device not found"}
            
            device = self.active_connections[host]
            
            # Get interface count
            if_count_result = await self._get_snmp_value(device, "1.3.6.1.2.1.2.1.0")
            
            if if_count_result["status"] != "success":
                return if_count_result
            
            interface_count = int(if_count_result["value"])
            interfaces = {}
            
            # Collect stats for each interface
            for if_index in range(1, interface_count + 1):
                interface_oids = {
                    "name": f"1.3.6.1.2.1.2.2.1.2.{if_index}",
                    "status": f"1.3.6.1.2.1.2.2.1.8.{if_index}",
                    "in_octets": f"1.3.6.1.2.1.2.2.1.10.{if_index}",
                    "out_octets": f"1.3.6.1.2.1.2.2.1.16.{if_index}",
                    "in_packets": f"1.3.6.1.2.1.2.2.1.11.{if_index}",
                    "out_packets": f"1.3.6.1.2.1.2.2.1.17.{if_index}",
                    "in_errors": f"1.3.6.1.2.1.2.2.1.14.{if_index}",
                    "out_errors": f"1.3.6.1.2.1.2.2.1.20.{if_index}"
                }
                
                interface_data = {}
                for field, oid in interface_oids.items():
                    try:
                        result = await self._get_snmp_value(device, oid)
                        if result["status"] == "success":
                            interface_data[field] = result["value"]
                    except:
                        continue
                
                if interface_data:
                    interfaces[str(if_index)] = interface_data
            
            return {
                "status": "success",
                "device": host,
                "interface_count": interface_count,
                "interfaces": interfaces,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect interface stats from {host}: {e}")
            return {
                "status": "error",
                "device": host,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def discover_devices(self, network_range: str, community: str = "public") -> List[Dict[str, Any]]:
        """Discover SNMP devices in network range"""
        try:
            # This is a simplified discovery - in production, you'd want more sophisticated scanning
            discovered_devices = []
            
            # For now, return empty list - implement actual network discovery as needed
            logger.info(f"Device discovery requested for {network_range}")
            
            return discovered_devices
            
        except Exception as e:
            logger.error(f"Failed to discover devices in {network_range}: {e}")
            return []
    
    async def _get_snmp_value(self, device: SNMPDevice, oid: str) -> Dict[str, Any]:
        """Get single SNMP value from device"""
        try:
            # Create community data
            community_data = CommunityData(
                device.community,
                mpModel=0 if device.version == 1 else 1
            )
            
            # Create transport target
            transport_target = UdpTransportTarget(
                (device.host, device.port),
                timeout=device.timeout,
                retries=device.retries
            )
            
            # Execute SNMP GET
            error_indication, error_status, error_index, var_binds = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: getCmd(
                    self.snmp_engine,
                    community_data,
                    transport_target,
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                )
            )
            
            if error_indication:
                return {
                    "status": "error",
                    "error": str(error_indication),
                    "oid": oid
                }
            
            if error_status:
                return {
                    "status": "error",
                    "error": f"SNMP error: {error_status.prettyPrint()} at {error_index}",
                    "oid": oid
                }
            
            # Extract value
            for var_bind in var_binds:
                value = var_bind[1]
                
                # Convert SNMP value to appropriate Python type
                if isinstance(value, OctetString):
                    py_value = str(value)
                elif isinstance(value, (Integer, Gauge32)):
                    py_value = int(value)
                else:
                    py_value = str(value)
                
                return {
                    "status": "success",
                    "value": py_value,
                    "oid": oid,
                    "type": type(value).__name__
                }
            
            return {
                "status": "error",
                "error": "No value returned",
                "oid": oid
            }
            
        except Exception as e:
            logger.error(f"SNMP GET failed for {device.host}:{oid}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "oid": oid
            }
    
    def _get_oid_name(self, oid: str) -> str:
        """Get human-readable name for OID"""
        oid_mapping = {
            "1.3.6.1.2.1.1.1.0": "system_description",
            "1.3.6.1.2.1.1.3.0": "system_uptime",
            "1.3.6.1.2.1.1.5.0": "system_name",
            "1.3.6.1.2.1.2.1.0": "interface_count",
            "1.3.6.1.2.1.2.2.1.10": "if_in_octets",
            "1.3.6.1.2.1.2.2.1.16": "if_out_octets",
            "1.3.6.1.4.1.9.2.1.1.0": "cpu_utilization",
            "1.3.6.1.4.1.9.9.109.1.1.1.1.3.1": "memory_pool_used",
            "1.3.6.1.4.1.9.9.109.1.1.1.1.4.1": "memory_pool_free",
        }
        
        return oid_mapping.get(oid, f"oid_{oid.replace('.', '_')}")
    
    def _update_stats(self, success: bool, response_time: float):
        """Update collection statistics"""
        self.collection_stats["total_requests"] += 1
        
        if success:
            self.collection_stats["successful_requests"] += 1
        else:
            self.collection_stats["failed_requests"] += 1
        
        # Update average response time
        total = self.collection_stats["total_requests"]
        current_avg = self.collection_stats["average_response_time"]
        self.collection_stats["average_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get SNMP handler statistics"""
        return {
            **self.collection_stats,
            "active_devices": len(self.active_connections),
            "device_list": list(self.active_connections.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on SNMP handler"""
        try:
            stats = await self.get_stats()
            
            # Check if we have any active devices
            if stats["active_devices"] == 0:
                return {
                    "status": "warning",
                    "message": "No active SNMP devices",
                    "stats": stats
                }
            
            # Check success rate
            success_rate = (
                stats["successful_requests"] / stats["total_requests"] * 100
                if stats["total_requests"] > 0 else 100
            )
            
            if success_rate < 80:
                return {
                    "status": "warning",
                    "message": f"Low success rate: {success_rate:.1f}%",
                    "stats": stats
                }
            
            return {
                "status": "healthy",
                "message": "SNMP handler operating normally",
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Global instance
snmp_handler = SNMPHandler()
