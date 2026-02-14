#!/usr/bin/env python3
"""
NOCbRAIN Global Knowledge Seeding Script
Downloads and generates high-quality networking knowledge for global tenant
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
import json

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.core.logic.knowledge_manager import knowledge_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


class GlobalKnowledgeSeeder:
    """Seeder for global knowledge base"""
    
    def __init__(self):
        self.knowledge_base_path = Path(__file__).parent.parent / "knowledge-base"
        self.global_tenant_id = "global"
        
        # Ensure directories exist
        self.knowledge_base_path.mkdir(exist_ok=True)
        (self.knowledge_base_path / "network").mkdir(exist_ok=True)
        (self.knowledge_base_path / "infrastructure").mkdir(exist_ok=True)
        (self.knowledge_base_path / "security").mkdir(exist_ok=True)
        (self.knowledge_base_path / "applications").mkdir(exist_ok=True)
        
        logger.info("Global Knowledge Seeder initialized")
    
    async def seed_cisco_knowledge(self):
        """Seed Cisco IOS troubleshooting guides"""
        logger.info("Seeding Cisco IOS knowledge...")
        
        cisco_content = """# Cisco IOS Troubleshooting Guide

## VLAN Configuration Issues

### Symptoms
- VLANs not communicating
- Trunk ports not working
- VLAN membership issues

### Step-by-Step Resolution

1. **Verify VLAN Configuration**
   ```bash
   show vlan brief
   show running-config | include vlan
   ```
   
2. **Check Trunk Configuration**
   ```bash
   show interfaces trunk
   show running-config interface GigabitEthernet0/1
   ```
   
3. **Verify Native VLAN**
   ```bash
   show spanning-tree vlan 1
   ```
   
4. **Fix Common Issues**
   - Ensure matching native VLAN on both ends
   - Check allowed VLAN list on trunk
   - Verify VLAN database consistency
   
5. **Test Connectivity**
   ```bash
   ping 192.168.1.1
   show mac address-table
   ```

### Prevention Measures
- Document VLAN assignments
- Use consistent naming conventions
- Implement VLAN access control lists

## OSPF Troubleshooting

### Symptoms
- OSPF neighbors not forming
- Routes not being advertised
- Routing loops

### Step-by-Step Resolution

1. **Check OSPF Configuration**
   ```bash
   show running-config | section router ospf
   show ip ospf interface brief
   ```
   
2. **Verify Neighbor Status**
   ```bash
   show ip ospf neighbor
   show ip ospf neighbor detail
   ```
   
3. **Check Network Statements**
   ```bash
   show ip ospf database
   show ip route ospf
   ```
   
4. **Debug OSPF Issues**
   ```bash
   debug ip ospf hello
   debug ip ospf adjacency
   ```
   
5. **Common Fixes**
   - Match area IDs
   - Check subnet masks
   - Verify passive interfaces
   
### Prevention Measures
- Regular OSPF health checks
- Monitor neighbor relationships
- Document OSPF design

## Interface Issues

### Symptoms
- Interface down
- High error rates
- Performance problems

### Step-by-Step Resolution

1. **Check Interface Status**
   ```bash
   show interfaces status
   show interfaces GigabitEthernet0/1
   ```
   
2. **Verify Physical Layer**
   ```bash
   show controllers GigabitEthernet0/1
   ```
   
3. **Check Configuration**
   ```bash
   show running-config interface GigabitEthernet0/1
   ```
   
4. **Reset Interface**
   ```bash
   shutdown
   no shutdown
   ```
   
### Prevention Measures
- Regular interface monitoring
- Cable management
- Environmental monitoring
"""
        
        # Save Cisco knowledge
        cisco_file = self.knowledge_base_path / "network" / "cisco-ios-troubleshooting.md"
        with open(cisco_file, 'w', encoding='utf-8') as f:
            f.write(cisco_content)
        
        logger.info(f"Created Cisco knowledge file: {cisco_file}")
        
        # Index the file
        result = await knowledge_manager.index_file(cisco_file, self.global_tenant_id)
        logger.info(f"Indexed Cisco knowledge: {result['chunks']} chunks")
        
        return result
    
    async def seed_proxmox_knowledge(self):
        """Seed Proxmox troubleshooting guides"""
        logger.info("Seeding Proxmox knowledge...")
        
        proxmox_content = """# Proxmox Troubleshooting Guide

## Common API Errors

### Symptoms
- API connection timeouts
- Authentication failures
- Permission denied errors

### Step-by-Step Resolution

1. **Check API Service Status**
   ```bash
   systemctl status pveproxy
   systemctl restart pveproxy
   ```
   
