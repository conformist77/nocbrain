# GitHub Copilot Setup Prompt for NOCbRAIN

## Instructions for GitHub Copilot

Copy and paste this entire prompt into GitHub Copilot to automatically set up the NOCbRAIN project:

```
Create a comprehensive AI Network Operations Center Assistant called NOCbRAIN with the following requirements:

PROJECT STRUCTURE:
- Create a monorepo with backend (Python FastAPI) and frontend (React TypeScript)
- Include Docker and Kubernetes deployment configurations
- Set up CI/CD pipeline with GitHub Actions
- Create comprehensive documentation and security setup
- Implement modular architecture for network monitoring, security analysis, and infrastructure management

BACKEND REQUIREMENTS:
- FastAPI framework with async support
- PostgreSQL database with SQLAlchemy ORM
- Redis for caching and session management
- JWT authentication and authorization
- RESTful API with OpenAPI documentation
- WebSocket support for real-time updates
- Integration with external APIs (OpenAI, security tools)
- Modular structure: network, security, infrastructure, monitoring, knowledge modules
- Comprehensive logging with structured logs
- Health checks and metrics endpoints
- Rate limiting and security middleware

FRONTEND REQUIREMENTS:
- React 18 with TypeScript
- Ant Design for UI components
- React Query for data fetching
- React Router for navigation
- Real-time updates with WebSocket
- Responsive design for mobile and desktop
- Dashboard with charts and visualizations
- Dark/light theme support
- Internationalization support

SECURITY REQUIREMENTS:
- OAuth2 + JWT authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting
- Secure headers
- API key management
- Audit logging
- Secret management with HashiCorp Vault

MONITORING REQUIREMENTS:
- Prometheus metrics
- Grafana dashboards
- Log aggregation with ELK stack
- Application performance monitoring
- Error tracking and alerting
- Health checks for all services
- Resource usage monitoring

DEPLOYMENT REQUIREMENTS:
- Docker containerization
- Kubernetes orchestration
- Helm charts for deployment
- Environment-specific configurations
- Automated testing pipeline
- Security scanning
- Dependency vulnerability scanning
- Automated deployments to staging/production

DOCUMENTATION REQUIREMENTS:
- API documentation with OpenAPI/Swagger
- User guides and tutorials
- Developer documentation
- Architecture diagrams
- Security best practices
- Troubleshooting guides
- Knowledge base for network protocols and security threats

TESTING REQUIREMENTS:
- Unit tests with pytest (backend)
- Integration tests
- End-to-end tests
- Performance tests
- Security tests
- Code coverage reporting
- Automated testing in CI/CD

NETWORK MONITORING MODULE:
- SNMP monitoring for network devices
- NetFlow and sFlow analysis
- Network topology discovery
- Bandwidth monitoring
- Device health monitoring
- Configuration backup and management
- Network performance metrics

SECURITY ANALYSIS MODULE:
- SIEM integration
- XDR/EDR analysis
- Threat intelligence feeds
- Log analysis and correlation
- Intrusion detection
- Vulnerability scanning
- Security incident response
- Compliance monitoring

INFRASTRUCTURE MODULE:
- VMware ESX monitoring
- KVM management
- Cloud platform integration (AWS, Azure, GCP)
- Server health monitoring
- Storage monitoring
- Backup and recovery
- Resource utilization tracking

AI/ML FEATURES:
- Anomaly detection
- Predictive analytics
- Natural language processing for log analysis
- Automated incident response
- Intelligent alerting
- Pattern recognition
- Machine learning model training

KNOWLEDGE BASE MODULE:
- Wiki system for documentation
- Best practices repository
- Troubleshooting guides
- Network protocol documentation
- Security threat database
- Integration with external knowledge sources
- Search functionality

SECURITY IMPLEMENTATION:
- Environment variable management
- Secret rotation
- Secure communication (TLS/SSL)
- Database encryption
- API security
- Container security
- Network security policies
- Compliance frameworks (GDPR, HIPAA, SOC2)

PERFORMANCE OPTIMIZATION:
- Database query optimization
- Caching strategies
- CDN integration
- Load balancing
- Horizontal scaling
- Resource pooling
- Memory management
- Background job processing

Create all necessary files including:
- Docker and Docker Compose configurations
- Kubernetes manifests and Helm charts
- GitHub Actions workflows
- Environment configuration files
- Security configurations
- Monitoring dashboards
- Documentation files
- Test files
- Scripts for automation

Ensure the project follows security best practices, is production-ready, and can be easily deployed and scaled. Include comprehensive error handling, logging, and monitoring throughout the application.
```

## Additional Copilot Commands

After the initial setup, you can use these specific prompts:

### For Backend Development:
```
Create the network monitoring module with SNMP support, device discovery, and real-time metrics collection. Include proper error handling, logging, and API endpoints for device management.
```

### For Security Features:
```
Implement the security analysis module with SIEM integration, threat detection algorithms, and automated incident response workflows. Include proper authentication and authorization.
```

### For Frontend Dashboard:
```
Create a comprehensive dashboard with real-time network monitoring visualizations, security alerts, and infrastructure health metrics. Use charts, tables, and responsive design.
```

### For Deployment:
```
Set up Kubernetes deployment configurations with proper resource management, health checks, auto-scaling, and rolling updates. Include monitoring and logging integration.
```

### For Testing:
```
Create comprehensive test suites including unit tests, integration tests, and end-to-end tests. Set up automated testing in the CI/CD pipeline with proper coverage reporting.
```

## Usage Instructions

1. **Initial Setup**: Copy the main prompt above and paste it into GitHub Copilot
2. **Review Generated Code**: Carefully review all generated code for security and correctness
3. **Customize Configuration**: Update environment variables and configurations as needed
4. **Test Locally**: Run the application locally using Docker Compose
5. **Deploy**: Use the provided deployment scripts to deploy to your environment

## Security Notes

- Never commit actual secrets or API keys
- Use environment variables for all sensitive data
- Review all generated code for security vulnerabilities
- Enable security scanning in your CI/CD pipeline
- Follow the principle of least privilege

This setup will create a production-ready, secure, and scalable NOCbRAIN application with all the features you requested.
