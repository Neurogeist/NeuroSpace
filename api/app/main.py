from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional
from .models.prompt import PromptRequest, PromptResponse, SessionResponse
from .services.blockchain import BlockchainService
from .services.ipfs import IPFSService
from .services.llm import LLMService
from .core.config import get_settings
from .core.rate_limit import RateLimitMiddleware
from .services.chat_session import ChatSessionService
from .utils.verifiability import generate_verification_hash
import logging
import time
import os
import re
import ipaddress
from fastapi import BackgroundTasks
from .services.model_registry import ModelRegistry
from pydantic import BaseModel
from .services.payment import PaymentService

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
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Address, X-Source"
            response.headers["Access-Control-Allow-Credentials"] = "false"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response

        # Handle actual requests
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Address, X-Source"
        response.headers["Access-Control-Allow-Credentials"] = "false"
        return response

# Add custom CORS middleware first
app.add_middleware(CustomCORSMiddleware)

# Initialize services
settings = get_settings()
chat_session_service = ChatSessionService()
llm_service = LLMService(chat_session_service)
blockchain_service = BlockchainService()
ipfs_service = IPFSService()
model_registry = ModelRegistry()
payment_service = PaymentService()

# Request tracking
request_stats: Dict[str, Any] = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "average_response_time": 0
}

# Temporarily disable rate limiting
# app.add_middleware(RateLimitMiddleware)

