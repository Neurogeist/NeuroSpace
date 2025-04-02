import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from ..core.config import get_settings
from ..models.prompt import PromptMetadata

settings = get_settings()

class IPFSService:
    def __init__(self):
        self.api_url = "https://api.pinata.cloud"
        self.headers = {
            "Authorization": f"Bearer {settings.PINATA_JWT}",
            "Content-Type": "application/json"
        }
        
    def upload_prompt(self, metadata: Dict[str, Any]) -> str:
        """Upload prompt and response metadata to IPFS via Pinata."""
        # Upload to Pinata
        response = requests.post(
            f"{self.api_url}/pinning/pinJSONToIPFS",
            headers=self.headers,
            json=metadata
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload to IPFS: {response.text}")
            
        return response.json()["IpfsHash"] 