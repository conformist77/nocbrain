"""
NOCbRAIN SSH Protocol Handler
Handles SSH communication with servers and Proxmox integration
"""

import asyncio
import paramiko
import json
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SSHConnection:
    """SSH connection configuration"""
    host: str
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    port: int = 22
    timeout: int = 10
    connection_type: str = "linux"  # linux, proxmox, cisco
    sudo_password: Optional[str] = None
    
    def __post_init__(self):
        if not self.password and not self.private_key_path:
            raise ValueError("Either password or private_key_path must be provided")


class SSHHandler:
    """Main SSH protocol handler"""
    
    def __init__(self):
        self.active_connections: Dict[str, paramiko.SSHClient] = {}
        self.connection_configs: Dict[str, SSHConnection] = {}
        self.collection_stats = {
            "total_connections": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0
        }
        
        logger.info("SSH Handler initialized")
    
    async def add_connection(self, connection: SSHConnection) -> Dict[str, Any]:
        """Add a new SSH connection"""
        try:
            # Test connection
            test_result = await self.test_connection(connection)
            
            if test_result["status"] == "success":
                self.connection_configs[connection.host] = connection
                logger.info(f"Added SSH connection: {connection.host}")
                return {
                    "status": "success",
                    "host": connection.host,
                    "connection_type": connection.connection_type,
                    "test_result": test_result
                }
            else:
                logger.error(f"Failed to connect to {connection.host}: {test_result['error']}")
                return {
                    "status": "error",
                    "host": connection.host,
                    "error": test_result["error"]
                }
                
        except Exception as e:
            logger.error(f"Failed to add SSH connection {connection.host}: {e}")
            return {
                "status": "error",
                "host": connection.host,
                "error": str(e)
            }
    
    async def remove_connection(self, host: str) -> Dict[str, Any]:
        """Remove SSH connection"""
        try:
            # Close existing connection if active
            if host in self.active_connections:
                self.active_connections[host].close()
                del self.active_connections[host]
            
            if host in self.connection_configs:
                del self.connection_configs[host]
                logger.info(f"Removed SSH connection: {host}")
                return {"status": "success", "host": host}
            else:
                return {"status": "error", "host": host, "error": "Connection not found"}
                
        except Exception as e:
            logger.error(f"Failed to remove SSH connection {host}: {e}")
            return {"status": "error", "host": host, "error": str(e)}
    
    async def test_connection(self, connection: SSHConnection) -> Dict[str, Any]:
        """Test SSH connectivity"""
        try:
            start_time = datetime.utcnow()
            
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect
            if connection.private_key_path:
                private_key = paramiko.RSAKey.from_private_key_file(
                    connection.private_key_path
                )
                ssh.connect(
                    hostname=connection.host,
                    username=connection.username,
                    pkey=private_key,
                    port=connection.port,
                    timeout=connection.timeout
                )
            else:
                ssh.connect(
                    hostname=connection.host,
                    username=connection.username,
                    password=connection.password,
                    port=connection.port,
                    timeout=connection.timeout
                )
            
            # Test command
            stdin, stdout, stderr = ssh.exec_command("echo 'SSH Connection Test'")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            ssh.close()
            
            if output == "SSH Connection Test":
                return {
                    "status": "success",
                    "response_time": response_time,
                    "connection_type": connection.connection_type
                }
            else:
                return {
                    "status": "error",
                    "error": f"Command failed: {error}",
                    "response_time": response_time
                }
                
        except Exception as e:
            logger.error(f"SSH connection test failed for {connection.host}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "host": connection.host
            }
    
    async def execute_command(self, host: str, command: str, use_sudo: bool = False) -> Dict[str, Any]:
        """Execute command via SSH"""
        try:
            if host not in self.connection_configs:
                return {
                    "status": "error",
                    "host": host,
                    "error": "Connection not found"
                }
            
            connection = self.connection_configs[host]
            start_time = datetime.utcnow()
            
            # Get or create SSH client
            ssh = await self._get_ssh_client(connection)
            
            # Prepare command
            full_command = command
            if use_sudo and connection.sudo_password:
                full_command = f"echo '{connection.sudo_password}' | sudo -S {command}"
            
            # Execute command
            stdin, stdout, stderr = ssh.exec_command(full_command)
            
            # Read output
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            exit_code = stdout.channel.recv_exit_status()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update stats
            self.collection_stats["total_commands"] += 1
            if exit_code == 0:
                self.collection_stats["successful_commands"] += 1
            else:
                self.collection_stats["failed_commands"] += 1
            
            return {
                "status": "success" if exit_code == 0 else "error",
                "host": host,
                "command": command,
                "output": output,
                "error": error,
                "exit_code": exit_code,
                "response_time": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute command on {host}: {e}")
            self.collection_stats["total_commands"] += 1
            self.collection_stats["failed_commands"] += 1
            return {
                "status": "error",
                "host": host,
                "command": command,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def collect_system_metrics(self, host: str) -> Dict[str, Any]:
        """Collect system metrics via SSH"""
        try:
            if host not in self.connection_configs:
                return {
                    "status": "error",
                    "host": host,
                    "error": "Connection not found"
                }
            
            connection = self.connection_configs[host]
            start_time = datetime.utcnow()
            
            # Define commands based on connection type
            if connection.connection_type == "proxmox":
                commands = self._get_proxmox_commands()
            elif connection.connection_type == "cisco":
                commands = self._get_cisco_commands()
            else:
                commands = self._get_linux_commands()
            
            # Execute all commands
            metrics = {}
            errors = []
            
            for metric_name, command in commands.items():
                try:
                    result = await self.execute_command(host, command["cmd"], command.get("sudo", False))
                    
                    if result["status"] == "success":
                        # Parse the output based on command type
                        parsed_value = self._parse_command_output(
                            result["output"], 
                            command.get("parser", "raw")
                        )
                        metrics[metric_name] = {
                            "value": parsed_value,
                            "raw_output": result["output"],
                            "timestamp": result["timestamp"]
                        }
                    else:
                        errors.append(f"{metric_name}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"{metric_name}: {str(e)}")
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "success",
                "host": host,
                "connection_type": connection.connection_type,
                "metrics": metrics,
                "errors": errors,
                "response_time": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics from {host}: {e}")
            return {
                "status": "error",
                "host": host,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def collect_proxmox_data(self, host: str) -> Dict[str, Any]:
        """Collect Proxmox-specific data"""
        try:
            if host not in self.connection_configs:
                return {"status": "error", "host": host, "error": "Connection not found"}
            
            connection = self.connection_configs[host]
            
            if connection.connection_type != "proxmox":
                return {"status": "error", "host": host, "error": "Not a Proxmox connection"}
            
            # Proxmox-specific commands
            proxmox_commands = {
                "vms": {
                    "cmd": "qm list",
                    "parser": "qm_list"
                },
                "containers": {
                    "cmd": "pct list",
                    "parser": "pct_list"
                },
                "nodes": {
                    "cmd": "pvesh get /nodes",
                    "parser": "json"
                },
                "storage": {
                    "cmd": "pvesh get /storage",
                    "parser": "json"
                },
                "cluster_status": {
                    "cmd": "pvecm status",
                    "parser": "pvecm_status"
                }
            }
            
            data = {}
            errors = []
            
            for data_type, command_config in proxmox_commands.items():
                try:
                    result = await self.execute_command(host, command_config["cmd"])
                    
                    if result["status"] == "success":
                        parsed_data = self._parse_command_output(
                            result["output"],
                            command_config["parser"]
                        )
                        data[data_type] = parsed_data
                    else:
                        errors.append(f"{data_type}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"{data_type}: {str(e)}")
            
            return {
                "status": "success",
                "host": host,
                "data": data,
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect Proxmox data from {host}: {e}")
            return {
                "status": "error",
                "host": host,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_ssh_client(self, connection: SSHConnection) -> paramiko.SSHClient:
        """Get or create SSH client"""
        if connection.host in self.active_connections:
            return self.active_connections[connection.host]
        
        # Create new connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if connection.private_key_path:
            private_key = paramiko.RSAKey.from_private_key_file(
                connection.private_key_path
            )
            ssh.connect(
                hostname=connection.host,
                username=connection.username,
                pkey=private_key,
                port=connection.port,
                timeout=connection.timeout
            )
        else:
            ssh.connect(
                hostname=connection.host,
                username=connection.username,
                password=connection.password,
                port=connection.port,
                timeout=connection.timeout
            )
        
        self.active_connections[connection.host] = ssh
        self.collection_stats["total_connections"] += 1
        self.collection_stats["successful_connections"] += 1
        
        return ssh
    
    def _get_linux_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get Linux system monitoring commands"""
        return {
            "uptime": {
                "cmd": "uptime",
                "parser": "uptime"
            },
            "cpu_usage": {
                "cmd": "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1",
                "parser": "float"
            },
            "memory_usage": {
                "cmd": "free -m | grep 'Mem:' | awk '{print $3/$2 * 100.0}'",
                "parser": "float"
            },
            "disk_usage": {
                "cmd": "df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1",
                "parser": "float"
            },
            "load_average": {
                "cmd": "cat /proc/loadavg | awk '{print $1\" \"$2\" \"$3}'",
                "parser": "load_avg"
            },
            "process_count": {
                "cmd": "ps aux | wc -l",
                "parser": "int"
            },
            "network_connections": {
                "cmd": "netstat -an | grep ESTABLISHED | wc -l",
                "parser": "int"
            }
        }
    
    def _get_proxmox_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get Proxmox monitoring commands"""
        return {
            "node_status": {
                "cmd": "pvesh get /nodes/localhost/status",
                "parser": "json"
            },
            "vm_count": {
                "cmd": "qm list | wc -l",
                "parser": "int"
            },
            "container_count": {
                "cmd": "pct list | wc -l",
                "parser": "int"
            },
            "storage_usage": {
                "cmd": "pvesh get /storage/local/status",
                "parser": "json"
            },
            "cluster_status": {
                "cmd": "pvecm status",
                "parser": "pvecm_status"
            }
        }
    
    def _get_cisco_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get Cisco IOS commands"""
        return {
            "version": {
                "cmd": "show version",
                "parser": "cisco_version"
            },
            "interfaces": {
                "cmd": "show ip interface brief",
                "parser": "cisco_interfaces"
            },
            "cpu_usage": {
                "cmd": "show processes cpu sorted | include CPU",
                "parser": "cisco_cpu"
            },
            "memory": {
                "cmd": "show memory statistics",
                "parser": "cisco_memory"
            },
            "running_config": {
                "cmd": "show running-config",
                "parser": "raw"
            }
        }
    
    def _parse_command_output(self, output: str, parser_type: str) -> Any:
        """Parse command output based on parser type"""
        try:
            if parser_type == "raw":
                return output
            elif parser_type == "float":
                return float(output.strip())
            elif parser_type == "int":
                return int(output.strip())
            elif parser_type == "json":
                return json.loads(output)
            elif parser_type == "uptime":
                # Parse uptime: "10:30:45 up 2 days, 3:45, 1 user, load average: 0.15, 0.25, 0.20"
                match = re.search(r'up (.+?), \d+ user', output)
                return match.group(1) if match else output
            elif parser_type == "load_avg":
                # Parse load average: "0.15 0.25 0.20"
                parts = output.strip().split()
                return [float(x) for x in parts[:3]]
            elif parser_type == "qm_list":
                # Parse QM list output
                lines = output.strip().split('\n')[1:]  # Skip header
                vms = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        vms.append({
                            "vmid": parts[0],
                            "name": parts[1],
                            "status": parts[2],
                            "cpu": parts[3],
                            "memory": parts[4],
                            "disk": parts[5]
                        })
                return vms
            elif parser_type == "pct_list":
                # Parse PCT list output
                lines = output.strip().split('\n')[1:]  # Skip header
                containers = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        containers.append({
                            "ctid": parts[0],
                            "name": parts[1],
                            "status": parts[2],
                            "cpu": parts[3],
                            "memory": parts[4],
                            "disk": parts[5]
                        })
                return containers
            elif parser_type == "pvecm_status":
                # Parse Proxmox cluster status
                lines = output.strip().split('\n')
                status = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        status[key.strip()] = value.strip()
                return status
            elif parser_type == "cisco_version":
                # Parse Cisco version output
                version_info = {}
                for line in output.split('\n'):
                    if "Cisco IOS Software" in line:
                        version_info["ios_version"] = line.strip()
                    elif "uptime is" in line:
                        version_info["uptime"] = line.split("uptime is")[1].strip()
                return version_info
            elif parser_type == "cisco_interfaces":
                # Parse Cisco interface brief
                interfaces = []
                lines = output.split('\n')[2:]  # Skip headers
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 6:
                            interfaces.append({
                                "interface": parts[0],
                                "ip_address": parts[1],
                                "status": parts[4],
                                "protocol": parts[5]
                            })
                return interfaces
            else:
                return output
                
        except Exception as e:
            logger.error(f"Failed to parse output with parser {parser_type}: {e}")
            return output
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get SSH handler statistics"""
        return {
            **self.collection_stats,
            "active_connections": len(self.active_connections),
            "configured_connections": len(self.connection_configs),
            "connection_list": list(self.connection_configs.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on SSH handler"""
        try:
            stats = await self.get_stats()
            
            # Check if we have any active connections
            if stats["configured_connections"] == 0:
                return {
                    "status": "warning",
                    "message": "No configured SSH connections",
                    "stats": stats
                }
            
            # Check connection success rate
            success_rate = (
                stats["successful_connections"] / stats["total_connections"] * 100
                if stats["total_connections"] > 0 else 100
            )
            
            if success_rate < 80:
                return {
                    "status": "warning",
                    "message": f"Low connection success rate: {success_rate:.1f}%",
                    "stats": stats
                }
            
            # Check command success rate
            command_success_rate = (
                stats["successful_commands"] / stats["total_commands"] * 100
                if stats["total_commands"] > 0 else 100
            )
            
            if command_success_rate < 80:
                return {
                    "status": "warning",
                    "message": f"Low command success rate: {command_success_rate:.1f}%",
                    "stats": stats
                }
            
            return {
                "status": "healthy",
                "message": "SSH handler operating normally",
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def close_all_connections(self):
        """Close all active SSH connections"""
        for host, ssh in self.active_connections.items():
            try:
                ssh.close()
                logger.info(f"Closed SSH connection: {host}")
            except Exception as e:
                logger.error(f"Failed to close SSH connection {host}: {e}")
        
        self.active_connections.clear()


# Global instance
ssh_handler = SSHHandler()
