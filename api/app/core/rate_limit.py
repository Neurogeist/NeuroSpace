from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def _clean_old_requests(self, user_address: str):
        """Remove requests older than 1 minute."""
        now = time.time()
        self.requests[user_address] = [
            req_time for req_time in self.requests[user_address]
            if now - req_time < 60
        ]
    
    def check_rate_limit(self, user_address: str) -> Tuple[bool, int]:
        """
        Check if the user has exceeded the rate limit.
        Returns (is_allowed, remaining_requests)
        """
        now = time.time()
        
        # Initialize user's request history if not exists
        if user_address not in self.requests:
            self.requests[user_address] = []
        
        # Clean old requests
        self._clean_old_requests(user_address)
        
        # Check if user has exceeded rate limit
        if len(self.requests[user_address]) >= self.requests_per_minute:
            return False, 0
        
        # Add new request
        self.requests[user_address].append(now)
        
        # Calculate remaining requests
        remaining = self.requests_per_minute - len(self.requests[user_address])
        return True, remaining

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)
            
        # Get user address from request
        user_address = request.headers.get("X-User-Address")
        if not user_address:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing required header",
                    "message": "X-User-Address header is required for rate limiting",
                    "example": "X-User-Address: 0x1234567890123456789012345678901234567890"
                }
            )
        
        # Check rate limit
        is_allowed, remaining = self.rate_limiter.check_rate_limit(user_address)
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "You have exceeded the rate limit of 60 requests per minute",
                    "remaining_time": "60 seconds",
                    "retry_after": 60
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
        
        return response 