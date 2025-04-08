from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime
import uuid
from typing import Dict, Any, List
from .models.prompt import PromptRequest, PromptResponse, SessionResponse
from .services.blockchain import BlockchainService
from .services.ipfs import IPFSService
from .services.llm import LLMService
from .core.config import get_settings
from .core.rate_limit import RateLimitMiddleware
from .services.chat_session import ChatSessionService
import logging
import time
import os
import re
import ipaddress

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
chat_session_service = ChatSessionService()

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

@app.post("/prompt", response_model=PromptResponse)
async def submit_prompt(request: PromptRequest):
    """Submit a prompt and get a response."""
    try:
        # Get or create session
        session_id = chat_session_service.create_session(request.session_id)
        
        # Get chat history for context (before adding current message)
        chat_history = chat_session_service.format_session_history(session_id)
        
        # Generate response with the specified model and chat history
        result = llm_service.generate_response(
            prompt=request.prompt,
            model_name=request.model_name,
            chat_history=chat_history
        )
        
        # Create metadata for IPFS storage
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "model_name": result["model_name"],
            "model_id": result["model_id"],
            "temperature": llm_service.config.temperature,
            "max_tokens": llm_service.config.max_new_tokens
        }
        
        # Store on IPFS
        ipfs_cid = await ipfs_service.upload_to_ipfs(
            prompt=request.prompt,
            response=result["response"],
            metadata=metadata
        )
        
        # Create hash of prompt data
        prompt_hash = blockchain_service.hash_prompt(
            prompt=request.prompt,
            response=result["response"],
            timestamp=metadata["timestamp"]
        )
        
        # Store hash on blockchain
        transaction_hash = await blockchain_service.submit_hash(prompt_hash)
        
        # Add user message to session with metadata
        chat_session_service.add_message(
            session_id=session_id,
            role="user",
            content=request.prompt,
            model_name=result["model_name"],
            model_id=result["model_id"],
            ipfs_cid=ipfs_cid,
            transaction_hash=transaction_hash
        )
        
        # Add assistant message to session
        chat_session_service.add_message(
            session_id=session_id,
            role="assistant",
            content=result["response"],
            model_name=result["model_name"],
            model_id=result["model_id"],
            ipfs_cid=ipfs_cid,
            transaction_hash=transaction_hash
        )
        
        # Update metadata with blockchain info
        metadata.update({
            "ipfs_cid": ipfs_cid,
            "transaction_hash": transaction_hash
        })
        
        response_data = PromptResponse(
            response=result["response"],
            model_name=result["model_name"],
            model_id=result["model_id"],
            session_id=session_id,
            ipfs_cid=ipfs_cid,
            transaction_hash=transaction_hash,
            metadata=metadata
        )
        
        return JSONResponse(content=response_data.dict(by_alias=True))
        
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """Get a list of available models."""
    try:
        models = llm_service.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a chat session by ID."""
    try:
        session = chat_session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse.from_chat_session(session)
        
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions", response_model=List[SessionResponse])
async def get_all_sessions():
    """Get all chat sessions."""
    try:
        sessions = chat_session_service.get_all_sessions()
        return [SessionResponse.from_chat_session(session) for session in sessions]
    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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