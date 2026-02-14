#!/usr/bin/env python3
"""
NOCbRAIN User Guide Generator for NOC/SOC Personnel
Generates comprehensive user guides for Level 1 & 2 NOC and SOC personnel
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

def generate_user_guide(output_path):
    """Generate NOC/SOC user guide"""
    
    user_guide_content = f"""# NOCbRAIN User Guide for NOC/SOC Personnel

## 🚀 Quick Start

### System Access
1. **URL**: https://portal.nocbrain.com
2. **Credentials**: Provided by your system administrator
3. **First Login**: Change your password immediately
4. **Dashboard**: You'll see the main dashboard after login

### Dashboard Overview
```
┌─────────────────────────────────────────────────────────────┐
│  NOCbRAIN Dashboard - Real-time Network Operations Center   │
├─────────────────────────────────────────────────────────────┤
│  📊 Network Status    │  🚨 Active Alerts   │  📈 Metrics  │
│  🖥️  Devices Online    │  ⚠️  Warnings        │  📊 Performance│
│  🌐  Network Health    │  🔴 Critical Issues  │  📉 Trends    │
├─────────────────────────────────────────────────────────────┤
│  🔍 Search & Filter    │  📋 Recent Events   │  ⚙️  Settings  │
└─────────────────────────────────────────────────────────────┘
```

## 📚 Daily Operations

### Morning Checklist (Level 1)

#### System Health Check
- [ ] **Login Verification**: Ensure you can access the system
- [ ] **Dashboard Review**: Check overall system status
- [ ] **Alert Review**: Review all overnight alerts
- [ ] **System Messages**: Check for system notifications
- [ ] **Backup Status**: Verify backup completion

#### Network Status Check
- [ ] **Device Connectivity**: Verify all critical devices are online
- [ ] **Performance Metrics**: Check CPU, Memory, Network utilization
- [ ] **Service Status**: Verify all services are running
- [ ] **Security Events**: Review security event log

#### Documentation Update
- [ ] **Shift Log**: Document shift activities
- [ ] **Incident Reports**: Complete any pending reports
- [ ] **Knowledge Base**: Update with new information

### Ongoing Monitoring (Level 1)

#### Real-time Monitoring
1. **Dashboard Monitoring**: Keep dashboard visible at all times
2. **Alert Response**: Respond to alerts within SLA timeframes
3. **Performance Monitoring**: Monitor system performance metrics
4. **User Support**: Assist users with system issues

#### Alert Management
1. **Critical Alerts**: Immediate response required
2. **Warning Alerts**: Response within 15 minutes
3. **Info Alerts**: Review during next check cycle

#### Communication Protocol
1. **Team Communication**: Use internal chat for coordination
2. **Escalation**: Follow escalation procedures for critical issues
3. **Documentation**: Document all actions taken

### Advanced Operations (Level 2)

#### Incident Management
1. **Incident Triage**: Assess incident severity and impact
2. **Root Cause Analysis**: Investigate underlying causes
3. **Resolution Planning**: Develop resolution strategies
4. **Post-Incident Review**: Conduct post-incident analysis

#### Performance Analysis
1. **Trend Analysis**: Identify performance trends
2. **Capacity Planning**: Monitor resource utilization
3. **Optimization**: Recommend system improvements
4. **Reporting**: Generate performance reports

## 🚨 Alert Management

### Alert Severity Levels

#### 🔴 Critical Alerts
- **Response Time**: Immediate (within 5 minutes)
- **Examples**: System outage, security breach, critical device failure
- **Actions**: 
  1. Acknowledge alert immediately
  2. Escalate to Level 2/Management
  3. Begin incident response procedures
  4. Document all actions

#### 🟡 Warning Alerts
- **Response Time**: Within 15 minutes
- **Examples**: High resource utilization, device warnings, performance degradation
- **Actions**:
  1. Acknowledge alert
  2. Investigate cause
  3. Implement temporary fixes if needed
  4. Monitor for escalation

#### 🔵 Info Alerts
- **Response Time**: Within 1 hour
- **Examples**: System notifications, informational events, scheduled maintenance
- **Actions**:
  1. Review alert details
  2. Update documentation if needed
  3. No immediate action required unless specified

### Alert Response Procedures

#### Step 1: Alert Acknowledgment
1. **Locate Alert**: Find alert in dashboard or alert list
2. **Acknowledge**: Click "Acknowledge" button
3. **Add Comment**: Brief description of initial assessment
4. **Assign**: Assign to appropriate team member if needed

#### Step 2: Investigation
1. **Gather Information**: Check logs, metrics, and system status
2. **Identify Impact**: Determine affected systems and users
3. **Assess Severity**: Confirm alert severity level
4. **Document Findings**: Record investigation results

#### Step 3: Resolution
1. **Implement Fix**: Apply appropriate solution
2. **Verify Resolution**: Confirm issue is resolved
3. **Monitor**: Watch for recurrence
4. **Close Alert**: Close alert with resolution details

### Alert Escalation Procedures