2. **Verify API Configuration**
   ```bash
   cat /etc/pve/pveproxy.cfg
   cat /etc/pve/local/pve-ssl.pem
   ```
   
3. **Check Network Connectivity**
   ```bash
   netstat -tlnp | grep 8006
   curl -k https://localhost:8006/version
   ```
   
4. **Debug Authentication**
   ```bash
   pveum user list
   pveum group list
   pveum acl list / -user root@pam
   ```
   
5. **Common Fixes**
   - Restart pveproxy service
   - Check SSL certificates
   - Verify user permissions
   
### Prevention Measures
- Regular API health checks
- SSL certificate monitoring
- User access audits

## Storage Recovery (ZFS)

### Symptoms
- ZFS pool degraded
- Storage performance issues
- Disk failures

### Step-by-Step Resolution

1. **Check Pool Status**
   ```bash
   zpool status
   zpool list
   ```
   
2. **Identify Failed Disks**
   ```bash
   zpool status -x
   zpool scrub pool_name
   ```
   
3. **Replace Failed Disk**
   ```bash
   zpool offline pool_name failed_disk
   zpool replace pool_name failed_disk new_disk
   ```
   
4. **Verify Recovery**
   ```bash
   zpool status
   zpool scrub pool_name
   ```
   
5. **Performance Optimization**
   ```bash
   zfs set compression=lz4 pool_name
   zfs set recordsize=128k pool_name
   ```
   
### Prevention Measures
- Regular scrubbing
- Monitor SMART status
- Hot spares configuration

## Storage Recovery (LVM)

### Symptoms
- LVM volume corruption
- Disk space issues
- Performance problems

### Step-by-Step Resolution

1. **Check LVM Status**
   ```bash
   vgdisplay
   lvdisplay
   pvdisplay
   ```
   
2. **Repair Volume Groups**
   ```bash
   vgcfgrestore --test --vgname vg_name /etc/lvm/backup/vg_name
   vgcfgrestore --vgname vg_name /etc/lvm/backup/vg_name
   ```
   
3. **Extend Logical Volumes**
   ```bash
   lvextend -L +10G /dev/vg_name/lv_name
   resize2fs /dev/vg_name/lv_name
   ```
   
4. **Check Filesystem**
   ```bash
   fsck -f /dev/vg_name/lv_name
   ```
   
### Prevention Measures
- Regular LVM backups
- Monitor disk usage
- Document LVM structure

## VM Issues

### Symptoms
- VM won't start
- Performance problems
- Network connectivity issues

### Step-by-Step Resolution

1. **Check VM Status**
   ```bash
   qm status 100
   qm config 100
   ```
   
2. **Debug VM Startup**
   ```bash
   qm start 100
   qm monitor 100
   ```
   
3. **Check Resources**
   ```bash
   free -h
   df -h
   cat /proc/loadavg
   ```
   
4. **Network Troubleshooting**
   ```bash
   cat /etc/pve/qemu-server/100.conf
   brctl show
   ```
   
5. **Common Fixes**
   - Check resource allocation
   - Verify network bridges
   - Review VM configuration
   
### Prevention Measures
- Resource monitoring
- Regular backups
- Performance tuning
"""
        
        # Save Proxmox knowledge
        proxmox_file = self.knowledge_base_path / "infrastructure" / "proxmox-troubleshooting.md"
        with open(proxmox_file, 'w', encoding='utf-8') as f:
            f.write(proxmox_content)
        
        logger.info(f"Created Proxmox knowledge file: {proxmox_file}")
        
        # Index the file
        result = await knowledge_manager.index_file(proxmox_file, self.global_tenant_id)
        logger.info(f"Indexed Proxmox knowledge: {result['chunks']} chunks")
        
        return result
    
    async def seed_zabbix_knowledge(self):
        """Seed Zabbix performance tuning guides"""
        logger.info("Seeding Zabbix knowledge...")
        
        zabbix_content = """# Zabbix Performance Tuning Guide

## Large Environment Optimization

### Symptoms
- High server load
- Slow dashboard loading
- Database performance issues
- Queue buildup

### Step-by-Step Resolution

1. **Database Optimization**
   ```sql
   -- Check table sizes
   SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "Size in MB" 
   FROM information_schema.tables 
   WHERE table_schema = "zabbix" 
   ORDER BY (data_length + index_length) DESC;
   
   -- Optimize tables
   OPTIMIZE TABLE history;
   OPTIMIZE TABLE trends;
   ```
   
