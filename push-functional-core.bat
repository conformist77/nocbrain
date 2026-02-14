@echo off
cd c:\Users\renderkar\Documents\NOCbRAIN

echo Adding functional core engine files...
git add backend/app/core/logic/
git add backend/app/api/endpoints/core_engine.py
git add backend/app/schemas/core_engine.py
git add backend/app/collectors/protocols/
git add backend/app/security-analyzer/pattern_engine.py
git add backend/app/main.py
git add docker-compose.yml

echo Committing functional core engine implementation...
git commit -m "feat: Implement complete functional core engine with RAG and AI

🧠 RAG (Retrieval-Augmented Generation) System:
- Knowledge Manager with LangChain and Qdrant integration
- Vector database for knowledge base indexing
- Network knowledge schema for content classification
- Real-time knowledge querying and retrieval
- Support for multiple knowledge types (Cisco, Proxmox, Zabbix, Security)

🔄 AI Reasoning Engine:
- Live intelligence processing loop with priority queues
- Security event prioritization and fast-track processing
- Real-time log analysis with AI-powered insights
- Automatic NOC action plan generation
- Similar incident search and knowledge retrieval

🔍 Protocol Handlers:
- SNMP Handler for Zabbix integration
- SSH Handler for Proxmox and server management
- Multi-platform support (Linux, Proxmox, Cisco)
- Real-time metrics collection and monitoring
- Health checks and connection management

🛡️ Security Pattern Engine:
- Advanced threat detection with pattern matching
- Lateral movement and brute force detection
- C2 communication and malware identification
- IP reputation and user behavior analysis
- SIEM/XDR log analysis capabilities

🌐 Enhanced API Endpoints:
- Core engine API with RAG integration
- Real-time log analysis and batch processing
- Knowledge base management and querying
- Incident response and action plan generation
- Comprehensive system health monitoring

🐳 Multi-Pod Scaling:
- Enhanced Docker Compose with resource limits
- Qdrant vector database integration
- Health checks for all services
- Proper service dependencies and networking
- Volume management for persistent data

🚀 Key Features:
- Real-time AI-powered log analysis
- Knowledge-driven incident response
- Security threat detection and prioritization
- Multi-protocol data collection
- Scalable microservices architecture

This transforms NOCbRAIN from boilerplate to a fully functional
AI-powered Network Operations Center with RAG capabilities."

echo Pushing to GitHub...
git push origin main

echo Done!
pause