#### Level 1 Escalation Criteria
- Multiple critical alerts in short time
- Unknown error patterns
- System-wide performance issues
- Security-related events

#### Escalation Process
1. **Notify Level 2**: Contact Level 2 personnel
2. **Provide Context**: Share investigation findings
3. **Transfer Ownership**: Handover incident ownership
4. **Document**: Record escalation details

## 🔍 Monitoring Procedures

### Network Device Monitoring

#### Device Status Check
1. **Connectivity**: Ping critical devices
2. **SNMP Status**: Verify SNMP communication
3. **Interface Status**: Check interface operational status
4. **Performance**: Monitor CPU, Memory, and bandwidth

#### Automated Monitoring
1. **Dashboard**: Monitor real-time dashboard
2. **Alerts**: Respond to system-generated alerts
3. **Reports**: Review scheduled monitoring reports
4. **Trends**: Analyze performance trends

### Application Monitoring

#### Service Status
1. **Web Services**: Check web application availability
2. **Database Services**: Verify database connectivity
3. **API Services**: Test API endpoint responses
4. **Background Jobs**: Monitor scheduled job execution

#### Performance Metrics
1. **Response Times**: Monitor application response times
2. **Error Rates**: Track application error rates
3. **Resource Usage**: Monitor CPU, Memory, Disk usage
4. **User Experience**: Track user experience metrics

### Security Monitoring

#### Security Events
1. **Login Attempts**: Monitor failed login attempts
2. **Access Patterns**: Review unusual access patterns
3. **Threat Detection**: Review security threat alerts
4. **Compliance**: Verify compliance with security policies

#### Incident Response
1. **Security Incidents**: Follow security incident procedures
2. **Forensics**: Preserve evidence for investigation
3. **Reporting**: Report security incidents to management
4. **Prevention**: Implement prevention measures

## 📊 Reporting Procedures

### Daily Reports

#### Shift Report Template
```
SHIFT REPORT - [DATE] - [SHIFT TIME]
==========================================
Operator: [NAME]
Shift Time: [START] - [END]

SYSTEM STATUS:
- Overall Health: [GREEN/YELLOW/RED]
- Devices Online: [NUMBER]/[TOTAL]
- Active Alerts: [NUMBER]

ALERTS SUMMARY:
- Critical: [NUMBER]
- Warning: [NUMBER]
- Info: [NUMBER]

INCIDENTS:
- [List of incidents handled]

ISSUES IDENTIFIED:
- [List of issues found]

ACTIONS TAKEN:
- [List of actions performed]

HANDOVER NOTES:
- [Information for next shift]
```

### Weekly Reports

#### Performance Summary
1. **System Availability**: Calculate uptime percentage
2. **Alert Statistics**: Summarize alert trends
3. **Incident Summary**: Document major incidents
4. **Performance Metrics**: Track key performance indicators

### Monthly Reports

#### Management Report
1. **Executive Summary**: High-level overview
2. **Trend Analysis**: Monthly trend analysis
3. **Incident Review**: Major incident review
4. **Improvement Plans**: Proposed improvements

## 🛠️ Troubleshooting Guide

### Common Issues

#### System Access Issues
**Problem**: Cannot login to NOCbRAIN
**Symptoms**: Login page shows error, authentication failure
**Solutions**:
1. Verify credentials are correct
2. Check account status (not locked/disabled)
3. Clear browser cache and cookies
4. Try different browser
5. Contact system administrator

#### Device Offline Issues
**Problem**: Device showing as offline
**Symptoms**: Device status red, no data received
**Solutions**:
1. Ping device from monitoring server
2. Check network connectivity
3. Verify SNMP configuration
4. Check device power and status
5. Review device logs

#### Performance Issues
**Problem**: Slow system response
**Symptoms**: Dashboard loading slowly, delayed alerts
**Solutions**:
1. Check system resource utilization
2. Verify database performance
3. Review network bandwidth
4. Check for system bottlenecks
5. Restart services if needed

### Advanced Troubleshooting

#### Log Analysis
1. **System Logs**: Review application logs
2. **Error Logs**: Check error logs for patterns
3. **Access Logs**: Review access logs for issues
4. **Security Logs**: Analyze security events

#### Performance Analysis
1. **Metrics Review**: Analyze performance metrics
2. **Trend Analysis**: Identify performance trends
3. **Bottleneck Identification**: Find system bottlenecks
4. **Optimization**: Recommend optimizations

## 📞 Communication Procedures

### Internal Communication

#### Team Communication
1. **Chat System**: Use internal chat for real-time communication
2. **Email**: Use email for formal communications
3. **Meetings**: Attend regular team meetings
4. **Documentation**: Document important decisions

#### Escalation Communication
1. **Immediate Escalation**: Contact Level 2 for critical issues
2. **Management Notification**: Inform management of major incidents
3. **Customer Communication**: Coordinate with customer support
4. **Vendor Communication**: Contact vendors for hardware/software issues

### External Communication