# Add request tracking middleware second
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track API requests and log them."""
    try:
        # Skip tracking for excluded endpoints (exact matches)
        excluded_endpoints = {
            "/health",
            "/signer",
            "/verify",
            "/",  # Frontend root
            "/favicon.ico",  # Favicon
            "/api-docs",  # Swagger UI
            "/redoc",  # ReDoc
            "/openapi.json"  # OpenAPI schema
        }
        
        # Skip tracking for static files
        excluded_extensions = {
            ".js",
            ".css",
            ".html",
            ".ico",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot"
        }
        
        # Skip tracking for excluded endpoints
        if request.url.path in excluded_endpoints:
            return await call_next(request)
            
        # Skip tracking for static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)
            
        # Skip tracking for file extensions
        if any(request.url.path.endswith(ext) for ext in excluded_extensions):
            return await call_next(request)
            
        # Skip tracking for API documentation
        if request.url.path.startswith("/api-docs") or request.url.path.startswith("/redoc"):
            return await call_next(request)
            
        # Track the request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log the request
        logger.info(f"Request: {request.method} {request.url.path} - Processed in {process_time:.2f}s")
        
        return response
        
    except Exception as e:
        logger.error(f"Error tracking request: {str(e)}")
        raise

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

class PromptRequest(BaseModel):
    prompt: str
    model: str
    user_address: str
    session_id: Optional[str] = None

@app.post("/submit_prompt")
async def submit_prompt(request: PromptRequest):
    """Submit a prompt and get a response."""
    try:
        # Verify payment before processing
        try:
            if not payment_service.verify_payment(request.session_id or "new", request.user_address):
                raise HTTPException(status_code=402, detail="Payment required")
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            # For testing, allow the request to proceed
            # In production, you should raise the HTTPException
            pass
        
        # Get the active session or create a new one
        session_id = request.session_id or str(uuid.uuid4())
        if not chat_session_service.get_session(session_id):
            chat_session_service.create_session(session_id, wallet_address=request.user_address)
        
        # Get model details from registry
        model_config = model_registry.get_model_config(request.model)
        if not model_config:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not found")
        
        # Generate response using LLM with model's default parameters
        llm_response = await llm_service.generate_response(
            model_id=request.model,
            prompt=request.prompt,
            system_prompt=None,
            temperature=model_config.temperature,
            max_tokens=model_config.max_new_tokens,  # Use max_new_tokens instead of max_tokens
            session_id=session_id
        )
        
        # Extract the response text
        response = llm_response.get('response', '') if isinstance(llm_response, dict) else llm_response
        
        # Create verification hash
        verification_hash = llm_service.create_verification_hash(request.prompt, response)
        
        # Sign the verification hash
        signature = blockchain_service.sign_message(verification_hash)
        
        # Store hash on blockchain
        blockchain_result = await blockchain_service.submit_to_blockchain(verification_hash)
        transaction_hash = blockchain_result.get('transaction_hash')
        
        # Upload to IPFS
        ipfs_data = {
            "prompt": request.prompt,
            "response": response,
            "model_name": request.model,
            "model_id": model_config.model_id,
            "timestamp": datetime.utcnow().isoformat(),
            "verification_hash": verification_hash,
            "signature": signature,
            "transaction_hash": transaction_hash
        }
        ipfs_cid = await ipfs_service.upload_json(ipfs_data)
        
        # Store in chat session
        await chat_session_service.add_message(
            session_id=session_id,
            role="user",
            content=request.prompt,
            model_name=request.model,
            model_id=model_config.model_id,
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "model_name": request.model,
                "model_id": model_config.model_id,
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_new_tokens,  # Use max_new_tokens here too
                "ipfs_cid": ipfs_cid,
                "verification_hash": verification_hash,
                "signature": signature,
                "transaction_hash": transaction_hash
            }
        )
        
        await chat_session_service.add_message(
            session_id=session_id,
            role="assistant",
            content=response,
            model_name=request.model,
            model_id=model_config.model_id,
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "model_name": request.model,
                "model_id": model_config.model_id,
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_new_tokens,  # And here
                "ipfs_cid": ipfs_cid,
                "verification_hash": verification_hash,
                "signature": signature,
                "transaction_hash": transaction_hash
            }
        )
        
        return {
            "response": response,
            "session_id": session_id,
            "model_id": model_config.model_id,
            "metadata": {
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_new_tokens,  # And here
                "top_p": model_config.top_p,
                "do_sample": model_config.do_sample,
                "num_beams": model_config.num_beams,
                "early_stopping": model_config.early_stopping,
                "verification_hash": verification_hash,
                "signature": signature,
                "ipfs_cid": ipfs_cid,
                "transaction_hash": transaction_hash
            }
        }
        
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

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    try:
        messages = chat_session_service.get_session_messages(session_id)
        if not messages:
            # Return an empty session instead of raising an error
            return {
                "session_id": session_id,
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

        messages_dict_list = [message.dict(by_alias=True, exclude_none=False) for message in messages]

        return {
            "session_id": session_id,
            "messages": messages_dict_list,
            "created_at": messages[0].timestamp if messages else datetime.utcnow(),
            "updated_at": messages[-1].timestamp if messages else datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        # Return an empty session instead of raising an error
        return {
            "session_id": session_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

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

class VerificationRequest(BaseModel):
    verification_hash: str
    signature: str
    expected_address: Optional[str] = None

class VerificationResponse(BaseModel):
    is_valid: bool
    recovered_address: str
    expected_address: str
    match: bool

@app.get("/signer")
async def get_signer():
    """Get the backend's current signing address."""
    try:
        return {
            "signer_address": blockchain_service.account.address
        }
    except Exception as e:
        logger.error(f"Error getting signer address: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify", response_model=VerificationResponse)
async def verify_signature(request: VerificationRequest):
    """Verify a signature against a verification hash."""
    try:
        # Get the expected address (either provided or use backend's address)
        expected_address = request.expected_address or blockchain_service.account.address
        
        # Verify the signature and recover the address
        recovered_address = blockchain_service.verify_signature(
            request.verification_hash,
            request.signature
        )
        
        # Check if the recovered address matches the expected address
        match = recovered_address.lower() == expected_address.lower()
        
        return VerificationResponse(
            is_valid=True,  # If we got here, the signature is valid
            recovered_address=recovered_address,
            expected_address=expected_address,
            match=match
        )
        
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/verify/hash/{hash}")
async def verify_hash(hash: str):
    """Check if a hash has been stored on-chain."""
    try:
        # Get hash info from blockchain
        hash_info = await blockchain_service.get_hash_info(hash)
        
        return {
            "exists": hash_info["exists"],
            "info": hash_info if hash_info["exists"] else None
        }
        
    except Exception as e:
        logger.error(f"Error verifying hash: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 