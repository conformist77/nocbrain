# NOCbRAIN - AI Network Operations Center Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/conformist77/nocbrain.git
cd nocbrain

# Run setup script (Linux/macOS)
chmod +x setup-clean.sh
./setup-clean.sh install

# Or on Windows
setup-clean.bat

# Start development servers
./setup-clean.sh dev
```

## 📋 What is NOCbRAIN?

NOCbRAIN is an **AI-powered Network Operations Center Assistant** that provides:

- 🌐 **Multi-tenant SaaS Architecture** with strict data isolation
- 🤖 **AI-powered log analysis** using LangChain and OpenAI
- 📊 **Real-time monitoring** with Prometheus and Grafana
- 🔒 **Advanced security analysis** with pattern detection
- 🧠 **Knowledge management** with RAG (Retrieval-Augmented Generation)
- 📱 **Modern web interface** with React and TypeScript
- 🐳 **Containerized deployment** with Docker and Kubernetes

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Core       │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   (LangChain)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Database      │              │
         │              │   (PostgreSQL)  │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Vector DB     │    │   Message Queue │
│   (Prometheus)  │    │   (Qdrant)      │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI with Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for session management and caching
- **AI/ML**: LangChain, OpenAI GPT-4, Qdrant Vector DB
- **Authentication**: JWT with OAuth2
- **Monitoring**: Prometheus metrics and structured logging

### Frontend
- **Framework**: React 18 with TypeScript
- **UI Library**: Ant Design Components
- **State Management**: React Query and Context API
- **Real-time**: WebSocket connections
- **Charts**: Chart.js and D3.js for visualizations

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Orchestration**: Kubernetes with Helm charts
- **Monitoring**: Prometheus + Grafana stack
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **CI/CD**: GitHub Actions with automated testing

## 📁 Project Structure

```
nocbrain/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── modules/        # Business logic modules
│   │   └── middleware/     # Custom middleware
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   └── package.json        # Node.js dependencies
├── agents/                 # AI monitoring agents
│   ├── monitoring_agent.py # System monitoring
│   └── security_agent.py   # Security monitoring
├── k8s/                    # Kubernetes manifests
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── docker-compose.yml      # Development environment
```

## 🔧 Installation

### Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **Docker & Docker Compose**
- **PostgreSQL 13+**
- **Redis 6+**

### Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/conformist77/nocbrain.git
   cd nocbrain
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration**
   ```bash
   # Backend environment
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   
   # Frontend environment
   cp frontend/.env.example frontend/.env
   # Edit frontend/.env with your configuration
   ```

5. **Database Setup**
   ```bash
   cd backend
   source venv/bin/activate
   alembic upgrade head
   python scripts/init_data.py
   ```

6. **Start Services**
   ```bash
   # Start databases
   docker-compose up -d postgres redis qdrant
   
   # Start backend
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start frontend (new terminal)
   cd frontend
   npm start
   ```

## 🚀 Usage

### Access Points

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001
- **Prometheus**: http://localhost:9090

### Key Features

#### 1. **Multi-tenant Dashboard**
- Tenant-specific metrics and analytics
- Isolated data per organization
- Customizable dashboards

#### 2. **AI-Powered Log Analysis**
- Real-time log processing with AI
- Automated incident detection
- Natural language explanations

#### 3. **Security Monitoring**
- Threat pattern detection
- Real-time security alerts
- Automated incident response

#### 4. **Knowledge Management**
- RAG-powered knowledge base
- Document indexing and search
- AI-generated recommendations

## 📊 API Examples

### Analyze Log Entry
```bash
curl -X POST "http://localhost:8000/api/v1/tenant/analyze-log" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-uuid" \
  -d '{
    "log_data": {
      "timestamp": "2024-02-14T10:30:00Z",
      "source": "zabbix",
      "content": "CPU usage on server web-01 is 95%",
      "severity": "high"
    }
  }'
```

### Get Tenant Dashboard
```bash
curl -X GET "http://localhost:8000/api/v1/tenant/dashboard" \
  -H "X-Tenant-ID: your-tenant-uuid"
```

### Query Knowledge Base
```bash
curl -X POST "http://localhost:8000/api/v1/tenant/knowledge/query" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: your-tenant-uuid" \
  -d '{
    "query": "How to troubleshoot high CPU usage",
    "top_k": 5
  }'
```

## 🔒 Security Features

- **Multi-tenant isolation** with UUID-based tenant IDs
- **JWT authentication** with role-based access control
- **API rate limiting** and request validation
- **Encrypted data storage** with AES-256
- **Security scanning** in CI/CD pipeline
- **OWASP compliance** and security best practices

## 📈 Monitoring & Observability

### Metrics Collection
- System performance metrics
- Application performance monitoring
- Business KPI tracking
- Custom metrics integration

### Logging
- Structured JSON logging
- Centralized log aggregation
- Log analysis with AI
- Real-time log streaming

### Alerting
- Configurable alert thresholds
- Multi-channel notifications
- Alert escalation rules
- Automated incident response

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=xml --cov-report=html

# Frontend tests
cd frontend
npm test -- --coverage --watchAll=false

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and deploy
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n nocbrain
```

