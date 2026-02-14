from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import logging
import asyncio

from app.core.config import settings
from app.core.database import init_db
from app.api.router import api_router
from app.core.logging import setup_logging
from app.core.logic.reasoning_engine import reasoning_engine
from app.core.logic.knowledge_manager import knowledge_manager
from app.middleware.tenant import TenantMiddleware
from app.core.rate_limiter import RateLimitMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NOCbRAIN backend...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized successfully")
    
    # Initialize global knowledge collection
    try:
        await knowledge_manager.initialize_collection("global")
        logger.info("Global knowledge collection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize global knowledge collection: {e}")
    
    # Start reasoning engine
    try:
        await reasoning_engine.start()
        logger.info("Reasoning engine started successfully")
    except Exception as e:
        logger.error(f"Failed to start reasoning engine: {e}")
    
    logger.info("NOCbRAIN backend startup completed")
    yield
    
    # Shutdown
    logger.info("Shutting down NOCbRAIN backend...")
    try:
        await reasoning_engine.stop()
        logger.info("Reasoning engine stopped")
    except Exception as e:
        logger.error(f"Failed to stop reasoning engine: {e}")
    logger.info("NOCbRAIN backend shutdown completed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Network Operations Center Assistant - Comprehensive network monitoring, security analysis, and infrastructure management with multi-tenant RAG-powered intelligence",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add rate limiting middleware (before tenant middleware)
app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL)

# Add tenant middleware
app.add_middleware(TenantMiddleware)

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
    """Health check endpoint"""
    try:
        # Get component statuses
        reasoning_stats = await reasoning_engine.get_stats()
        global_stats = await knowledge_manager.get_tenant_stats("global")
        
        return {
            "status": "healthy",
            "service": "NOCbRAIN",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "multi_tenant": True,
            "components": {
                "reasoning_engine": {
                    "is_running": reasoning_stats.get("is_running", False),
                    "total_processed": reasoning_stats.get("total_processed", 0)
                },
                "knowledge_manager": {
                    "global_documents": global_stats.get("total_documents", 0),
                    "global_collection": global_stats.get("collection_name", "unknown")
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "NOCbRAIN",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NOCbRAIN - AI Network Operations Center Assistant",
        "version": settings.VERSION,
        "description": "Multi-tenant RAG-powered network monitoring and security analysis",
        "docs": "/api/docs",
        "features": [
            "Multi-tenant architecture with strict isolation",
            "Real-time log analysis with AI",
            "Knowledge base with RAG and global knowledge",
            "Security pattern matching",
            "Automated NOC action plans",
            "Multi-protocol collectors (SNMP, SSH)",
            "Threat detection and response"
        ],
        "security": {
            "tenant_isolation": "Strict vector and database isolation",
            "data_encryption": "AES-256 at rest and TLS 1.3 in transit",
            "access_control": "JWT-based authentication with RBAC"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
