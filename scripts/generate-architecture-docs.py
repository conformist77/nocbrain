#!/usr/bin/env python3
"""
NOCbRAIN Architecture Documentation Generator
Generates comprehensive architecture documentation for developers
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

def generate_architecture_docs(output_path):
    """Generate architecture documentation"""
    
    architecture_content = f"""# NOCbRAIN Architecture Documentation

## Overview

NOCbRAIN is an AI-powered Network Operations Center Assistant designed with a modern, scalable microservices architecture.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI/ML Engine  │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (PyTorch)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   Database      │    │   Monitoring    │
         │              │   (PostgreSQL)  │    │   (Prometheus)  │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │    │     Cache       │    │   Log Storage   │
│                 │    │    (Redis)      │    │   (Elasticsearch)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

#### Frontend Layer
- **Technology**: React 18 + TypeScript
- **UI Framework**: Ant Design
- **State Management**: Zustand + React Query
- **Real-time**: WebSocket connections
- **Routing**: React Router

#### Backend Layer
- **API Framework**: FastAPI
- **Language**: Python 3.11+
- **Authentication**: JWT + OAuth2
- **Database ORM**: SQLAlchemy
- **Task Queue**: Celery + Redis

#### Data Layer
- **Primary Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Time Series**: InfluxDB (planned)
- **Search**: Elasticsearch
- **Object Storage**: MinIO/S3

#### Monitoring Layer
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Logging**: ELK Stack
- **Tracing**: Jaeger
- **Alerting**: AlertManager

## Module Architecture

### Core Modules

#### Authentication Module
```python
app/
├── core/
│   ├── auth.py          # JWT authentication
│   ├── security.py      # Security utilities
│   └── permissions.py   # RBAC implementation
```

**Key Components:**
- JWT token management
- Role-based access control
- Permission validation
- Session management

#### Network Monitoring Module
```python
app/
├── modules/
│   └── network/
│       ├── service.py   # Network monitoring service
│       ├── models.py    # Network device models
│       └── agents.py    # SNMP agents
```

**Key Components:**
- SNMP device discovery
- Network topology mapping
- Performance metrics collection
- Real-time monitoring

#### Security Analysis Module
```python
app/
├── modules/
│   └── security/
│       ├── service.py   # Security analysis service
│       ├── siem.py      # SIEM integration
│       └── threats.py   # Threat detection
```

**Key Components:**
- SIEM integration
- Threat detection algorithms
- Security event correlation
- Incident response automation

#### Infrastructure Module
```python
app/
├── modules/
│   └── infrastructure/
│       ├── service.py   # Infrastructure service
│       ├── vmware.py    # VMware integration
│       └── cloud.py     # Cloud provider APIs
```

**Key Components:**
- VMware ESX management
- Cloud platform integration
- Resource utilization monitoring
- Auto-scaling capabilities

## Data Flow Architecture

### Request Flow
```
User Request → Frontend → Backend API → Business Logic → Database → Response
     ↓              ↓           ↓              ↓           ↓
  Authentication  Validation  Processing   Persistence  Response
```

### Real-time Data Flow
```
Monitoring Agent → WebSocket → Frontend → Dashboard Update
       ↓               ↓           ↓           ↓
   Metrics Collection   Real-time API   State Update   UI Refresh
```

### AI/ML Processing Flow
```
Data Input → Preprocessing → ML Model → Analysis → Alert Generation
     ↓           ↓            ↓          ↓           ↓
   Collection   Normalization  Inference  Scoring   Notification
```

## Security Architecture

### Authentication Flow
```
User Login → Credentials Validation → JWT Generation → Token Storage → API Access
      ↓               ↓                   ↓              ↓           ↓
   Username/Password   Hash Verification   Cryptographic   Secure Storage   Bearer Token
```

### Authorization Model
```
User → Roles → Permissions → Resources
  ↓      ↓         ↓           ↓
Identity  Groups  Actions    Data Access
```

### Data Encryption
- **In Transit**: TLS 1.3
- **At Rest**: AES-256
- **Key Management**: HashiCorp Vault
- **Agent Communication**: Fernet Encryption

## Deployment Architecture

