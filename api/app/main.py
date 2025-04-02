from fastapi import FastAPI, HTTPException
from datetime import datetime
import uuid
from typing import Dict
from .models.prompt import PromptRequest, PromptResponse
from .services.blockchain import BlockchainService
from .services.ipfs import IPFSService
from .services.llm import LLMService
from .core.config import get_settings

app = FastAPI(title="Web3 Prompt API")
settings = get_settings()

# Initialize services
blockchain_service = BlockchainService()
ipfs_service = IPFSService()
llm_service = LLMService()

# In-memory storage for development
prompts: Dict[str, Dict] = {}

@app.post("/prompts", response_model=PromptResponse)
async def create_prompt(request: PromptRequest):
    """Create a new prompt, generate a response, and store everything on-chain."""
    try:
        # Generate unique prompt ID
        prompt_id = str(uuid.uuid4())
        
        # Generate response using LLM
        response = llm_service.generate_response(request.prompt)
        
        # Create metadata with both prompt and response
        timestamp = datetime.utcnow()
        metadata = {
            "prompt": request.prompt,
            "response": response,
            "timestamp": timestamp.isoformat(),
            "user_address": request.user_address
        }
        
        # Upload to IPFS
        ipfs_cid = ipfs_service.upload_prompt(metadata)
        
        # Create hash and submit to blockchain
        prompt_hash = blockchain_service.hash_prompt(
            request.prompt,
            response,
            timestamp.isoformat(),
            request.user_address
        )
        transaction_hash = blockchain_service.submit_hash(prompt_hash)
        
        # Store metadata
        prompt_data = {
            "prompt_id": prompt_id,
            "prompt": request.prompt,
            "response": response,
            "ipfs_cid": ipfs_cid,
            "timestamp": timestamp,
            "transaction_hash": transaction_hash,
            "user_address": request.user_address
        }
        prompts[prompt_id] = prompt_data
        
        return PromptResponse(**prompt_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """Get prompt metadata by ID."""
    if prompt_id not in prompts:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompts[prompt_id] 