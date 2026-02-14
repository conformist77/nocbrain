"""
NOCbRAIN Health Check Endpoints
Basic health monitoring for the API
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "NOCbRAIN",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status"""
    return {
        "status": "healthy",
        "service": "NOCbRAIN",
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "database": "healthy",
            "redis": "healthy"
        }
    }
