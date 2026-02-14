#!/usr/bin/env python3
"""
NOCbRAIN Monitoring Agent
Real-time network and system monitoring with AI analysis
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
import psutil
import socket
import requests
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]

@dataclass
class NetworkMetrics:
    """Network metrics data structure"""
    timestamp: str
    host: str
    ping_time: float
    port_status: Dict[str, bool]
    bandwidth_usage: Dict[str, float]
    connection_count: int

class MonitoringAgent:
    """Main monitoring agent class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_endpoint = config.get('api_endpoint', 'http://localhost:8000/api/v1')
        self.agent_id = config.get('agent_id', 'agent-001')
        self.monitoring_interval = config.get('interval', 30)
        self.targets = config.get('targets', [])
        self.running = False
        
        logger.info(f"Monitoring Agent {self.agent_id} initialized")
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Linux only)
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]
            
            return SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    async def collect_network_metrics(self, target: str) -> NetworkMetrics:
        """Collect network metrics for a target"""
        try:
            # Ping test
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            try:
                sock.connect((target, 80))
                ping_time = (time.time() - start_time) * 1000
                sock.close()
            except:
                ping_time = -1
            
            # Port scanning
            common_ports = [22, 80, 443, 3306, 5432, 6379, 8000, 8080]
            port_status = {}
            
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((target, port))
                    port_status[str(port)] = result == 0
                    sock.close()
                except:
                    port_status[str(port)] = False
            
            # Connection count
            try:
                connections = len(psutil.net_connections())
            except:
                connections = 0
            
            return NetworkMetrics(
                timestamp=datetime.utcnow().isoformat(),
                host=target,
                ping_time=ping_time,
                port_status=port_status,
                bandwidth_usage={},  # Would need SNMP for real bandwidth
                connection_count=connections
            )
            
        except Exception as e:
            logger.error(f"Error collecting network metrics for {target}: {e}")
            return None
    
    async def analyze_with_ai(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metrics with AI (simplified version)"""
        try:
            # Simple rule-based analysis (in real version, would call AI API)
            analysis = {
                'anomalies': [],
                'recommendations': [],
                'severity': 'normal'
            }
            
            # CPU analysis
            if metrics.get('cpu_percent', 0) > 80:
                analysis['anomalies'].append('High CPU usage detected')
                analysis['recommendations'].append('Check for runaway processes')
                analysis['severity'] = 'warning'
            
            # Memory analysis
            if metrics.get('memory_percent', 0) > 85:
                analysis['anomalies'].append('High memory usage detected')
                analysis['recommendations'].append('Check for memory leaks')
                analysis['severity'] = 'warning'
            
            # Disk analysis
            if metrics.get('disk_usage', 0) > 90:
                analysis['anomalies'].append('Low disk space')
                analysis['recommendations'].append('Clean up old logs and temporary files')
                analysis['severity'] = 'critical'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {'anomalies': [], 'recommendations': [], 'severity': 'unknown'}
    
    async def send_to_api(self, data: Dict[str, Any]) -> bool:
        """Send monitoring data to central API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Agent-ID': self.agent_id
            }
            
            response = requests.post(
                f"{self.api_endpoint}/monitoring/metrics",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Successfully sent metrics to API")
                return True
            else:
                logger.warning(f"API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending data to API: {e}")
            return False
    
    async def monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Starting monitoring loop")
        
        while self.running:
            try:
                # Collect system metrics
                system_metrics = await self.collect_system_metrics()
                if system_metrics:
                    system_data = {
                        'agent_id': self.agent_id,
                        'type': 'system',
                        'metrics': system_metrics.__dict__,
                        'timestamp': system_metrics.timestamp
                    }
                    
                    # Analyze with AI
                    analysis = await self.analyze_with_ai(system_metrics.__dict__)
                    system_data['analysis'] = analysis
                    
                    # Send to API
                    await self.send_to_api(system_data)
                
                # Collect network metrics for each target
                for target in self.targets:
                    network_metrics = await self.collect_network_metrics(target)
                    if network_metrics:
                        network_data = {
                            'agent_id': self.agent_id,
                            'type': 'network',
                            'target': target,
                            'metrics': network_metrics.__dict__,
                            'timestamp': network_metrics.timestamp
                        }
                        
                        # Analyze with AI
                        analysis = await self.analyze_with_ai(network_metrics.__dict__)
                        network_data['analysis'] = analysis
                        
                        # Send to API
                        await self.send_to_api(network_data)
                
                # Wait for next interval
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the monitoring agent"""
        self.running = True
        logger.info(f"Starting monitoring agent {self.agent_id}")
        
        try:
            await self.monitoring_loop()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.running = False
            logger.info("Monitoring agent stopped")
    
    def stop(self):
        """Stop the monitoring agent"""
        self.running = False
        logger.info("Stopping monitoring agent")

async def main():
    """Main function to run the monitoring agent"""
    # Load configuration
    config = {
        'agent_id': 'monitoring-agent-001',
        'api_endpoint': 'http://localhost:8000/api/v1',
        'interval': 30,
        'targets': ['localhost', '8.8.8.8', '1.1.1.1']
    }
    
    # Create and start agent
    agent = MonitoringAgent(config)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\nShutting down monitoring agent...")
        agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
