"""
NOCbRAIN Health Check Endpoints
Comprehensive health monitoring for API and system components
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
import asyncio
import time
import psutil
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.logic.reasoning_engine import reasoning_engine
from app.core.logic.knowledge_manager import knowledge_manager
from app.core.rate_limiter import rate_limiter

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "NOCbRAIN",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - psutil.boot_time()
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status"""
    start_time = time.time()
    
    # Check all components concurrently
    tasks = {
        "database": check_database_health(),
        "redis": check_redis_health(),
        "qdrant": check_qdrant_health(),
        "reasoning_engine": check_reasoning_engine_health(),
        "knowledge_manager": check_knowledge_manager_health(),
        "system": check_system_health()
    }
    
    # Wait for all health checks
    results = {}
    for component, task in tasks.items():
        try:
            results[component] = await asyncio.wait_for(task, timeout=5.0)
        except asyncio.TimeoutError:
            results[component] = {
                "status": "unhealthy",
                "error": "Health check timeout",
                "response_time": 5.0
            }
        except Exception as e:
            results[component] = {
                "status": "unhealthy",
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    # Determine overall status
    overall_status = "healthy"
    unhealthy_components = [name for name, health in results.items() if health.get("status") != "healthy"]
    
    if unhealthy_components:
        if len(unhealthy_components) == 1:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
    
    total_response_time = time.time() - start_time
    
    return {
        "status": overall_status,
        "service": "NOCbRAIN",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
        "response_time": total_response_time,
        "components": results,
        "summary": {
            "total_components": len(results),
            "healthy_components": len([r for r in results.values() if r.get("status") == "healthy"]),
            "unhealthy_components": len(unhealthy_components),
            "unhealthy_list": unhealthy_components
        },
        "system_info": {
            "uptime": time.time() - psutil.boot_time(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": {
                "percent": psutil.disk_usage('/').percent if hasattr(psutil.disk_usage('/'), 'percent') else 0
            }
        }
    }


async def check_database_health() -> Dict[str, Any]:
    """Check PostgreSQL database health"""
    start_time = time.time()
    
    try:
        # Try to get a database session
        from app.core.database import get_db_session
        
        async with get_db_session() as db:
            # Simple health query
            result = await db.execute("SELECT 1 as health_check")
            await result.fetchone()
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "database": settings.DATABASE_URL.split('@')[-1].split('/')[0] if '@' in settings.DATABASE_URL else "unknown",
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": time.time() - start_time,
            "database": settings.DATABASE_URL.split('@')[-1].split('/')[0] if '@' in settings.DATABASE_URL else "unknown",
            "checked_at": datetime.now().isoformat()
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health"""
    start_time = time.time()
    
    try:
        # Test Redis connection
        redis_client = await rate_limiter._get_redis_client()
        
        # Ping Redis
        pong = await redis_client.ping()
        response_time = time.time() - start_time
        
        # Get Redis info
        info = await redis_client.info()
        
        return {
            "status": "healthy" if pong else "unhealthy",
            "response_time": response_time,
            "redis_info": {
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            },
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": time.time() - start_time,
            "checked_at": datetime.now().isoformat()
        }


async def check_qdrant_health() -> Dict[str, Any]:
    """Check Qdrant vector database health"""
    start_time = time.time()
    
    try:
        # Test Qdrant connection
        global_stats = await knowledge_manager.get_tenant_stats("global")
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "qdrant_info": {
                "global_documents": global_stats.get("total_documents", 0),
                "collection_name": global_stats.get("collection_name", "unknown"),
                "vector_size": global_stats.get("vector_size", "unknown")
            },
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": time.time() - start_time,
            "checked_at": datetime.now().isoformat()
        }


async def check_reasoning_engine_health() -> Dict[str, Any]:
    """Check AI reasoning engine health"""
    start_time = time.time()
    
    try:
        # Test reasoning engine
        stats = await reasoning_engine.get_stats()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if stats.get("is_running", False) else "unhealthy",
            "response_time": response_time,
            "engine_info": {
                "is_running": stats.get("is_running", False),
                "total_processed": stats.get("total_processed", 0),
                "queue_size": stats.get("queue_size", 0),
                "last_processed": stats.get("last_processed")
            },
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": time.time() - start_time,
            "checked_at": datetime.now().isoformat()
        }


async def check_knowledge_manager_health() -> Dict[str, Any]:
    """Check knowledge manager health"""
    start_time = time.time()
    
    try:
        # Test knowledge manager
        global_stats = await knowledge_manager.get_tenant_stats("global")
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "manager_info": {
                "global_documents": global_stats.get("total_documents", 0),
                "collection_status": "active",
                "last_indexed": global_stats.get("last_indexed")
            },
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": time.time() - start_time,
            "checked_at": datetime.now().isoformat()
        }


async def check_system_health() -> Dict[str, Any]:
    """Check system resources health"""
    start_time = time.time()
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine health based on thresholds
        cpu_status = "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
        memory_status = "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
        disk_status = "healthy" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
        
        overall_system_status = "healthy"
        if "warning" in [cpu_status, memory_status, disk_status]:
            overall_system_status = "warning"
        if "critical" in [cpu_status, memory_status, disk_status]:
            overall_system_status = "critical"
        
        response_time = time.time() - start_time
        
        return {
            "status": overall_system_status,
            "response_time": response_time,
            "system_info": {
                "cpu": {
                    "percent": cpu_percent,
                    "status": cpu_status,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "status": memory_status
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                    "status": disk_status
                },
                "uptime": time.time() - psutil.boot_time(),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": time.time() - start_time,
            "checked_at": datetime.now().isoformat()
        }


@router.get("/components/{component}")
async def component_health_check(component: str) -> Dict[str, Any]:
    """Health check for specific component"""
    component_checks = {
        "database": check_database_health,
        "redis": check_redis_health,
        "qdrant": check_qdrant_health,
        "reasoning_engine": check_reasoning_engine_health,
        "knowledge_manager": check_knowledge_manager_health,
        "system": check_system_health
    }
    
    if component not in component_checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component '{component}' not found. Available: {list(component_checks.keys())}"
        )
    
    try:
        result = await component_checks[component]()
        return result
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "component": component,
            "checked_at": datetime.now().isoformat()
        }
