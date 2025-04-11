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

# Initialize services
settings = get_settings()
chat_session_service = ChatSessionService()
llm_service = LLMService(chat_session_service)
blockchain_service = BlockchainService()
ipfs_service = IPFSService()
model_registry = ModelRegistry()

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

@app.post("/prompt")
async def submit_prompt(prompt: PromptRequest, background_tasks: BackgroundTasks):
    """Submit a prompt and get a response."""
    try:
        # Get the active session or create a new one
        session_id = prompt.session_id or str(uuid.uuid4())
        if not chat_session_service.get_session(session_id):
            chat_session_service.create_session(session_id)
        
        # Get model details from registry
        model_config = model_registry.get_model_config(prompt.model_name)
        if not model_config:
            raise HTTPException(status_code=400, detail=f"Model {prompt.model_name} not found")
        
        # Generate response using LLM
        response = await llm_service.generate_response(
            model_id=prompt.model_name,
            prompt=prompt.prompt,
            system_prompt=prompt.system_prompt,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
            session_id=session_id
        )
        
        # Clean the response
        cleaned_response = response["response"]  # The response is already cleaned in generate_response
        
        # Create verification hash
        verification_hash = llm_service.create_verification_hash(prompt.prompt, cleaned_response)
        
        # Sign the verification hash
        signature = blockchain_service.sign_message(verification_hash)
        
        # Upload to IPFS
        ipfs_data = {
            "prompt": prompt.prompt,
            "response": cleaned_response,
            "model_name": prompt.model_name,
            "model_id": model_config.model_id,
            "timestamp": datetime.utcnow().isoformat(),
            "verification_hash": verification_hash,
            "signature": signature
        }
        ipfs_cid = await ipfs_service.upload_json(ipfs_data)
        
        # Submit to blockchain
        blockchain_result = await blockchain_service.submit_to_blockchain(verification_hash)
        transaction_hash = blockchain_result['transaction_hash']  # Extract just the hash string
        
        # Add messages to chat session
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "model_name": prompt.model_name,
            "model_id": model_config.model_id,
            "temperature": prompt.temperature,
            "max_tokens": prompt.max_tokens,
            "ipfs_cid": ipfs_cid,
            "transaction_hash": transaction_hash,  # Use the extracted hash string
            "verification_hash": verification_hash,
            "signature": signature
        }

        logger.info(f"Metadata timestamp: {metadata['timestamp']}")

        
        await chat_session_service.add_message(
            session_id=session_id,
            role="user",
            content=prompt.prompt,
            model_name=prompt.model_name,
            model_id=model_config.model_id,
            metadata=metadata
        )
        
        await chat_session_service.add_message(
            session_id=session_id,
            role="assistant",
            content=cleaned_response,
            model_name=prompt.model_name,
            model_id=model_config.model_id,
            metadata=metadata
        )
        
        return {
            "response": cleaned_response,
            "session_id": session_id,
            "metadata": metadata
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
            raise HTTPException(status_code=404, detail="Session not found")

        messages_dict_list = [message.dict(by_alias=True, exclude_none=False) for message in messages]

        return {
            "session_id": session_id,
            "messages": messages_dict_list,
            "created_at": messages[0].timestamp if messages else datetime.utcnow(),
            "updated_at": messages[-1].timestamp if messages else datetime.utcnow()
        }
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