### Production Deployment
1. Configure environment variables
2. Set up SSL certificates
3. Configure database clustering
4. Set up monitoring and alerting
5. Enable backup and disaster recovery

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python3 --version

# Check virtual environment
source backend/venv/bin/activate
which python

# Check dependencies
pip list | grep fastapi

# Check database connection
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

#### Frontend Build Fails
```bash
# Clear node modules
rm -rf frontend/node_modules
npm install

# Check Node version
node --version
npm --version

# Clear cache
npm cache clean --force
```

#### Database Connection Issues
```bash
# Check Docker containers
docker-compose ps

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U nocbrain
```

#### API Authentication Fails
- Verify `X-Tenant-ID` header is included
- Check JWT token validity
- Ensure user has required permissions
- Check API rate limits

#### AI Features Not Working
- Verify OpenAI API key in `.env`
- Check Qdrant vector database status
- Ensure knowledge base is indexed
- Check API quotas and limits

### Logs and Debugging

```bash
# Backend logs
tail -f backend.log

# Frontend logs
cd frontend && npm start  # Check console

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Database logs
docker-compose logs -f postgres
```

### Performance Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Monitor backend processes
   ps aux | grep uvicorn
   ```

2. **Slow API Responses**
   ```bash
   # Check database performance
   docker-compose exec postgres pg_stat_activity;
   
   # Monitor Redis
   docker-compose exec redis redis-cli info
   ```

3. **Frontend Loading Issues**
   ```bash
   # Check bundle size
   cd frontend && npm run build -- --stats
   
   # Test network requests
   curl -I http://localhost:3000
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write tests for new features
- Update documentation
- Follow conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: https://github.com/conformist77/nocbrain/tree/main/docs
- **Issues**: https://github.com/conformist77/nocbrain/issues
- **Discussions**: https://github.com/conformist77/nocbrain/discussions
- **Email**: support@nocbrain.org

## 🗺️ Roadmap

### Version 1.1 (Q2 2024)
- [ ] Advanced AI/ML models
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Multi-cloud support

### Version 1.2 (Q3 2024)
- [ ] Edge computing support
- [ ] 5G network monitoring
- [ ] Predictive maintenance
- [ ] Advanced threat intelligence

### Version 2.0 (Q4 2024)
- [ ] Full microservices architecture
- [ ] Advanced AI orchestration
- [ ] Global CDN support
- [ ] Enterprise features

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - JavaScript library for building UIs
- [LangChain](https://langchain.com/) - Framework for AI applications
- [Qdrant](https://qdrant.tech/) - Vector similarity search engine
- [Ant Design](https://ant.design/) - Enterprise UI design language

---

**Built with ❤️ by the NOCbRAIN Team**
- Security settings
- Monitoring targets

## 📚 Documentation System

NOCbRAIN provides comprehensive documentation for different user groups:

### 📖 Documentation Categories
1. **🧑‍💻 Developer Documentation** - Architecture, API, modules, development setup
2. **🔧 Operations Documentation** - Installation, maintenance, troubleshooting, infrastructure
3. **🛡️ NOC/SOC Documentation** - User guides, alert management, incident response
4. **📈 Marketing Documentation** - Product overview, features, case studies, technical specs
5. **🤖 AI/ML Documentation** - XML format for AI systems to understand product nature

### 🔄 Auto-Update Process
Documentation is automatically updated based on version changes:
```bash
# Update all documentation
./scripts/update-docs.sh --version v1.0.0

# Update specific category
./scripts/update-docs.sh --category developer --version v1.0.0

# Deploy to production
./scripts/deploy-docs.sh --version v1.0.0 --environment production
```

### 📦 Downloadable Documentation Packages
Each category generates downloadable packages:
- `nocbrain-developer-docs-v1.0.0.pdf`
- `nocbrain-operations-docs-v1.0.0.pdf`
- `nocbrain-noc-soc-docs-v1.0.0.pdf`
- `nocbrain-marketing-docs-v1.0.0.pdf`
- `nocbrain-ai-ml-docs-v1.0.0.xml`

### 🚀 Quick Access
- **Live Documentation**: https://docs.nocbrain.com
- **API Reference**: https://api.nocbrain.com/docs
- **Developer Portal**: https://dev.nocbrain.com
- **Operations Guide**: https://ops.nocbrain.com
- **NOC/SOC Portal**: https://portal.nocbrain.com
- **Package Repository**: https://packages.nocbrain.com

### 🔄 CI/CD Integration
Documentation is automatically updated and deployed via GitHub Actions:
- Triggers on code changes, version tags, and manual dispatch
- Generates all documentation categories automatically
- Deploys to staging/production environments
- Creates downloadable packages
- Verifies deployment and sends notifications

## Contributing
We welcome contributions! Please read our [Contributing Guidelines](./CONTRIBUTING.md).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
- 📧 Email: support@nocbrain.org
- 💬 Discord: [Join our community](https://discord.gg/nocbrain)
- 📖 Wiki: [Documentation](https://wiki.nocbrain.org)

## Security
For security concerns, please email security@nocbrain.org or use our private disclosure process.

---
**NOCbRAIN** - Empowering NOCs with AI intelligence 🚀
