from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import asyncio
import logging

from app.config import settings
from app.db import init_db
from app.api import auth, alerts, incidents
from app.services.zabbix_client import ZabbixClient
from app.services.correlation import CorrelationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NOCBrain v0.1")
    await init_db()
    
    # Start background tasks
    zabbix_client = ZabbixClient()
    correlation_engine = CorrelationEngine()
    
    # Start ingestion and correlation tasks
    ingestion_task = asyncio.create_task(zabbix_client.start_ingestion())
    correlation_task = asyncio.create_task(correlation_engine.start_correlation())
    
    yield
    
    # Shutdown
    ingestion_task.cancel()
    correlation_task.cancel()
    logger.info("NOCBrain v0.1 stopped")


app = FastAPI(
    title="NOCBrain v0.1",
    description="LLM-powered alert correlation system",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])


@app.get("/")
async def root():
    return {"message": "NOCBrain v0.1 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
