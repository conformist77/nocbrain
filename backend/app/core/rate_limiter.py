"""
NOCbRAIN Rate Limiter
Redis-based global rate limiting for API abuse prevention
"""

import redis.asyncio as redis
import json
import time
import asyncio
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisRateLimiter:
    """Redis-based rate limiter with sliding window algorithm"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self.redis_client is None:
            async with self._lock:
                if self.redis_client is None:
                    self.redis_client = redis.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        retry_on_timeout=True,
                        socket_keepalive=True,
                        socket_keepalive_options={},
                        health_check_interval=30
                    )
        return self.redis_client
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Rate limit key (e.g., IP address, API key, tenant ID)
            limit: Maximum requests allowed
            window: Time window in seconds
            tenant_id: Optional tenant ID for tenant-specific limits
        
        Returns:
            Dict with allowed status and metadata
        """
        try:
            client = await self._get_redis_client()
            
            # Create composite key with tenant if provided
            if tenant_id:
                composite_key = f"rate_limit:{tenant_id}:{key}"
            else:
                composite_key = f"rate_limit:{key}"
            
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use Redis pipeline for atomic operations
            pipe = client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(composite_key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(composite_key)
            
            # Add current request
            pipe.zadd(composite_key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(composite_key, window)
            
            results = await pipe.execute()
            
            current_requests = results[1]
            
            is_allowed = current_requests < limit
            remaining = max(0, limit - current_requests - 1)
            reset_time = current_time + window
            
            return {
                "allowed": is_allowed,
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "current_requests": current_requests,
                "window": window
            }
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if rate limiter fails
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - 1,
                "reset_time": int(time.time()) + window,
                "current_requests": 0,
                "window": window
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(
        self, 
        app,
        default_limits: Dict[str, Dict[str, int]] = None,
        redis_url: str = None
    ):
        super().__init__(app)
        self.limiter = RedisRateLimiter(redis_url)
        
        # Default rate limits per endpoint type
        self.default_limits = default_limits or {
            "global": {"limit": 1000, "window": 60},  # 1000 requests per minute globally
            "tenant": {"limit": 500, "window": 60},   # 500 requests per minute per tenant
            "ip": {"limit": 100, "window": 60},      # 100 requests per minute per IP
            "auth": {"limit": 10, "window": 60},      # 10 auth requests per minute
            "ai": {"limit": 50, "window": 60},        # 50 AI requests per minute
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting"""
        
        # Skip health checks and static files
        if request.url.path in ["/health", "/health/detailed", "/metrics"]:
            return await call_next(request)
        
        # Extract identifiers
        client_ip = self._get_client_ip(request)
        tenant_id = getattr(request.state, 'tenant_id', None)
        api_key = request.headers.get("X-API-Key")
        
        # Determine rate limit strategy based on endpoint
        path = request.url.path.lower()
        limit_key = self._get_limit_key(path)
        
        limits = self.default_limits.get(limit_key, self.default_limits["global"])
        
        # Apply multiple rate limits (global, tenant, IP)
        rate_checks = []
        
        # Global rate limit
        rate_checks.append(
            self.limiter.is_allowed("global", limits["limit"], limits["window"])
        )
        
        # Tenant-specific rate limit
        if tenant_id:
            rate_checks.append(
                self.limiter.is_allowed(
                    f"tenant:{tenant_id}", 
                    self.default_limits["tenant"]["limit"], 
                    self.default_limits["tenant"]["window"],
                    tenant_id
                )
            )
        
        # IP-based rate limit
        rate_checks.append(
            self.limiter.is_allowed(
                f"ip:{client_ip}", 
                self.default_limits["ip"]["limit"], 
                self.default_limits["ip"]["window"]
            )
        )
        
        # API key rate limit
        if api_key:
            rate_checks.append(
                self.limiter.is_allowed(
                    f"api_key:{api_key}", 
                    self.default_limits["auth"]["limit"], 
                    self.default_limits["auth"]["window"]
                )
            )
        
        # Wait for all rate limit checks
        check_results = await asyncio.gather(*rate_checks, return_exceptions=True)
        
        # Check if any rate limit was exceeded
        for result in check_results:
            if isinstance(result, Exception):
                logger.error(f"Rate limit check error: {result}")
                continue
                
            if not result["allowed"]:
                logger.warning(
                    f"Rate limit exceeded for {client_ip} "
                    f"(tenant: {tenant_id}, path: {path})"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": result["limit"],
                        "remaining": result["remaining"],
                        "reset_time": result["reset_time"],
                        "window": result["window"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(result["limit"]),
                        "X-RateLimit-Remaining": str(result["remaining"]),
                        "X-RateLimit-Reset": str(result["reset_time"]),
                        "Retry-After": str(result["window"])
                    }
                )
        
        # Add rate limit headers to successful responses
        response = await call_next(request)
        
        # Add rate limit info from the first check
        if check_results and not isinstance(check_results[0], Exception):
            result = check_results[0]
            response.headers["X-RateLimit-Limit"] = str(result["limit"])
            response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
            response.headers["X-RateLimit-Reset"] = str(result["reset_time"])
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_limit_key(self, path: str) -> str:
        """Determine rate limit key based on request path"""
        if "/auth" in path:
            return "auth"
        elif "/api/v1/tenant" in path and ("/analyze" in path or "/query" in path):
            return "ai"
        elif "/api/v1/tenant" in path:
            return "tenant"
        else:
            return "global"


# Global rate limiter instance
rate_limiter = RedisRateLimiter()


async def check_rate_limit(
    key: str, 
    limit: int, 
    window: int,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Utility function to check rate limit manually
    
    Args:
        key: Rate limit key
        limit: Maximum requests allowed
        window: Time window in seconds
        tenant_id: Optional tenant ID
    
    Returns:
        Dict with rate limit information
    """
    return await rate_limiter.is_allowed(key, limit, window, tenant_id)
