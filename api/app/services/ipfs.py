import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from ..core.config import get_settings
from ..models.prompt import PromptMetadata
import logging

logger = logging.getLogger(__name__)

class IPFSService:
    def __init__(self):
        settings = get_settings()
        self.api_url = settings.IPFS_API_URL
        logger.info(f"IPFS service initialized with API URL: {self.api_url}")

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

    async def upload_to_ipfs(self, data: dict) -> dict:
        """
        Upload data to IPFS.
        
        Args:
            data: Dictionary containing the data to upload
            
        Returns:
            Dictionary containing the IPFS hash and other metadata
        """
        try:
            # Convert datetime objects to ISO format strings
            data_copy = data.copy()
            for key, value in data_copy.items():
                if isinstance(value, datetime):
                    data_copy[key] = value.isoformat()
            
            # Convert data to JSON string
            json_data = json.dumps(data_copy)
            
            # Upload to IPFS
            response = requests.post(
                f"{self.api_url}/add",
                files={"file": json_data}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to upload to IPFS: {response.text}")
            
            result = response.json()
            logger.info(f"Data uploaded to IPFS with hash: {result['Hash']}")
            return result
        except Exception as e:
            logger.error(f"Failed to upload to IPFS: {str(e)}")
            raise Exception(f"IPFS upload failed: {str(e)}")

    async def get_from_ipfs(self, ipfs_hash: str) -> dict:
        """
        Retrieve data from IPFS.
        
        Args:
            ipfs_hash: IPFS hash of the data to retrieve
            
        Returns:
            Dictionary containing the retrieved data
        """
        try:
            # Retrieve from IPFS
            response = requests.post(
                f"{self.api_url}/cat",
                params={"arg": ipfs_hash}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve from IPFS: {response.text}")
            
            data = response.json()
            logger.info(f"Data retrieved from IPFS with hash: {ipfs_hash}")
            return data
        except Exception as e:
            logger.error(f"Failed to retrieve from IPFS: {str(e)}")
            raise Exception(f"IPFS retrieval failed: {str(e)}") 