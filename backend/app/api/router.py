from fastapi import APIRouter

from app.api.endpoints import auth, users, network, security, infrastructure, monitoring, knowledge, core_engine, tenant

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Network monitoring endpoints
api_router.include_router(network.router, prefix="/network", tags=["network"])

# Security analysis endpoints
api_router.include_router(security.router, prefix="/security", tags=["security"])

# Infrastructure management endpoints
api_router.include_router(infrastructure.router, prefix="/infrastructure", tags=["infrastructure"])

# Monitoring endpoints
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# Knowledge base endpoints
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])

# Core engine endpoints (RAG and AI reasoning)
api_router.include_router(core_engine.router, prefix="/core", tags=["core-engine"])

# Tenant management endpoints (multi-tenant)
api_router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
