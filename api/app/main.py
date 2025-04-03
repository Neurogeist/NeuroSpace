from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime
import uuid
from typing import Dict, Any
from .models.prompt import PromptRequest, PromptResponse
from .services.blockchain import BlockchainService
from .services.ipfs import IPFSService
from .services.llm import LLMService
from .core.config import get_settings
from .core.rate_limit import RateLimitMiddleware
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NeuroChain API",
    description="API for decentralized prompt submission and AI-generated responses",
    version="1.0.0"
)

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Address"
            response.headers["Access-Control-Allow-Credentials"] = "false"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response

        # Handle actual requests
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Address"
        response.headers["Access-Control-Allow-Credentials"] = "false"
        return response

# Add custom CORS middleware first
app.add_middleware(CustomCORSMiddleware)

# Add rate limiting middleware after CORS
app.add_middleware(RateLimitMiddleware)

# Initialize services
settings = get_settings()
llm_service = LLMService()
blockchain_service = BlockchainService()
ipfs_service = IPFSService()

# Request tracking
request_stats: Dict[str, Any] = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "average_response_time": 0
}

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics and handle errors."""
    start_time = time.time()
    request_stats["total_requests"] += 1
    
    try:
        response = await call_next(request)
        request_stats["successful_requests"] += 1
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except HTTPException as e:
        # Re-raise HTTP exceptions without modification
        raise e
    except Exception as e:
        request_stats["failed_requests"] += 1
        logger.error(f"Unhandled exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        response_time = time.time() - start_time
        request_stats["average_response_time"] = (
            (request_stats["average_response_time"] * (request_stats["total_requests"] - 1) + response_time)
            / request_stats["total_requests"]
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check service health
        services_status = {
            "llm": llm_service.model is not None,
            "blockchain": blockchain_service.web3 is not None,
            "ipfs": ipfs_service.client is not None
        }
        
        return {
            "status": "healthy",
            "services": services_status,
            "stats": request_stats
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@app.post("/prompts", response_model=PromptResponse)
async def submit_prompt(
    request: PromptRequest,
    x_user_address: str = Header(..., alias="X-User-Address")
):
    """Submit a prompt for processing."""
    try:
        logger.info(f"Processing prompt from user {x_user_address}")
        
        # Generate response using LLM
        response = await llm_service.generate_response(request.prompt)
        logger.info("Response generated successfully")
        
        # Upload to IPFS
        ipfs_data = {
            "prompt": request.prompt,
            "response": response,
            "timestamp": request.timestamp,
            "user_address": x_user_address
        }
        ipfs_result = await ipfs_service.upload_to_ipfs(ipfs_data)
        ipfs_cid = ipfs_result["Hash"]  # The hash is in the "Hash" field
        logger.info(f"Content uploaded to IPFS: {ipfs_cid}")
        
        # Submit to blockchain
        hash_result = blockchain_service.hash_prompt(
            request.prompt,
            response,
            request.timestamp,
            x_user_address
        )
        signature = blockchain_service.submit_hash(hash_result)
        logger.info(f"Hash submitted to blockchain: {signature}")
        
        return PromptResponse(
            response=response,
            ipfs_cid=ipfs_cid,
            signature=signature,
            timestamp=datetime.utcnow(),
            user_address=x_user_address
        )
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process prompt: {str(e)}"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "error": str(exc)
        }
    )

@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """Get prompt metadata by ID."""
    if prompt_id not in prompts:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompts[prompt_id] 