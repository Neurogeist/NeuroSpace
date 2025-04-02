import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from ..core.config import get_settings
from ..models.prompt import PromptMetadata

class IPFSService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.PINATA_API_KEY
        self.api_secret = settings.PINATA_API_SECRET
        self.jwt_token = settings.PINATA_JWT
        self.base_url = "https://api.pinata.cloud"

    async def upload_to_ipfs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload data to IPFS via Pinata."""
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/pinning/pinJSONToIPFS",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"IPFS upload failed: {str(e)}")

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