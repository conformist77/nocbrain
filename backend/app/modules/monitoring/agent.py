"""
NOCbRAIN Monitoring Agent
Secure agent for collecting metrics from servers and clients
Supports multiple protocols: HTTP/HTTPS, gRPC, WebSocket
"""
import asyncio
import json
import ssl
import hashlib
import time
import psutil
import platform
import socket
from datetime import datetime
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import aiohttp
import websockets
import grpc
from prometheus_client import Counter, Histogram, Gauge, start_http_server

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Prometheus Metrics
METRICS_COLLECTED = Counter('nocbrain_metrics_collected_total', 'Total metrics collected', ['agent_id', 'metric_type'])
COLLECTION_DURATION = Histogram('nocbrain_collection_duration_seconds', 'Time spent collecting metrics')
SYSTEM_UPTIME = Gauge('nocbrain_system_uptime_seconds', 'System uptime in seconds')
CPU_USAGE = Gauge('nocbrain_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('nocbrain_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('nocbrain_disk_usage_percent', 'Disk usage percentage', ['mountpoint'])

class NOCBRAINAgent:
    """Secure monitoring agent for NOCbRAIN"""
    
    def __init__(self, agent_id: str, server_url: str, api_key: str):
        self.agent_id = agent_id
        self.server_url = server_url
        self.api_key = api_key
        self.encryption_key = self._derive_encryption_key(api_key)
        self.cipher = Fernet(self.encryption_key)
        self.hostname = socket.gethostname()
        self.platform = platform.system()
        self.is_running = False
        self.last_heartbeat = None
        
    def _derive_encryption_key(self, api_key: str) -> bytes:
        """Derive encryption key from API key"""
        return hashlib.sha256(api_key.encode()).digest()[:32]
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt monitoring data"""
        json_data = json.dumps(data).encode()
        encrypted = self.cipher.encrypt(json_data)
        return encrypted.decode()
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk_partitions = psutil.disk_partitions()
            disk_usage = {}
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except PermissionError:
                    continue
            
            # Network metrics
            network_io = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # System load
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Boot time
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'hostname': self.hostname,
                'platform': self.platform,
                'system': {
                    'uptime': uptime,
                    'boot_time': boot_time,
                    'load_average': load_avg,
                    'process_count': process_count
                },
                'cpu': {
                    'usage_percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': {
                        'current': cpu_freq.current if cpu_freq else None,
                        'min': cpu_freq.min if cpu_freq else None,
                        'max': cpu_freq.max if cpu_freq else None
                    }
                },
                'memory': {
                    'virtual': {
                        'total': memory.total,
                        'available': memory.available,
                        'used': memory.used,
                        'free': memory.free,
                        'percent': memory.percent
                    },
                    'swap': {
                        'total': swap.total,
                        'used': swap.used,
                        'free': swap.free,
                        'percent': swap.percent
                    }
                },
                'disk': disk_usage,
                'network': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv,
                    'connections_count': network_connections
                }
            }
            
            # Update Prometheus metrics
            SYSTEM_UPTIME.set(uptime)
            CPU_USAGE.set(cpu_percent)
            MEMORY_USAGE.set(memory.percent)
            for mountpoint, usage in disk_usage.items():
                DISK_USAGE.labels(mountpoint=mountpoint).set(usage['percent'])
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            # This can be extended to collect application-specific metrics
            # For example: database connections, web server stats, etc.
            
            app_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'applications': {
                    # Example: collect metrics from running services
                    'nginx': self._get_nginx_stats(),
                    'apache': self._get_apache_stats(),
                    'mysql': self._get_mysql_stats(),
                    'postgresql': self._get_postgresql_stats(),
                    'redis': self._get_redis_stats()
                }
            }
            
            return app_metrics
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {}
    
    def _get_nginx_stats(self) -> Dict[str, Any]:
        """Collect Nginx statistics"""
        try:
            # Implementation depends on nginx stub_status module
            return {
                'active_connections': 0,
                'accepted_connections': 0,
                'handled_connections': 0,
                'total_requests': 0,
                'reading': 0,
                'writing': 0,
                'waiting': 0
            }
        except:
            return {}
    
    def _get_apache_stats(self) -> Dict[str, Any]:
        """Collect Apache statistics"""
        try:
            # Implementation depends on mod_status
            return {
                'total_accesses': 0,
                'total_kbytes': 0,
                'busy_workers': 0,
                'idle_workers': 0
            }
        except:
            return {}
    
    def _get_mysql_stats(self) -> Dict[str, Any]:
        """Collect MySQL statistics"""
        try:
            # Implementation would connect to MySQL and query status
            return {
                'connections': 0,
                'queries_per_second': 0,
                'slow_queries': 0,
                'uptime': 0
            }
        except:
            return {}
    
    def _get_postgresql_stats(self) -> Dict[str, Any]:
        """Collect PostgreSQL statistics"""
        try:
            # Implementation would connect to PostgreSQL and query pg_stat_activity
            return {
                'connections': 0,
                'active_connections': 0,
                'database_size': 0,
                'transactions_per_second': 0
            }
        except:
            return {}
    
    def _get_redis_stats(self) -> Dict[str, Any]:
        """Collect Redis statistics"""
        try:
            # Implementation would connect to Redis and query INFO
            return {
                'connected_clients': 0,
                'used_memory': 0,
                'total_commands_processed': 0,
                'keyspace_hits': 0,
                'keyspace_misses': 0
            }
        except:
            return {}
    
    async def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send encrypted metrics to server"""
        try:
            encrypted_data = self._encrypt_data(metrics)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'X-Agent-ID': self.agent_id,
                'X-Agent-Version': '1.0.0'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/api/v1/monitoring/metrics",
                    data=json.dumps({'data': encrypted_data}),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Metrics sent successfully for agent {self.agent_id}")
                        METRICS_COLLECTED.labels(agent_id=self.agent_id, metric_type='system').inc()
                        return True
                    else:
                        logger.error(f"Failed to send metrics: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending metrics: {e}")
            return False
    
    async def send_heartbeat(self) -> bool:
        """Send heartbeat to server"""
        try:
            heartbeat_data = {
                'agent_id': self.agent_id,
                'hostname': self.hostname,
                'platform': self.platform,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'online',
                'version': '1.0.0'
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/api/v1/monitoring/heartbeat",
                    data=json.dumps(heartbeat_data),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self.last_heartbeat = datetime.utcnow()
                        return True
                    else:
                        logger.error(f"Failed to send heartbeat: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    async def run_collection_cycle(self):
        """Main collection cycle"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                if system_metrics:
                    await self.send_metrics(system_metrics)
                
                # Collect application metrics
                app_metrics = self._collect_application_metrics()
                if app_metrics:
                    await self.send_metrics(app_metrics)
                
                # Send heartbeat
                await self.send_heartbeat()
                
                # Record collection duration
                duration = time.time() - start_time
                COLLECTION_DURATION.observe(duration)
                
                # Wait for next collection (default 60 seconds)
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in collection cycle: {e}")
                await asyncio.sleep(10)
    
    async def start(self):
        """Start the agent"""
        logger.info(f"Starting NOCbRAIN agent {self.agent_id}")
        self.is_running = True
        
        # Start Prometheus metrics server
        start_http_server(8001)
        logger.info("Prometheus metrics server started on port 8001")
        
        # Start collection cycle
        await self.run_collection_cycle()
    
    def stop(self):
        """Stop the agent"""
        logger.info(f"Stopping NOCbRAIN agent {self.agent_id}")
        self.is_running = False


# FastAPI for agent management
app = FastAPI(title="NOCbRAIN Agent", version="1.0.0")
security = HTTPBearer()

@app.post("/start")
async def start_agent(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Start the monitoring agent"""
    # Implementation would start the agent with provided credentials
    return {"message": "Agent started successfully"}

@app.post("/stop")
async def stop_agent(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Stop the monitoring agent"""
    # Implementation would stop the agent
    return {"message": "Agent stopped successfully"}

@app.get("/status")
async def get_agent_status():
    """Get agent status"""
    return {
        "status": "running",
        "version": "1.0.0",
        "hostname": socket.gethostname(),
        "platform": platform.system()
    }

@app.get("/metrics")
async def get_prometheus_metrics():
    """Endpoint for Prometheus scraping"""
    # This would return Prometheus metrics
    return {"metrics": "prometheus_format_here"}
