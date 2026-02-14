@echo off
cd c:\Users\renderkar\Documents\NOCbRAIN

echo Adding monitoring agent files...
git add agents/
git add backend/app/modules/monitoring/
git add backend/app/api/endpoints/monitoring.py
git add backend/app/schemas/monitoring.py

echo Committing monitoring agent update...
git commit -m "feat: Add secure monitoring agent system with advanced metrics collection

🚀 New Features Added:
- Secure monitoring agent with encryption support
- Multi-platform agent (Windows, Linux, macOS)
- Real-time metrics collection and transmission
- Advanced system and application monitoring
- Agent registration and management API
- Alert rules and notification system
- WebSocket real-time updates
- Prometheus metrics integration

🔧 Security Features:
- End-to-end encryption with Fernet
- API key authentication
- SSL/TLS secure communication
- Agent verification and validation
- Secure configuration management

📊 Monitoring Capabilities:
- System metrics (CPU, Memory, Disk, Network)
- Application monitoring (Nginx, Apache, MySQL, PostgreSQL, Redis, Docker)
- Custom metrics support
- Real-time alerting
- Historical data storage and querying

🛠️ Installation & Deployment:
- Automated installation scripts (Linux/Windows)
- Systemd service integration (Linux)
- Windows service integration
- Firewall configuration
- Configuration management

🌐 API Endpoints:
- /api/v1/monitoring/metrics - Receive metrics
- /api/v1/monitoring/heartbeat - Agent heartbeat
- /api/v1/monitoring/agents - Agent management
- /api/v1/monitoring/alerts - Alert management
- /api/v1/monitoring/realtime - WebSocket updates

This complements SNMP monitoring with a more secure, comprehensive, and real-time agent-based approach."

echo Pushing to GitHub...
git push origin main

echo Done!
pause
