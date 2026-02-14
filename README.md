# NOCbRAIN - AI Network Operations Center Assistant

## Overview
NOCbRAIN is an open-source AI-powered assistant for network monitoring, security analysis, and infrastructure management. Designed as a global SaaS solution to help organizations worldwide with their NOC operations.

## Features
- 🌐 **Network Monitoring**: Real-time monitoring of network devices, switches, routers, and firewalls
- 🔒 **Security Analysis**: SIEM, XDR, EDR integration for advanced threat detection
- ☁️ **Infrastructure Management**: VMware ESX, KVM, and cloud platform monitoring
- 📊 **Application Monitoring**: Microservices, databases, and load balancer monitoring
- 🧠 **AI-Powered Analysis**: Intelligent log analysis and threat detection
- 📚 **Knowledge Base**: Integrated wiki and documentation system
- 🐳 **Container-Ready**: Docker and Kubernetes deployment support

## Architecture
- **Backend**: Python with FastAPI
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL + Redis
- **AI/ML**: PyTorch + LangChain
- **Containerization**: Docker + Kubernetes
- **Security**: OAuth2 + JWT + HashiCorp Vault

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+
- Node.js 16+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/nocbrain.git
cd nocbrain

# Copy environment files
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Or install locally
./scripts/setup.sh
```

### Configuration
Edit `.env` file with your specific configurations:
- Database credentials
- API keys
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
