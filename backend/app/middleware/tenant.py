"""
NOCbRAIN Tenant Middleware
FastAPI middleware for multi-tenant isolation
"""

import uuid
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate tenant context"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract tenant ID from header
        tenant_id = self._extract_tenant_id(request)
        
        # Validate tenant ID
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Tenant-ID header is required"
            )
        
        try:
            # Validate UUID format
            uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant ID format"
            )
        
        # Add tenant context to request state
        request.state.tenant_id = tenant_id
        request.state.tenant_context = {
            "tenant_id": tenant_id,
            "is_global": tenant_id == "global"  # Special case for global knowledge
        }
        
        # Log tenant access
        logger.info(f"Request from tenant: {tenant_id}")
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request headers"""
        # Try X-Tenant-ID header first
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if tenant_id:
            return tenant_id
        
        # For development, allow tenant_id query parameter
        if request.query_params.get("tenant_id"):
            return request.query_params.get("tenant_id")
        
        # For system operations, allow "global" tenant
        if request.url.path.startswith("/api/v1/system/") or \
           request.url.path.startswith("/health") or \
           request.url.path.startswith("/api/docs"):
            return "global"
        
        return None


def get_tenant_id(request: Request) -> str:
    """Get tenant ID from request context"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
    return request.state.tenant_id


def get_tenant_context(request: Request) -> dict:
    """Get full tenant context from request"""
    if not hasattr(request.state, "tenant_context"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found"
        )
    return request.state.tenant_context