#### Customer Communication
1. **Incident Notification**: Inform customers of major outages
2. **Status Updates**: Provide regular status updates
3. **Resolution Notification**: Notify customers when issues are resolved
4. **Follow-up**: Conduct post-incident follow-up

#### Vendor Communication
1. **Support Tickets**: Create support tickets with vendors
2. **Technical Support**: Contact vendor technical support
3. **Hardware Issues**: Report hardware failures
4. **Software Issues**: Report software bugs

## 📋 Standard Operating Procedures

### Incident Response SOP

#### Phase 1: Detection
1. **Alert Detection**: Monitor for system alerts
2. **User Reports**: Respond to user reports
3. **Automated Monitoring**: Review automated monitoring results
4. **Initial Assessment**: Assess incident severity

#### Phase 2: Response
1. **Incident Triage**: Triage incident based on severity
2. **Team Notification**: Notify appropriate team members
3. **Initial Response**: Begin initial response actions
4. **Documentation**: Start incident documentation

#### Phase 3: Resolution
1. **Investigation**: Investigate root cause
2. **Resolution**: Implement resolution
3. **Verification**: Verify resolution is effective
4. **Recovery**: Restore normal operations

#### Phase 4: Post-Incident
1. **Review**: Conduct post-incident review
2. **Documentation**: Complete incident documentation
3. **Improvement**: Identify improvement opportunities
4. **Prevention**: Implement prevention measures

### Maintenance SOP

#### Scheduled Maintenance
1. **Planning**: Plan maintenance activities
2. **Notification**: Notify affected users
3. **Execution**: Execute maintenance procedures
4. **Verification**: Verify system is functioning correctly

#### Emergency Maintenance
1. **Assessment**: Assess need for emergency maintenance
2. **Approval**: Obtain required approvals
3. **Execution**: Execute emergency maintenance
4. **Communication**: Communicate with stakeholders

## 🎯 Performance Metrics

### Key Performance Indicators (KPIs)

#### System Performance
- **System Availability**: Target 99.9%
- **Mean Time to Respond (MTTR)**: Target 5 minutes for critical
- **Mean Time to Resolve (MTTR)**: Target 1 hour for critical
- **Alert Response Time**: Target within SLA

#### Team Performance
- **Alert Acknowledgment Rate**: Target 95%
- **First Contact Resolution**: Target 80%
- **Customer Satisfaction**: Target 90%
- **Training Completion**: Target 100%

### Performance Monitoring

#### Daily Metrics
1. **Alert Volume**: Number of alerts per day
2. **Response Times**: Average response times
3. **Resolution Times**: Average resolution times
4. **System Uptime**: System availability percentage

#### Weekly Metrics
1. **Trend Analysis**: Alert trends over time
2. **Performance Trends**: System performance trends
3. **Team Performance**: Team performance metrics
4. **Improvement Areas**: Areas needing improvement

## 📚 Knowledge Management

### Knowledge Base

#### Documentation Requirements
1. **Procedures**: Document all standard procedures
2. **Troubleshooting**: Document common issues and solutions
3. **System Information**: Document system configurations
4. **Contact Information**: Maintain contact lists

#### Knowledge Sharing
1. **Team Meetings**: Share knowledge in team meetings
2. **Training Sessions**: Conduct regular training sessions
3. **Documentation Updates**: Keep documentation current
4. **Best Practices**: Share best practices

### Training Requirements

#### Initial Training
1. **System Training**: Comprehensive system training
2. **Procedure Training**: Standard procedure training
3. **Tool Training**: Tool and application training
4. **Safety Training**: Safety and security training

#### Ongoing Training
1. **Refresher Training**: Regular refresher courses
2. **New Feature Training**: Training on new features
3. **Advanced Training**: Advanced topic training
4. **Cross-Training**: Cross-functional training

## 🚨 Emergency Procedures

### System Outage Procedures

#### Immediate Response
1. **Assessment**: Assess outage scope and impact
2. **Communication**: Notify stakeholders
3. **Restoration**: Begin restoration procedures
4. **Documentation**: Document outage details

#### Recovery Procedures
1. **System Recovery**: Restore system operations
2. **Data Recovery**: Verify data integrity
3. **Service Recovery**: Restore all services
4. **User Notification**: Notify users of recovery

### Security Incident Procedures

#### Security Breach Response
1. **Containment**: Contain security breach
2. **Investigation**: Investigate security incident
3. **Notification**: Notify security team
4. **Documentation**: Document security incident

#### Forensics Procedures
1. **Evidence Preservation**: Preserve digital evidence
2. **Analysis**: Conduct forensic analysis
3. **Reporting**: Generate forensic reports
4. **Prevention**: Implement prevention measures

---

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*User Guide Version: 1.0.0*
*Target Audience: NOC/SOC Personnel (Level 1 & 2)*
"""

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(user_guide_content)
    
    print(f"NOC/SOC user guide generated: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate NOCbRAIN NOC/SOC user guide')
    parser.add_argument('--output', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    generate_user_guide(args.output)

if __name__ == '__main__':
    main()
