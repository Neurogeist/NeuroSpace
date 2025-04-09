from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import time
import logging

logger = logging.getLogger(__name__)

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
    def __init__(self, app, rate_limit: int = 60, window: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window = window
        self.requests: Dict[str, Dict[str, float]] = {}
        
        # Endpoints that don't require X-User-Address header
        self.excluded_endpoints = {
            "/health",
            "/signer",
            "/verify"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded endpoints
        if request.url.path in self.excluded_endpoints:
            return await call_next(request)
            
        # Get user address from header
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
        
        # Clean up old requests
        current_time = time.time()
        self._cleanup_requests(current_time)
        
        # Check rate limit
        if not self._check_rate_limit(user_address, current_time):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {self.window} seconds.",
                    "rate_limit": self.rate_limit,
                    "window": self.window
                }
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _cleanup_requests(self, current_time: float):
        """Remove old requests outside the time window."""
        for address in list(self.requests.keys()):
            self.requests[address] = {
                timestamp for timestamp in self.requests[address]
                if current_time - timestamp < self.window
            }
            if not self.requests[address]:
                del self.requests[address]
    
    def _check_rate_limit(self, address: str, current_time: float) -> bool:
        """Check if the request is within the rate limit."""
        if address not in self.requests:
            self.requests[address] = set()
        
        # Add current request timestamp
        self.requests[address].add(current_time)
        
        # Check if we're over the limit
        return len(self.requests[address]) <= self.rate_limit 