# Linux System Troubleshooting Guide

## High CPU Usage

### Symptoms
- System running slow
- Load average high
- Processes unresponsive

### Step-by-Step Resolution

1. **Identify High CPU Processes**
   ```bash
   top -bn1 | head -20
   ```
   Look for processes using high CPU percentages.

2. **Check System Load**
   ```bash
   uptime
   cat /proc/loadavg
   ```
   Load average should be below number of CPU cores.

3. **Find Process Details**
   ```bash
   ps aux | grep <process_name>
   ```
   Get PID and process details.

4. **Kill or Restart Process**
   ```bash
   kill -9 <PID>
   # or
   systemctl restart <service_name>
   ```

5. **Monitor System**
   ```bash
   htop
   iostat -x 1
   ```

### Prevention Measures
- Set up CPU monitoring alerts
- Implement auto-scaling
- Optimize application performance
- Regular system maintenance

## High Memory Usage

### Symptoms
- Out of memory errors
- System swapping heavily
- Applications crashing

### Step-by-Step Resolution

1. **Check Memory Usage**
   ```bash
   free -h
   cat /proc/meminfo
   ```

2. **Find Memory-Hungry Processes**
   ```bash
   ps aux --sort=-%mem | head -10
   ```

3. **Check Swap Usage**
   ```bash
   swapon -s
   free -h
   ```

4. **Clear System Cache**
   ```bash
   echo 3 > /proc/sys/vm/drop_caches
   ```

5. **Restart Memory-Intensive Services**
   ```bash
   systemctl restart <service_name>
   ```

## Disk Space Issues

### Symptoms
- Cannot write files
- Applications failing to start
- System warnings about disk space

### Step-by-Step Resolution

1. **Check Disk Usage**
   ```bash
   df -h
   du -sh /*
   ```

2. **Find Large Files**
   ```bash
   find / -type f -size +100M 2>/dev/null
   ```

3. **Clean Log Files**
   ```bash
   journalctl --vacuum-time=7d
   find /var/log -name "*.log" -mtime +30 -delete
   ```

4. **Clean Package Cache**
   ```bash
   apt-get clean
   yum clean all
   ```

5. **Remove Unused Packages**
   ```bash
   apt-get autoremove
   yum autoremove
   ```

## Network Connectivity Issues

### Symptoms
- Cannot connect to network
- Slow network performance
- Connection timeouts

### Step-by-Step Resolution

1. **Check Network Interface**
   ```bash
   ip addr show
   ifconfig -a
   ```

2. **Test Connectivity**
   ```bash
   ping 8.8.8.8
   traceroute 8.8.8.8
   ```

3. **Check DNS Resolution**
   ```bash
   nslookup google.com
   dig google.com
   ```

4. **Check Firewall Rules**
   ```bash
   iptables -L
   ufw status
   ```

5. **Restart Network Service**
   ```bash
   systemctl restart networking
   systemctl restart NetworkManager
   ```

## Service Management

### Common Service Commands

1. **Check Service Status**
   ```bash
   systemctl status <service_name>
   service <service_name> status
   ```

2. **Start/Stop/Restart Service**
   ```bash
   systemctl start <service_name>
   systemctl stop <service_name>
   systemctl restart <service_name>
   ```

3. **Enable/Disable Service**
   ```bash
   systemctl enable <service_name>
   systemctl disable <service_name>
   ```

4. **View Service Logs**
   ```bash
   journalctl -u <service_name> -f
   tail -f /var/log/<service_name>.log
   ```

## System Performance Monitoring

### Key Commands

1. **System Overview**
   ```bash
   top
   htop
   glances
   ```

2. **Resource Usage**
   ```bash
   vmstat 1
   iostat -x 1
   sar -u 1
   ```

3. **Process Monitoring**
   ```bash
   ps aux
   pstree
   lsof -i
   ```

4. **Network Monitoring**
   ```bash
   netstat -tuln
   ss -tuln
   nethogs
   ```

## Log Analysis

### Important Log Files

- `/var/log/syslog` - System logs
- `/var/log/auth.log` - Authentication logs
- `/var/log/kern.log` - Kernel logs
- `/var/log/dmesg` - Boot messages
- `journalctl` - Systemd journal

### Log Analysis Commands

1. **Real-time Log Monitoring**
   ```bash
   tail -f /var/log/syslog
   journalctl -f
   ```

2. **Search Logs**
   ```bash
   grep "error" /var/log/syslog
   journalctl -u <service_name> --since "1 hour ago"
   ```

3. **Log Rotation**
   ```bash
   logrotate -f /etc/logrotate.conf
   ```

## Security Troubleshooting

### Common Security Issues

1. **Failed Login Attempts**
   ```bash
   grep "Failed password" /var/log/auth.log
   lastb
   ```

2. **Suspicious Processes**
   ```bash
   ps aux | grep -v "^\[" | sort -k4 -nr
   ```

3. **Network Connections**
   ```bash
   netstat -tuln
   ss -tuln
   lsof -i
   ```

4. **File Integrity**
   ```bash
   find / -perm -4000 -type f
   find / -name "*.sh" -perm -u+x
   ```

## Emergency Procedures

### System Recovery

1. **Boot into Rescue Mode**
   - Single user mode: `systemctl rescue`
   - Recovery mode via bootloader

2. **File System Check**
   ```bash
   fsck -y /dev/sda1
   ```

3. **Backup Critical Data**
   ```bash
   tar -czf backup.tar.gz /important/data
   rsync -av /source/ /backup/
   ```

4. **System Restore**
   ```bash
   # From backup
   tar -xzf backup.tar.gz -C /
   
   # From snapshot (if using LVM/btrfs)
   lvcreate --snapshot -n backup -L 10G /dev/vg/root
   ```

## Performance Optimization

### System Tuning

1. **Kernel Parameters**
   ```bash
   echo 'vm.swappiness=10' >> /etc/sysctl.conf
   echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
   sysctl -p
   ```

2. **Process Limits**
   ```bash
   echo '* soft nofile 65536' >> /etc/security/limits.conf
   echo '* hard nofile 65536' >> /etc/security/limits.conf
   ```

3. **I/O Scheduler**
   ```bash
   echo deadline > /sys/block/sda/queue/scheduler
   ```

## Automation

### Monitoring Scripts

1. **CPU Alert Script**
   ```bash
   #!/bin/bash
   CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
   if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
       echo "High CPU usage: $CPU_USAGE%" | mail -s "CPU Alert" admin@example.com
   fi
   ```

2. **Disk Space Check**
   ```bash
   #!/bin/bash
   DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
   if [ $DISK_USAGE -gt 90 ]; then
       echo "Disk usage critical: $DISK_USAGE%" | mail -s "Disk Alert" admin@example.com
   fi
   ```

## Best Practices

1. **Regular Maintenance**
   - Update system packages
   - Clean old logs and temporary files
   - Monitor system resources
   - Backup important data

2. **Documentation**
   - Document system configuration
   - Keep troubleshooting records
   - Maintain change logs
   - Create runbooks for common issues

3. **Monitoring**
   - Set up comprehensive monitoring
   - Configure alert thresholds
   - Monitor key performance indicators
   - Review logs regularly

4. **Security**
   - Keep system updated
   - Use strong passwords
   - Configure firewall properly
   - Monitor for suspicious activity
