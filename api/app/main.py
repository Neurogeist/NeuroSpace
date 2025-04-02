from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
from typing import Dict
from .models.prompt import PromptRequest, PromptResponse
from .services.blockchain import BlockchainService
from .services.ipfs import IPFSService
from .services.llm import LLMService
from .core.config import get_settings

app = FastAPI(title="NeuroChain API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
blockchain_service = BlockchainService()
ipfs_service = IPFSService()
llm_service = LLMService()

# In-memory storage for development
prompts: Dict[str, Dict] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/prompts", response_model=PromptResponse)
async def submit_prompt(request: PromptRequest):
    """Submit a prompt and get an AI-generated response."""
    try:
        # Generate response using LLM
        response = await llm_service.generate_response(request.prompt)
        
        # Upload to IPFS
        ipfs_data = {
            "prompt": request.prompt,
            "response": response,
            "timestamp": request.timestamp,
            "user_address": request.user_address
        }
        ipfs_result = await ipfs_service.upload_to_ipfs(ipfs_data)
        ipfs_cid = ipfs_result["IpfsHash"]
        
        # Submit to blockchain
        hash_result = blockchain_service.hash_prompt(
            request.prompt,
            response,
            request.timestamp,
            request.user_address
        )
        signature = blockchain_service.submit_hash(hash_result)
        
        return PromptResponse(
            response=response,
            ipfs_cid=ipfs_cid,
            signature=signature
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """Get prompt metadata by ID."""
    if prompt_id not in prompts:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompts[prompt_id] 