from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PromptRequest(BaseModel):
    prompt: str
    user_address: Optional[str] = None

class PromptResponse(BaseModel):
    prompt_id: str
    prompt: str
    response: str
    ipfs_cid: str
    timestamp: datetime
    transaction_hash: str
    user_address: Optional[str] = None

class PromptMetadata(BaseModel):
    prompt: str
    response: str
    timestamp: datetime
    user_address: Optional[str] = None 