### Container Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   Container     │    │   Container     │    │   Container     │
│   (Nginx)       │    │   (Python)      │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Kubernetes Architecture
```
Namespace: nocbrain
├── Deployments
│   ├── frontend (3 replicas)
│   ├── backend (3 replicas)
│   └── agents (auto-scaling)
├── Services
│   ├── frontend-service
│   ├── backend-service
│   └── database-service
└── ConfigMaps
    ├── app-config
    └── monitoring-config
```

## Scalability Architecture

### Horizontal Scaling
- **Frontend**: Load balancer + multiple instances
- **Backend**: Auto-scaling based on CPU/memory
- **Database**: Read replicas + sharding
- **Cache**: Redis Cluster

### Vertical Scaling
- **Resource Allocation**: Dynamic resource requests
- **Performance Monitoring**: Real-time metrics
- **Capacity Planning**: Predictive scaling

## Integration Architecture

### External Integrations
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SIEM Systems  │    │   Cloud APIs    │    │   Monitoring    │
│   (Splunk)      │◄──►│   (AWS/Azure)   │◄──►│   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NOCbRAIN      │    │   NOCbRAIN      │    │   NOCbRAIN      │
│   Backend       │    │   Backend       │    │   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### API Gateway Pattern
```
External Request → API Gateway → Service Mesh → Backend Services
       ↓               ↓              ↓              ↓
    Authentication   Rate Limiting   Service Discovery  Load Balancing
```

## Development Architecture

### Code Organization
```
nocbrain/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core functionality
│   │   ├── models/       # Database models
│   │   ├── modules/      # Business modules
│   │   └── services/     # Business services
│   ├── tests/            # Test suite
│   └── migrations/       # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── utils/        # Utility functions
│   └── tests/            # Frontend tests
└── docs/                 # Documentation
```

### Development Workflow
```
Feature Branch → PR Review → CI/CD Pipeline → Staging → Production
      ↓              ↓              ↓              ↓           ↓
   Development    Code Review    Automated    Integration   Release
                                     Testing
```

## Monitoring Architecture

### Observability Stack
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Infrastructure│    │   Business      │
│   Metrics       │    │   Metrics       │    │   Metrics       │
│   (Custom)      │    │   (Node Exporter)│    │   (KPIs)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │   Grafana       │    │   AlertManager  │
│   (Collection)  │    │   (Visualization)│    │   (Alerting)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Logging Architecture
```
Application Logs → Log Aggregation → Processing → Storage → Visualization
        ↓                ↓              ↓          ↓           ↓
   Structured Logs    Fluentd/FluentBit  Parsing    Elasticsearch  Kibana
```

## Performance Architecture

### Caching Strategy
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   CDN           │    │   Application   │
│   Cache         │    │   Cache         │    │   Cache         │
│   (LocalStorage)│    │   (CloudFlare)   │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Database Optimization
- **Indexing Strategy**: Optimized query performance
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Analyzed and optimized queries
- **Read Replicas**: Distributed read operations

## Testing Architecture

### Test Pyramid
```
┌─────────────────┐
│   E2E Tests     │  ← Few, Slow, High Value
│   (Playwright)  │
└─────────────────┘
┌─────────────────┐
│   Integration   │  ← Medium, Medium Speed
│   Tests         │
│   (pytest)      │
└─────────────────┘
┌─────────────────┐
│   Unit Tests    │  ← Many, Fast, Low Value
│   (pytest)      │
└─────────────────┘
```

## Future Architecture Considerations

### Microservices Evolution
- **Service Mesh**: Istio integration
- **Event Sourcing**: Event-driven architecture
- **CQRS**: Command Query Responsibility Segregation
- **Saga Pattern**: Distributed transactions

### AI/ML Enhancement
- **Model Serving**: TensorFlow Serving
- **Feature Store**: MLflow integration
- **Model Monitoring**: Drift detection
- **A/B Testing**: Experimentation framework

---

*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Architecture Version: 1.0.0*
"""

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(architecture_content)
    
    print(f"Architecture documentation generated: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate NOCbRAIN architecture documentation')
    parser.add_argument('--output', required=True, help='Output file path')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    generate_architecture_docs(args.output)

if __name__ == '__main__':
    main()
