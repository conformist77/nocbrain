#!/bin/bash

# NOCbRAIN Setup Script
# This script sets up the entire NOCbRAIN project structure

set -e

echo "🚀 Setting up NOCbRAIN - AI Network Operations Center Assistant"

# Create main directories
echo "📁 Creating project structure..."
mkdir -p {backend,frontend,docs,scripts,configs,tests,deployments,k8s,docker}
mkdir -p backend/{app,tests,migrations}
mkdir -p backend/app/{api,core,models,services,utils,modules}
mkdir -p backend/app/modules/{network,security,infrastructure,monitoring,knowledge}
mkdir -p frontend/{src,public,tests}
mkdir -p frontend/src/{components,pages,services,utils,types,hooks}
mkdir -p docs/{api,user-guide,developer-guide,security,wiki}
mkdir -p k8s/{namespaces,configmaps,secrets,deployments,services,ingress}
mkdir -p docker/{backend,frontend,databases}

# Create backend structure
echo "🐍 Setting up Python backend..."
cd backend

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
celery==5.3.4
pika==1.3.2
prometheus-client==0.19.0
structlog==23.2.0
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
langchain==0.0.350
openai==1.3.7
torch==2.1.1
transformers==4.36.0
scikit-learn==1.3.2
pandas==2.1.4
numpy==1.25.2
plotly==5.17.0
dash==2.14.2
netmiko==4.2.0
paramiko==3.3.1
pysnmp==4.4.12
elasticsearch==8.11.0
kubernetes==28.1.0
vault==1.1.3
EOF

# Create main app file
cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import init_db
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Network Operations Center Assistant",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "NOCbRAIN"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
EOF

# Create core configuration
mkdir -p app/core
cat > app/core/config.py << 'EOF'
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "NOCbRAIN"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://nocbrain:nocbrain@localhost/nocbrain"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    
    # Security
    VAULT_URL: str = "http://localhost:8200"
    VAULT_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()
EOF

cd ..

# Create frontend structure
echo "⚛️ Setting up React frontend..."
cd frontend

# Create package.json
cat > package.json << 'EOF'
{
  "name": "nocbrain-frontend",
  "version": "1.0.0",
  "description": "NOCbRAIN Frontend Application",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css,md}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "axios": "^1.6.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.0",
    "recharts": "^2.8.0",
    "socket.io-client": "^4.7.0",
    "dayjs": "^1.11.0",
    "lodash": "^4.17.21",
    "react-query": "^3.39.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/lodash": "^4.14.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "prettier": "^3.1.0",
    "typescript": "^5.0.2",
    "vite": "^4.4.0"
  }
}
EOF

# Create main React component
mkdir -p src
cat > src/App.tsx << 'EOF'
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from 'react-query';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import NetworkMonitor from './pages/NetworkMonitor';
import SecurityAnalysis from './pages/SecurityAnalysis';
import Infrastructure from './pages/Infrastructure';
import KnowledgeBase from './pages/KnowledgeBase';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider>
        <Router>
          <MainLayout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/network" element={<NetworkMonitor />} />
              <Route path="/security" element={<SecurityAnalysis />} />
              <Route path="/infrastructure" element={<Infrastructure />} />
              <Route path="/knowledge" element={<KnowledgeBase />} />
            </Routes>
          </MainLayout>
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
EOF

cd ..

# Create Docker configuration
echo "🐳 Creating Docker configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://nocbrain:nocbrain@db:5432/nocbrain
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    networks:
      - nocbrain-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
    networks:
      - nocbrain-network

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=nocbrain
      - POSTGRES_USER=nocbrain
      - POSTGRES_PASSWORD=nocbrain
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - nocbrain-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - nocbrain-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - nocbrain-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - nocbrain-network

volumes:
  postgres_data:
  grafana_data:

networks:
  nocbrain-network:
    driver: bridge
EOF

# Create Kubernetes manifests
echo "☸️ Creating Kubernetes manifests..."
cd k8s

cat > namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: nocbrain
  labels:
    name: nocbrain
EOF

# Create deployment files
cat > deployments/backend.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nocbrain-backend
  namespace: nocbrain
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nocbrain-backend
  template:
    metadata:
      labels:
        app: nocbrain-backend
    spec:
      containers:
      - name: backend
        image: nocbrain/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: nocbrain-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: nocbrain-config
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: nocbrain-backend-service
  namespace: nocbrain
spec:
  selector:
    app: nocbrain-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
EOF

cd ..

# Create GitHub Actions workflow
echo "🔄 Creating GitHub Actions workflow..."
mkdir -p .github/workflows

cat > .github/workflows/ci-cd.yml << 'EOF'
name: NOCbRAIN CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest
    
    - name: Run linting
      run: |
        cd backend
        black --check .
        isort --check-only .
        flake8 .

  test-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm test
    
    - name: Run linting
      run: |
        cd frontend
        npm run lint

  build-and-deploy:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push backend
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        push: true
        tags: nocbrain/backend:latest
    
    - name: Build and push frontend
      uses: docker/build-push-action@v5
      with:
        context: ./frontend
        push: true
        tags: nocbrain/frontend:latest