2. **Zabbix Server Configuration**
   ```bash
   # Edit /etc/zabbix/zabbix_server.conf
   StartPollers=50
   StartPingers=10
   StartTrappers=30
   StartDiscoverers=5
   CacheSize=1G
   HistoryCacheSize=512M
   TrendCacheSize=256M
   ValueCacheSize=256M
   ```
   
3. **Frontend Optimization**
   ```bash
   # Edit /etc/zabbix/web/zabbix.conf.php
   $DB['HISTORY'] = 'history_uint';
   $DB['TRENDS'] = 'trends_uint';
   ```
   
4. **Housekeeping Settings**
   ```bash
   # Configure housekeeping
   HousekeepingFrequency=1
   MaxHistoryPeriod=90d
   MaxTrendsPeriod=365d
   ```
   
5. **Monitoring Performance**
   ```bash
   # Check Zabbix server status
   zabbix_server -R status
   
   # Monitor queue
   zabbix_server -R queue
   ```
   
### Prevention Measures
- Regular performance monitoring
- Database maintenance
- Capacity planning

## Database Partitioning

### Symptoms
- Large history tables
- Slow queries
- Disk space issues

### Step-by-Step Resolution

1. **Partition History Tables**
   ```sql
   -- Create partitioned history table
   CREATE TABLE history_partitioned (
       itemid BIGINT UNSIGNED NOT NULL,
       clock INTEGER NOT NULL DEFAULT 0,
       value DOUBLE NOT NULL DEFAULT 0.0000,
       ns INTEGER NOT NULL DEFAULT 0,
       PRIMARY KEY (itemid, clock)
   ) PARTITION BY RANGE (clock);
   
   -- Create partitions
   CREATE TABLE history_p202401 PARTITION OF history_partitioned
       FOR VALUES FROM (UNIX_TIMESTAMP('2024-01-01')) TO (UNIX_TIMESTAMP('2024-02-01'));
   ```
   
2. **Automate Partition Management**
   ```bash
   # Create partition management script
   #!/bin/bash
   # Add new partitions for next month
   ```
   
3. **Migrate Data**
   ```sql
   -- Migrate existing data
   INSERT INTO history_partitioned SELECT * FROM history;
   ```
   
### Prevention Measures
- Automated partition creation
- Regular partition cleanup
- Monitor partition sizes

## Proxy Configuration

### Symptoms
- Proxy connection issues
- Data collection delays
- Performance bottlenecks

### Step-by-Step Resolution

1. **Proxy Configuration**
   ```bash
   # Edit /etc/zabbix/zabbix_proxy.conf
   Server=zabbix_server_ip
   Hostname=proxy_name
   ProxyMode=0
   ProxyLocalBuffer=72
   ProxyOfflineBuffer=1
   ```
   
2. **Network Optimization**
   ```bash
   # Check connectivity
   telnet zabbix_server_ip 10051
   
   # Monitor proxy status
   zabbix_proxy -R status
   ```
   
3. **Performance Tuning**
   ```bash
   # Adjust proxy settings
   StartPollers=20
   CacheSize=256M
   ```
   
### Prevention Measures
- Regular proxy monitoring
- Network health checks
- Performance baseline

## Troubleshooting Common Issues

### Symptoms
- Items not collecting data
- Triggers not firing
- Graphs not updating

### Step-by-Step Resolution

1. **Check Item Status**
   ```bash
   # Use Zabbix API or frontend
   # Check last value, error message
   ```
   
2. **Debug Item Collection**
   ```bash
   # Test item manually
   zabbix_get -s target_host -k item_key
   ```
   
3. **Check Permissions**
   ```bash
   # Verify Zabbix agent permissions
   sudo -u zabbix zabbix_get -s localhost -k agent.ping
   ```
   
4. **Monitor Logs**
   ```bash
   # Check Zabbix server logs
   tail -f /var/log/zabbix/zabbix_server.log
   
   # Check agent logs
   tail -f /var/log/zabbix/zabbix_agentd.log
   ```
   
### Prevention Measures
- Regular item monitoring
- Log analysis
- Performance baseline
"""
        
        # Save Zabbix knowledge
        zabbix_file = self.knowledge_base_path / "applications" / "zabbix-performance-tuning.md"
        with open(zabbix_file, 'w', encoding='utf-8') as f:
            f.write(zabbix_content)
        
        logger.info(f"Created Zabbix knowledge file: {zabbix_file}")
        
        # Index the file
        result = await knowledge_manager.index_file(zabbix_file, self.global_tenant_id)
        logger.info(f"Indexed Zabbix knowledge: {result['chunks']} chunks")
        
        return result
    
    async def seed_kubernetes_knowledge(self):
        """Seed Kubernetes troubleshooting guides"""
        logger.info("Seeding Kubernetes knowledge...")
        
        k8s_content = """# Kubernetes Troubleshooting Guide

