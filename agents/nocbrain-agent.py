#!/usr/bin/env python3
"""
NOCbRAIN Monitoring Agent
Secure agent for collecting and sending metrics to NOCbRAIN server
Supports multiple platforms: Windows, Linux, macOS
"""
import asyncio
import json
import ssl
import sys
import os
import argparse
import platform
import socket
import time
import hashlib
import psutil
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet

# Configuration
DEFAULT_SERVER_URL = "https://api.nocbrain.com"
DEFAULT_COLLECTION_INTERVAL = 60
DEFAULT_API_KEY = None

class NOCBRAINAgent:
    """NOCbRAIN Monitoring Agent"""
    
    def __init__(self, config: Dict[str, Any]):
        self.server_url = config['server_url']
        self.api_key = config['api_key']
        self.agent_id = config['agent_id']
        self.collection_interval = config.get('collection_interval', DEFAULT_COLLECTION_INTERVAL)
        self.encryption_enabled = config.get('encryption_enabled', True)
        self.compression_enabled = config.get('compression_enabled', True)
        
        # Generate encryption key from API key
        if self.encryption_enabled:
            self.encryption_key = self._derive_encryption_key(self.api_key)
            self.cipher = Fernet(self.encryption_key)
        
        self.hostname = socket.gethostname()
        self.platform = platform.system()
        self.is_running = False
        self.session = requests.Session()
        
        # Setup session headers
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'NOCbRAIN-Agent/1.0.0 ({self.platform})'
        })
        
        # SSL context for HTTPS
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    def _derive_encryption_key(self, api_key: str) -> bytes:
        """Derive encryption key from API key"""
        return hashlib.sha256(api_key.encode()).digest()[:32]
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt monitoring data"""
        if not self.encryption_enabled:
            return json.dumps(data)
        
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
                except (PermissionError, OSError):
                    continue
            
            # Network metrics
            network_io = psutil.net_io_counters()
            network_connections = len(psutil.net_connections())
            
            # System load
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
            else:
                load_avg = [0, 0, 0]
            
            # Boot time and uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            
            # Process metrics
            process_count = len(psutil.pids())
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'hostname': self.hostname,
                'platform': self.platform,
                'system': {
                    'uptime': uptime,
                    'boot_time': boot_time,
                    'load_average': list(load_avg),
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
            
            return metrics
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
            return {}
    
    def _collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            app_metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'hostname': self.hostname,
                'applications': {
                    'nginx': self._get_nginx_stats(),
                    'apache': self._get_apache_stats(),
                    'mysql': self._get_mysql_stats(),
                    'postgresql': self._get_postgresql_stats(),
                    'redis': self._get_redis_stats(),
                    'docker': self._get_docker_stats()
                }
            }
            return app_metrics
        except Exception as e:
            print(f"Error collecting application metrics: {e}")
            return {}
    
    def _get_nginx_stats(self) -> Dict[str, Any]:
        """Collect Nginx statistics"""
        try:
            # Try to get stats from nginx stub_status
            response = self.session.get('http://localhost/nginx_status', timeout=5)
            if response.status_code == 200:
                # Parse nginx status page
                lines = response.text.split('\n')
                stats = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        stats[key.strip()] = value.strip()
                return stats
        except:
            pass
        return {}
    
    def _get_apache_stats(self) -> Dict[str, Any]:
        """Collect Apache statistics"""
        try:
            # Try to get stats from Apache server-status
            response = self.session.get('http://localhost/server-status?auto', timeout=5)
            if response.status_code == 200:
                # Parse Apache status
                stats = {}
                for line in response.text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        stats[key.strip()] = value.strip()
                return stats
        except:
            pass
        return {}
    
    def _get_mysql_stats(self) -> Dict[str, Any]:
        """Collect MySQL statistics"""
        try:
            # This would connect to MySQL and query status
            # Implementation depends on MySQL client library
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
            # This would connect to PostgreSQL and query pg_stat_activity
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
            # This would connect to Redis and query INFO
            return {
                'connected_clients': 0,
                'used_memory': 0,
                'total_commands_processed': 0,
                'keyspace_hits': 0,
                'keyspace_misses': 0
            }
        except:
            return {}
    
    def _get_docker_stats(self) -> Dict[str, Any]:
        """Collect Docker statistics"""
        try:
            # This would use Docker API to get container stats
            return {
                'running_containers': 0,
                'total_containers': 0,
                'cpu_usage': 0,
                'memory_usage': 0
            }
        except:
            return {}
    
    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send metrics to server"""
        try:
            encrypted_data = self._encrypt_data(metrics)
            
            payload = {
                'data': encrypted_data,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{self.server_url}/api/v1/monitoring/metrics",
                json=payload,
                timeout=30,
                verify=self.ssl_context
            )
            
            if response.status_code == 200:
                print(f"Metrics sent successfully for agent {self.agent_id}")
                return True
            else:
                print(f"Failed to send metrics: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending metrics: {e}")
            return False
    
    def send_heartbeat(self) -> bool:
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
            
            response = self.session.post(
                f"{self.server_url}/api/v1/monitoring/heartbeat",
                json=heartbeat_data,
                timeout=10,
                verify=self.ssl_context
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Failed to send heartbeat: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error sending heartbeat: {e}")
            return False
    
    async def run_collection_cycle(self):
        """Main collection cycle"""
        print(f"Starting NOCbRAIN agent {self.agent_id}")
        print(f"Server: {self.server_url}")
        print(f"Collection interval: {self.collection_interval} seconds")
        print(f"Platform: {self.platform}")
        
        self.is_running = True
        
        # Send initial heartbeat
        self.send_heartbeat()
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                if system_metrics:
                    self.send_metrics(system_metrics)
                
                # Collect application metrics
                app_metrics = self._collect_application_metrics()
                if app_metrics:
                    self.send_metrics(app_metrics)
                
                # Send heartbeat
                self.send_heartbeat()
                
                # Calculate sleep time
                collection_time = time.time() - start_time
                sleep_time = max(0, self.collection_interval - collection_time)
                
                print(f"Collection cycle completed in {collection_time:.2f}s, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                
            except KeyboardInterrupt:
                print("\nShutting down agent...")
                self.is_running = False
                break
            except Exception as e:
                print(f"Error in collection cycle: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the agent"""
        print(f"Stopping NOCbRAIN agent {self.agent_id}")
        self.is_running = False


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in configuration file: {e}")
        return {}


def save_config(config: Dict[str, Any], config_file: str):
    """Save configuration to file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {config_file}")
    except Exception as e:
        print(f"Error saving configuration: {e}")


def main():
    parser = argparse.ArgumentParser(description='NOCbRAIN Monitoring Agent')
    parser.add_argument('--server-url', default=DEFAULT_SERVER_URL,
                       help='NOCbRAIN server URL')
    parser.add_argument('--api-key', required=True,
                       help='API key for authentication')
    parser.add_argument('--agent-id', required=True,
                       help='Unique agent ID')
    parser.add_argument('--config', default='agent-config.json',
                       help='Configuration file path')
    parser.add_argument('--collection-interval', type=int, default=DEFAULT_COLLECTION_INTERVAL,
                       help='Metrics collection interval in seconds')
    parser.add_argument('--no-encryption', action='store_true',
                       help='Disable encryption')
    parser.add_argument('--no-compression', action='store_true',
                       help='Disable compression')
    parser.add_argument('--setup', action='store_true',
                       help='Setup agent configuration')
    
    args = parser.parse_args()
    
    # Load existing configuration
    config = load_config(args.config)
    
    # Update configuration with command line arguments
    config.update({
        'server_url': args.server_url,
        'api_key': args.api_key,
        'agent_id': args.agent_id,
        'collection_interval': args.collection_interval,
        'encryption_enabled': not args.no_encryption,
        'compression_enabled': not args.no_compression
    })
    
    # Save configuration
    save_config(config, args.config)
    
    if args.setup:
        print("Agent setup completed. Run without --setup to start monitoring.")
        return
    
    # Create and start agent
    agent = NOCBRAINAgent(config)
    
    try:
        asyncio.run(agent.run_collection_cycle())
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
    except Exception as e:
        print(f"Agent error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