EOF

# Create environment files
echo "🔧 Creating environment configuration..."
cat > .env.example << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://nocbrain:nocbrain@localhost:5432/nocbrain

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=4320

# External APIs
OPENAI_API_KEY=your-openai-api-key

# Vault Configuration
VAULT_URL=http://localhost:8200
VAULT_TOKEN=your-vault-token

# Monitoring
PROMETHEUS_PORT=9090

# Development
DEBUG=True
LOG_LEVEL=INFO
EOF

# Create security configuration
echo "🔒 Creating security configuration..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
build/
dist/

# Kubernetes secrets
secrets/
*.key
*.crt
*.pem

# Temporary files
tmp/
temp/
EOF

# Create documentation
echo "📚 Creating documentation..."
cat > docs/README.md << 'EOF'
# NOCbRAIN Documentation

## API Documentation
- [REST API Reference](api.md)
- [WebSocket API](websocket-api.md)
- [Authentication](authentication.md)

## User Guides
- [Getting Started](user-guide/getting-started.md)
- [Network Monitoring](user-guide/network-monitoring.md)
- [Security Analysis](user-guide/security-analysis.md)
- [Infrastructure Management](user-guide/infrastructure.md)

## Developer Guides
- [Development Setup](developer-guide/setup.md)
- [Architecture Overview](developer-guide/architecture.md)
- [Contributing Guidelines](developer-guide/contributing.md)
- [Testing Guide](developer-guide/testing.md)

## Security
- [Security Overview](security/overview.md)
- [Threat Model](security/threat-model.md)
- [Security Best Practices](security/best-practices.md)

## Knowledge Base
- [Network Protocols](wiki/network-protocols.md)
- [Security Threats](wiki/security-threats.md)
- [Troubleshooting](wiki/troubleshooting.md)
- [Best Practices](wiki/best-practices.md)
EOF

# Create scripts directory
echo "📜 Creating utility scripts..."
cd scripts

cat > setup.sh << 'EOF'
#!/bin/bash
# NOCbRAIN Setup Script

echo "🚀 Setting up NOCbRAIN development environment..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Setup frontend
echo "⚛️ Setting up React frontend..."
cd frontend
npm install
cd ..

# Setup environment
echo "🔧 Setting up environment..."
cp .env.example .env

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo "✅ Setup complete!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 Grafana: http://localhost:3001"
echo "📈 Prometheus: http://localhost:9090"
EOF

chmod +x setup.sh

cat > deploy.sh << 'EOF'
#!/bin/bash
# NOCbRAIN Deployment Script

ENVIRONMENT=${1:-development}
NAMESPACE="nocbrain"

echo "🚀 Deploying NOCbRAIN to $ENVIRONMENT..."

# Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
kubectl apply -f k8s/configmaps/ -n $NAMESPACE
kubectl apply -f k8s/secrets/ -n $NAMESPACE

# Deploy applications
kubectl apply -f k8s/deployments/ -n $NAMESPACE
kubectl apply -f k8s/services/ -n $NAMESPACE

# Wait for deployments
kubectl wait --for=condition=available --timeout=300s deployment/nocbrain-backend -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/nocbrain-frontend -n $NAMESPACE

echo "✅ Deployment complete!"
echo "🌐 Access the application at: http://your-domain.com"
EOF

chmod +x deploy.sh

cd ..

# Create LICENSE
echo "📄 Creating MIT License..."
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024 NOCbRAIN Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND PURPOSE. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create contributing guidelines
cat > CONTRIBUTING.md << 'EOF'
# Contributing to NOCbRAIN

We welcome contributions to NOCbRAIN! This document provides guidelines for contributors.

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## Development Guidelines

### Code Style
- Python: Follow PEP 8, use Black and isort
- TypeScript: Follow ESLint rules, use Prettier
- Write meaningful commit messages
- Add tests for new features

### Testing
- Write unit tests for all new code
- Ensure all tests pass before submitting PR
- Maintain test coverage above 80%

### Documentation
- Update documentation for new features
- Add inline comments for complex logic
- Keep API documentation up to date

## Security

For security vulnerabilities, please email security@nocbrain.org instead of opening a public issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
EOF

echo "✅ NOCbRAIN project structure created successfully!"
echo ""
echo "🚀 Next steps:"
echo "1. Copy and run the setup script: ./scripts/setup.sh"
echo "2. Configure your environment variables in .env"
echo "3. Start development: docker-compose up"
echo "4. Access the application at http://localhost:3000"
echo ""
echo "📚 Documentation: ./docs/README.md"
echo "🤝 Contributing: ./CONTRIBUTING.md"
echo "🔒 License: ./LICENSE"
