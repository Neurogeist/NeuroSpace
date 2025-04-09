import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from api.app.core.config import settings
import logging
import aiohttp

logger = logging.getLogger(__name__)

class IPFSService:
    def __init__(self):
        self.api_url = settings.IPFS_API_URL
        logger.info(f"IPFS service initialized with API URL: {self.api_url}")

    async def upload_to_ipfs(self, prompt: str, response: str, metadata: Dict[str, Any]) -> str:
        """
        Upload prompt, response, and metadata to IPFS.
        
        Args:
            prompt: The user's prompt
            response: The model's response
            metadata: Model metadata including model name, temperature, etc.
            
        Returns:
            str: IPFS CID of the uploaded content
        """
        try:
            content = {
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata
            }
            
            # Convert content to JSON string
            content_json = json.dumps(content)
            
            # Upload to IPFS
            files = {
                'file': ('content.json', content_json)
            }
            
            response = requests.post(f"{self.api_url}/add", files=files)
            response.raise_for_status()
            
            # Extract the IPFS hash from the response
            result = response.json()
            logger.info(f"Data uploaded to IPFS with hash: {result['Hash']}")
            return result['Hash']
            
        except Exception as e:
            logger.error(f"Failed to upload to IPFS: {str(e)}")
            raise Exception(f"IPFS upload failed: {str(e)}")

    async def get_from_ipfs(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Retrieve data from IPFS.
        
        Args:
            ipfs_hash: IPFS hash of the data to retrieve
            
        Returns:
            Dictionary containing the retrieved data
        """
        try:
            # Retrieve from IPFS
            response = requests.post(f"{self.api_url}/cat", params={'arg': ipfs_hash})
            response.raise_for_status()
            
            # Parse the JSON content
            content = json.loads(response.text)
            logger.info(f"Data retrieved from IPFS with hash: {ipfs_hash}")
            return content
        except Exception as e:
            logger.error(f"Failed to retrieve from IPFS: {str(e)}")
            raise Exception(f"IPFS retrieval failed: {str(e)}")

    async def upload_json(self, data: Dict[str, Any]) -> str:
        """Upload JSON data to IPFS."""
        try:
            # Convert data to JSON string
            json_data = json.dumps(data)
            
            # Upload to IPFS
            response = await self._make_request(
                "add",
                files={"file": ("data.json", json_data, "application/json")}
            )
            
            # Return the hash
            return response["Hash"]
            
        except Exception as e:
            logger.error(f"Error uploading JSON to IPFS: {str(e)}")
            raise Exception(f"Failed to upload JSON to IPFS: {str(e)}")

    async def _make_request(self, endpoint: str, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the IPFS API."""
        try:
            # Build the URL
            url = f"{self.api_url}/{endpoint}"
            
            # Make the request
            async with aiohttp.ClientSession() as session:
                if files:
                    # For file uploads, use multipart/form-data
                    data = aiohttp.FormData()
                    for key, value in files.items():
                        data.add_field(key, value[1], filename=value[0], content_type=value[2] if len(value) > 2 else None)
                    
                    async with session.post(url, data=data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise ValueError(f"IPFS API error: {error_text}")
                        
                        return await response.json()
                else:
                    # For other requests, use application/json
                    async with session.post(url) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise ValueError(f"IPFS API error: {error_text}")
                        
                        return await response.json()
                        
        except Exception as e:
            logger.error(f"Error making IPFS request: {str(e)}")
            raise Exception(f"Failed to make IPFS request: {str(e)}") 