## CrashLoopBackOff Issues

### Symptoms
- Pod status: CrashLoopBackOff
- Container keeps restarting
- Application not starting

### Step-by-Step Resolution

1. **Check Pod Status**
   ```bash
   kubectl get pods -o wide
   kubectl describe pod pod_name
   ```
   
2. **Check Pod Logs**
   ```bash
   kubectl logs pod_name
   kubectl logs pod_name --previous
   ```
   
3. **Check Events**
   ```bash
   kubectl get events --sort-by=.metadata.creationTimestamp
   kubectl describe pod pod_name | grep -A 20 Events:
   ```
   
4. **Debug Container**
   ```bash
   kubectl exec -it pod_name -- /bin/bash
   kubectl debug pod_name --image=busybox
   ```
   
5. **Common Fixes**
   - Resource limits too low
   - Application errors
   - Configuration issues
   - Image pull problems
   
### Prevention Measures
- Resource monitoring
- Health checks
- Proper resource requests/limits

## Pending Pods

### Symptoms
- Pod status: Pending
- Pod not scheduling
- Resource allocation issues

### Step-by-Step Resolution

1. **Check Pod Status**
   ```bash
   kubectl get pods -o wide
   kubectl describe pod pod_name
   ```
   
2. **Check Resource Usage**
   ```bash
   kubectl top nodes
   kubectl describe nodes
   ```
   
3. **Check Events**
   ```bash
   kubectl get events --field-selector type=Warning
   ```
   
4. **Debug Scheduling**
   ```bash
   kubectl get pods -o jsonpath='{.items[*].status.conditions[?(@.type=="PodScheduled")]}'
   ```
   
5. **Common Fixes**
   - Insufficient resources
   - Taints and tolerations
   - Node affinity/anti-affinity
   - Resource quotas
   
### Prevention Measures
- Capacity planning
- Resource monitoring
- Proper node sizing

## Network Issues

### Symptoms
- Service connectivity problems
- DNS resolution failures
- Network policies blocking traffic

### Step-by-Step Resolution

1. **Check Service Status**
   ```bash
   kubectl get services
   kubectl describe service service_name
   ```
   
2. **Test Connectivity**
   ```bash
   kubectl exec -it pod_name -- nslookup service_name
   kubectl exec -it pod_name -- curl service_name
   ```
   
3. **Check Network Policies**
   ```bash
   kubectl get networkpolicies
   kubectl describe networkpolicy policy_name
   ```
   
4. **Debug DNS**
   ```bash
   kubectl exec -it pod_name -- nslookup kubernetes.default
   kubectl logs -n kube-system -l k8s-app=kube-dns
   ```
   
5. **Common Fixes**
   - Service configuration
   - Network policies
   - DNS configuration
   - CNI issues
   
### Prevention Measures
- Network monitoring
- DNS health checks
- Policy testing

## Storage Issues

### Symptoms
- PVC pending
- Pod can't mount volumes
- Storage performance issues

### Step-by-Step Resolution

1. **Check PVC Status**
   ```bash
   kubectl get pvc
   kubectl describe pvc pvc_name
   ```
   
2. **Check Storage Classes**
   ```bash
   kubectl get storageclass
   kubectl describe storageclass class_name
   ```
   
3. **Check PV Status**
   ```bash
   kubectl get pv
   kubectl describe pv pv_name
   ```
   
4. **Debug Mount Issues**
   ```bash
   kubectl exec -it pod_name -- df -h
   kubectl exec -it pod_name -- mount | grep volume
   ```
   
5. **Common Fixes**
   - Storage class configuration
   - Resource quotas
   - Access modes
   - Provisioner issues
   
### Prevention Measures
- Storage monitoring
- Capacity planning
- Backup strategies

## Performance Issues

### Symptoms
- High resource usage
- Slow response times
- Cluster performance degradation

### Step-by-Step Resolution

1. **Resource Monitoring**
   ```bash
   kubectl top nodes
   kubectl top pods
   ```
   
2. **Performance Analysis**
   ```bash
   kubectl describe node node_name
   kubectl describe pod pod_name
   ```
   
3. **Check Limits**
   ```bash
   kubectl describe pod pod_name | grep -A 10 Limits:
   ```
   
4. **Optimization**
   ```bash
   # Adjust resource requests/limits
   kubectl patch deployment deployment_name -p '{"spec":{"template":{"spec":{"containers":[{"name":"container_name","resources":{"requests":{"cpu":"500m","memory":"512Mi"}}}]}}}}'
   ```
   
