from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Set
import time
import logging
import redis
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Rate limit configurations
RATE_LIMIT_CONFIG = {
    "default": {"requests": 60, "window": 60},  # 60 requests per minute
    "/submit_prompt": {"requests": 30, "window": 60},  # 30 requests per minute
    "/rag/upload": {"requests": 10, "window": 60},  # 10 requests per minute
    "/rag/query": {"requests": 20, "window": 60},  # 20 requests per minute
    "/verify": {"requests": 300, "window": 60},  # 300 requests per minute for verify endpoint
}

class RateLimiter:
    def __init__(self):
        self.redis_client = None
        # Check for Railway Redis URL first, then fallback to individual config
        self.redis_url = os.getenv("REDIS_URL") or os.getenv("RAILWAY_REDIS_URL")
        self.use_redis = bool(self.redis_url)
        
        if self.use_redis:
            try:
                if self.redis_url:
                    # Use Railway's Redis URL if available
                    self.redis_client = redis.from_url(
                        self.redis_url,
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        retry_on_timeout=True
                    )
                else:
                    # Fallback to individual config
                    self.redis_client = redis.Redis(
                        host=os.getenv("REDIS_HOST", "localhost"),
                        port=int(os.getenv("REDIS_PORT", 6379)),
                        db=int(os.getenv("REDIS_DB", 0)),
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        retry_on_timeout=True
                    )
                
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Redis rate limiter initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {str(e)}")
                self.use_redis = False
                logger.info("ℹ️ Falling back to in-memory rate limiter")
        
        # Fallback to in-memory storage if Redis is not available
        if not self.use_redis:
            self.requests: Dict[str, Dict[str, Set[float]]] = {}
            logger.info("ℹ️ Using in-memory rate limiter")
    
    def _get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit configuration for a path."""
        config = RATE_LIMIT_CONFIG.get(path, RATE_LIMIT_CONFIG["default"])
        return config["requests"], config["window"]
    
    def _cleanup_requests(self, current_time: float, window: int):
        """Clean up expired rate limit data."""
        if self.use_redis:
            # Redis automatically handles expiration
            return
            
        for address in list(self.requests.keys()):
            for path in list(self.requests[address].keys()):
                self.requests[address][path] = {
                    timestamp for timestamp in self.requests[address][path]
                    if current_time - timestamp < window
                }
                if not self.requests[address][path]:
                    del self.requests[address][path]
            if not self.requests[address]:
                del self.requests[address]
    
    def check_rate_limit(self, address: str, path: str, current_time: float) -> Tuple[bool, int, int]:
        """
        Check if the request is within the rate limit.
        Returns (is_allowed, remaining_requests, reset_time)
        """
        requests, window = self._get_rate_limit(path)
        
        try:
            if self.use_redis:
                return self._check_redis_rate_limit(address, path, requests, window, current_time)
            else:
                return self._check_memory_rate_limit(address, path, requests, window, current_time)
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {str(e)}")
            # Fallback to in-memory if Redis fails
            if self.use_redis:
                logger.info("Falling back to in-memory rate limiting due to Redis error")
                self.use_redis = False
                self.requests = {}
                return self._check_memory_rate_limit(address, path, requests, window, current_time)
            raise
    
    def _check_redis_rate_limit(self, address: str, path: str, requests: int, window: int, current_time: float) -> Tuple[bool, int, int]:
        """Check rate limit using Redis."""
        key = f"rate_limit:{address}:{path}"
        
        # Get current count
        current = self.redis_client.get(key)
        if current is None:
            # First request
            self.redis_client.setex(key, window, 1)
            return True, requests - 1, int(current_time + window)
        
        current = int(current)
        if current >= requests:
            # Get TTL for reset time
            ttl = self.redis_client.ttl(key)
            return False, 0, int(current_time + ttl)
        
        # Increment counter
        self.redis_client.incr(key)
        return True, requests - current - 1, int(current_time + window)
    
    def _check_memory_rate_limit(self, address: str, path: str, requests: int, window: int, current_time: float) -> Tuple[bool, int, int]:
        """Check rate limit using in-memory storage."""
        if address not in self.requests:
            self.requests[address] = {}
        
        if path not in self.requests[address]:
            self.requests[address][path] = set()
        
        # Clean old requests
        self.requests[address][path] = {
            timestamp for timestamp in self.requests[address][path]
            if current_time - timestamp < window
        }
        
        # Check if over limit
        if len(self.requests[address][path]) >= requests:
            # Find oldest request to calculate reset time
            oldest = min(self.requests[address][path])
            reset_time = int(oldest + window)
            return False, 0, reset_time
        
        # Add current request
        self.requests[address][path].add(current_time)
        return True, requests - len(self.requests[address][path]), int(current_time + window)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        
        # Endpoints that don't require rate limiting
        self.excluded_endpoints = {
            "/health",
            "/signer",
            "/verify",
            "/",  # Frontend root
            "/static",  # Static files
            "/favicon.ico",  # Favicon
            "/api-docs",  # Swagger UI
            "/redoc",  # ReDoc
            "/openapi.json"  # OpenAPI schema
        }
        
        # File extensions that don't require rate limiting
        self.excluded_extensions = {
            ".js", ".css", ".html", ".ico", ".png", ".jpg", ".jpeg",
            ".gif", ".svg", ".woff", ".woff2", ".ttf", ".eot"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded endpoints
        if request.url.path in self.excluded_endpoints:
            return await call_next(request)

        # Skip static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)

        # Skip based on file extensions
        if any(request.url.path.endswith(ext) for ext in self.excluded_extensions):
            return await call_next(request)

        # Skip API documentation
        if request.url.path.startswith(("/api-docs", "/redoc")) or request.url.path == "/openapi.json":
            return await call_next(request)

        # Get identifier (wallet address or IP)
        identifier = request.headers.get("X-User-Address")
        if not identifier:
            # Fallback to IP address
            identifier = request.client.host if request.client else "unknown"
        
        try:
            # Check rate limit
            current_time = time.time()
            is_allowed, remaining, reset_time = self.rate_limiter.check_rate_limit(
                identifier, request.url.path, current_time
            )
            
            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_CONFIG.get(request.url.path, RATE_LIMIT_CONFIG["default"])["requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            if not is_allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again in {reset_time - int(current_time)} seconds.",
                        "rate_limit": RATE_LIMIT_CONFIG.get(request.url.path, RATE_LIMIT_CONFIG["default"])["requests"],
                        "window": RATE_LIMIT_CONFIG.get(request.url.path, RATE_LIMIT_CONFIG["default"])["window"],
                        "reset_time": reset_time
                    }
                )
            
            return response
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # If rate limiting fails, allow the request but log the error
            return await call_next(request) 