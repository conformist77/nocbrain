import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import ipaddress
import socket
import subprocess
import time

from pysnmp.hlapi import *
from netmiko import ConnectHandler
import structlog

from app.core.database import AsyncSession
from app.schemas.network import (
    DeviceCreate, DeviceResponse, DeviceUpdate,
    NetworkScanRequest, NetworkScanResult, DiscoveredDevice,
    NetworkTopologyResponse, NetworkNode, NetworkEdge,
    NetworkMetricsResponse, DeviceMetrics, MetricData
)
from app.models.network import Device, DeviceMetric, NetworkAlert

logger = structlog.get_logger(__name__)


class NetworkService:
    def __init__(self):
        self.active_scans: Dict[str, asyncio.Task] = {}
        
    async def add_device(self, db: AsyncSession, device_data: DeviceCreate, user_id: int) -> DeviceResponse:
        """Add a new network device for monitoring"""
        try:
            # Test connectivity
            is_reachable = await self._test_connectivity(device_data.ip_address)
            
            # Test SNMP if configured
            snmp_configured = False
            if device_data.snmp_community:
                snmp_configured = await self._test_snmp(
                    device_data.ip_address,
                    device_data.snmp_community,
                    device_data.snmp_port,
                    device_data.snmp_version.value
                )
            
            # Create device record
            device = Device(
                name=device_data.name,
                ip_address=device_data.ip_address,
                device_type=device_data.device_type.value,
                description=device_data.description,
                location=device_data.location,
                vendor=device_data.vendor,
                model=device_data.model,
                os_version=device_data.os_version,
                snmp_community=device_data.snmp_community,
                snmp_port=device_data.snmp_port,
                snmp_version=device_data.snmp_version.value,
                snmp_username=device_data.snmp_username,
                snmp_password=device_data.snmp_password,
                snmp_security_level=device_data.snmp_security_level,
                monitoring_enabled=device_data.monitoring_enabled,
                status="online" if is_reachable else "offline",
                last_seen=datetime.utcnow() if is_reachable else None,
                created_by=user_id,
                snmp_configured=snmp_configured
            )
            
            # Save to database
            db.add(device)
            await db.commit()
            await db.refresh(device)
            
            # Start monitoring if enabled
            if device_data.monitoring_enabled:
                asyncio.create_task(self._start_device_monitoring(device.id))
            
            return DeviceResponse.from_orm(device)
            
        except Exception as e:
            logger.error(f"Failed to add device {device_data.name}: {e}")
            raise
    
    async def get_devices(self, db: AsyncSession, skip: int, limit: int, user_id: int) -> List[DeviceResponse]:
        """Get list of monitored devices"""
        # This would query the database
        # For now, return empty list
        return []
    
    async def get_device(self, db: AsyncSession, device_id: int, user_id: int) -> Optional[DeviceResponse]:
        """Get specific device details"""
        # This would query the database
        return None
    
    async def update_device(self, db: AsyncSession, device_id: int, device_update: DeviceUpdate, user_id: int) -> Optional[DeviceResponse]:
        """Update device configuration"""
        # This would update the database
        return None
    
    async def delete_device(self, db: AsyncSession, device_id: int, user_id: int) -> bool:
        """Remove device from monitoring"""
        # This would delete from database
        return True
    
    async def scan_network(self, db: AsyncSession, scan_request: NetworkScanRequest, user_id: int) -> NetworkScanResult:
        """Scan network for discoverable devices"""
        scan_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Parse IP range
            network = ipaddress.ip_network(scan_request.ip_range, strict=False)
            total_ips = network.num_addresses
            
            # Limit scan size for performance
            if total_ips > 1024:
                raise ValueError("IP range too large. Maximum 1024 addresses allowed.")
            
            # Start scan
            scan_task = asyncio.create_task(
                self._perform_network_scan(network, scan_request, scan_id)
            )
            self.active_scans[scan_id] = scan_task
            
            # Wait for completion
            discovered_devices = await scan_task
            
            # Create result
            scan_duration = time.time() - start_time
            result = NetworkScanResult(
                scan_id=scan_id,
                ip_range=scan_request.ip_range,
                total_ips=total_ips,
                reachable_ips=len(discovered_devices),
                discovered_devices=discovered_devices,
                scan_duration=scan_duration,
                timestamp=datetime.utcnow()
            )
            
            # Clean up
            del self.active_scans[scan_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            raise
    
    async def get_network_topology(self, db: AsyncSession, user_id: int) -> NetworkTopologyResponse:
        """Get network topology visualization data"""
        # This would query devices and their connections
        nodes = []
        edges = []
        
        return NetworkTopologyResponse(
            nodes=nodes,
            edges=edges,
            last_updated=datetime.utcnow()
        )
    
    async def get_network_metrics(self, db: AsyncSession, device_id: Optional[int], time_range: str, user_id: int) -> NetworkMetricsResponse:
        """Get network performance metrics"""
        # This would query metrics from database
        return NetworkMetricsResponse(
            time_range=time_range,
            total_devices=0,
            online_devices=0,
            offline_devices=0,
            devices_with_warnings=0,
            critical_devices=0,
            overall_health="unknown",
            metrics=[],
            summary={}
        )
    
    async def configure_snmp(self, db: AsyncSession, device_id: int, snmp_config, user_id: int) -> Dict[str, Any]:
        """Configure SNMP settings for a device"""
        # This would update device SNMP configuration
        return {"message": "SNMP configuration updated successfully"}
    
    async def get_realtime_data(self) -> Dict[str, Any]:
        """Get real-time network data for WebSocket"""
        # This would return current network status
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "devices": [],
            "alerts": [],
            "metrics": {}
        }
    
    async def _test_connectivity(self, ip_address: str, timeout: int = 5) -> bool:
        """Test if a device is reachable via ping"""
        try:
            # Use subprocess for ping
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', str(timeout), ip_address]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 1
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Ping test failed for {ip_address}: {e}")
            return False
    
    async def _test_snmp(self, ip_address: str, community: str, port: int, version: str) -> bool:
        """Test SNMP connectivity"""
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((ip_address, port)),
                ContextData(),
                ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
            )
            
            error_indication, error_status, error_index, var_binds = next(iterator)
            
            if error_indication:
                logger.error(f"SNMP error for {ip_address}: {error_indication}")
                return False
            
            if error_status:
                logger.error(f"SNMP error for {ip_address}: {error_status}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"SNMP test failed for {ip_address}: {e}")
            return False
    
    async def _perform_network_scan(self, network: ipaddress.IPv4Network, scan_request: NetworkScanRequest, scan_id: str) -> List[DiscoveredDevice]:
        """Perform the actual network scan"""
        discovered_devices = []
        semaphore = asyncio.Semaphore(scan_request.max_concurrent)
        
        async def scan_host(ip: ipaddress.IPv4Address) -> Optional[DiscoveredDevice]:
            async with semaphore:
                try:
                    # Test connectivity
                    is_reachable = await self._test_connectivity(str(ip), scan_request.timeout)
                    if not is_reachable:
                        return None
                    
                    device = DiscoveredDevice(
                        ip_address=str(ip),
                        hostname=socket.gethostbyaddr(str(ip))[0] if socket.gethostbyaddr(str(ip))[0] else None,
                        snmp_available=await self._test_snmp(str(ip), "public", 161, "2c") if scan_request.scan_type in ["snmp", "comprehensive"] else False
                    )
                    
                    return device
                    
                except Exception as e:
                    logger.debug(f"Failed to scan {ip}: {e}")
                    return None
        
        # Create tasks for all IPs
        tasks = [scan_host(ip) for ip in network.hosts()]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        for result in results:
            if isinstance(result, DiscoveredDevice):
                discovered_devices.append(result)
        
        return discovered_devices
    
    async def _start_device_monitoring(self, device_id: int):
        """Start background monitoring for a device"""
        while True:
            try:
                # Collect metrics
                await self._collect_device_metrics(device_id)
                await asyncio.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error(f"Device monitoring error for {device_id}: {e}")
                await asyncio.sleep(60)
    
    async def _collect_device_metrics(self, device_id: int):
        """Collect metrics from a specific device"""
        # This would implement SNMP polling, SSH commands, etc.
        pass