5. **Common Fixes**
   - Resource optimization
   - Horizontal scaling
   - Vertical scaling
   - Cluster scaling
   
### Prevention Measures
- Performance monitoring
- Resource planning
- Autoscaling configuration
"""
        
        # Save Kubernetes knowledge
        k8s_file = self.knowledge_base_path / "infrastructure" / "kubernetes-troubleshooting.md"
        with open(k8s_file, 'w', encoding='utf-8') as f:
            f.write(k8s_content)
        
        logger.info(f"Created Kubernetes knowledge file: {k8s_file}")
        
        # Index the file
        result = await knowledge_manager.index_file(k8s_file, self.global_tenant_id)
        logger.info(f"Indexed Kubernetes knowledge: {result['chunks']} chunks")
        
        return result
    
    async def seed_security_knowledge(self):
        """Seed security best practices"""
        logger.info("Seeding security knowledge...")
        
        security_content = """# Network Security Best Practices

## Incident Response Procedures

### Initial Response
1. **Containment**
   - Isolate affected systems
   - Block malicious IPs
   - Disable compromised accounts
   
2. **Assessment**
   - Determine scope of incident
   - Identify affected systems
   - Assess data impact
   
3. **Investigation**
   - Collect evidence
   - Analyze logs
   - Identify root cause
   
4. **Recovery**
   - Restore systems
   - Patch vulnerabilities
   - Monitor for recurrence

### Documentation
- Timeline of events
- Actions taken
- Lessons learned
- Prevention measures

## Threat Detection

### Common Indicators
- Unusual login patterns
- Data exfiltration attempts
- Network anomalies
- System performance issues

### Monitoring Tools
- SIEM systems
- Network monitoring
- Log analysis
- Threat intelligence

### Response Automation
- Automated blocking
- Alert escalation
- Incident ticketing
- Reporting workflows

## Security Hardening

### Network Security
- Firewall configuration
- Network segmentation
- Access control lists
- VPN implementation

### System Security
- Patch management
- Configuration hardening
- Access control
- Audit logging

### Application Security
- Code review
- Security testing
- Vulnerability scanning
- Secure coding practices
"""
        
        # Save security knowledge
        security_file = self.knowledge_base_path / "security" / "security-best-practices.md"
        with open(security_file, 'w', encoding='utf-8') as f:
            f.write(security_content)
        
        logger.info(f"Created security knowledge file: {security_file}")
        
        # Index the file
        result = await knowledge_manager.index_file(security_file, self.global_tenant_id)
        logger.info(f"Indexed security knowledge: {result['chunks']} chunks")
        
        return result
    
    async def seed_all_knowledge(self):
        """Seed all global knowledge"""
        logger.info("Starting global knowledge seeding...")
        
        try:
            # Initialize global collection
            await knowledge_manager.initialize_collection(self.global_tenant_id)
            
            # Seed all knowledge types
            results = []
            
            cisco_result = await self.seed_cisco_knowledge()
            results.append(("Cisco IOS", cisco_result))
            
            proxmox_result = await self.seed_proxmox_knowledge()
            results.append(("Proxmox", proxmox_result))
            
            zabbix_result = await self.seed_zabbix_knowledge()
            results.append(("Zabbix", zabbix_result))
            
            k8s_result = await self.seed_kubernetes_knowledge()
            results.append(("Kubernetes", k8s_result))
            
            security_result = await self.seed_security_knowledge()
            results.append(("Security", security_result))
            
            # Get final stats
            stats = await knowledge_manager.get_tenant_stats(self.global_tenant_id)
            
            # Summary
            logger.info("Global knowledge seeding completed!")
            logger.info(f"Total documents: {stats['total_documents']}")
            
            for name, result in results:
                logger.info(f"{name}: {result['chunks']} chunks indexed")
            
            return {
                "status": "success",
                "total_documents": stats['total_documents'],
                "knowledge_types": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to seed global knowledge: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


async def main():
    """Main seeding function"""
    seeder = GlobalKnowledgeSeeder()
    result = await seeder.seed_all_knowledge()
    
    print(f"\n{'='*60}")
    print("GLOBAL KNOWLEDGE SEEDING RESULTS")
    print(f"{'='*60}")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Total Documents: {result['total_documents']}")
        print("\nKnowledge Types:")
        for name, info in result['knowledge_types']:
            print(f"  - {name}: {info['chunks']} chunks")
    
    print(f"Timestamp: {result['timestamp']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
