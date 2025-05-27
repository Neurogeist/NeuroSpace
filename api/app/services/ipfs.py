import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from api.app.core.config import settings
import logging
import aiohttp
from ..core.config import get_settings
import os
from pathlib import Path
from aiohttp import ClientSession

logger = logging.getLogger(__name__)
settings = get_settings()

class IPFSService:
    """Service for interacting with IPFS."""
    
    def __init__(self, ipfs_gateway: str = "https://ipfs.io/ipfs/"):
        self.ipfs_gateway = ipfs_gateway.rstrip('/')
        self.settings = get_settings()
        self.provider = self.settings.IPFS_PROVIDER
        self.api_url = self.settings.ipfs_api_url
        self.gateway_url = self.settings.ipfs_gateway_url
        
        if self.provider == "pinata":
            if not self.settings.PINATA_API_KEY or not self.settings.PINATA_API_SECRET:
                raise ValueError("Pinata API key and secret are required when using Pinata provider")
            self.headers = {
                "pinata_api_key": self.settings.PINATA_API_KEY,
                "pinata_secret_api_key": self.settings.PINATA_API_SECRET
            }
    
    async def add_content(self, content: str) -> str:
        """Add content to IPFS and return the CID."""
        try:
            logger.info("Starting IPFS content upload")
            if self.provider == "pinata":
                logger.info("Using Pinata provider")
                return await self._add_to_pinata(content)
            else:
                logger.info("Using local IPFS node")
                return await self._add_to_local(content)
        except Exception as e:
            logger.error(f"Error adding content to IPFS: {str(e)}")
            raise
    
    async def _add_to_pinata(self, content: str) -> str:
        """Add content to Pinata."""
        try:
            logger.info("Creating temporary file for Pinata upload")
            # Create a temporary file
            temp_file = Path("temp_content.txt")
            temp_file.write_text(content)
            
            # Prepare the request
            files = {
                'file': ('content.txt', open(temp_file, 'rb'))
            }
            
            logger.info("Uploading to Pinata")
            # Make the request
            response = requests.post(
                f"{self.api_url}/pinning/pinFileToIPFS",
                headers=self.headers,
                files=files
            )
            
            # Clean up the temporary file
            temp_file.unlink()
            logger.info("Temporary file cleaned up")
            
            if response.status_code != 200:
                logger.error(f"Pinata upload failed: {response.text}")
                raise Exception(f"Failed to pin file to IPFS: {response.text}")
            
            ipfs_hash = response.json()["IpfsHash"]
            logger.info(f"Successfully uploaded to Pinata with hash: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error adding content to Pinata: {str(e)}")
            raise
    
    async def _add_to_local(self, content: str) -> str:
        """Add content to local IPFS node."""
        try:
            logger.info("Creating temporary file for local IPFS upload")
            # Create a temporary file
            temp_file = Path("temp_content.txt")
            temp_file.write_text(content)
            
            # Prepare the request
            files = {
                'file': ('content.txt', open(temp_file, 'rb'))
            }
            
            logger.info("Uploading to local IPFS node")
            # Make the request
            response = requests.post(
                f"{self.api_url}/add",
                files=files
            )
            
            # Clean up the temporary file
            temp_file.unlink()
            logger.info("Temporary file cleaned up")
            
            if response.status_code != 200:
                logger.error(f"Local IPFS upload failed: {response.text}")
                raise Exception(f"Failed to add file to IPFS: {response.text}")
            
            ipfs_hash = response.json()["Hash"]
            logger.info(f"Successfully uploaded to local IPFS with hash: {ipfs_hash}")
            return ipfs_hash
            
        except Exception as e:
            logger.error(f"Error adding content to local IPFS: {str(e)}")
            raise
    
    async def get_content(self, cid: str) -> str:
        """Get content from IPFS by CID."""
        try:
            response = requests.get(f"{self.gateway_url}/ipfs/{cid}")
            if response.status_code != 200:
                raise Exception(f"Failed to get content from IPFS: {response.text}")
            return response.text
        except Exception as e:
            logger.error(f"Error getting content from IPFS: {str(e)}")
            raise
    
    def get_gateway_url(self, cid: str) -> str:
        """Get the gateway URL for a CID."""
        return f"{self.gateway_url}/ipfs/{cid}"

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
        """
        Upload JSON data to IPFS.
        
        Args:
            data: Dictionary to upload
            
        Returns:
            str: IPFS hash (CID) of the uploaded data
            
        Raises:
            Exception: If upload fails
        """
        try:
            json_data = json.dumps(data)

            if self.provider == "pinata":
                url = f"{self.api_url}/pinning/pinFileToIPFS"
                form = aiohttp.FormData()
                form.add_field("file", json_data, filename="data.json", content_type="application/json")

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=form, headers=self.headers) as resp:
                        if resp.status != 200:
                            raise Exception(f"Pinata upload failed: {await resp.text()}")
                        response_data = await resp.json()
                        logger.info(f"✅ Uploaded to Pinata: {response_data['IpfsHash']}")
                        return response_data["IpfsHash"]

            else:
                # Fallback to local IPFS node
                response_data = await self._make_request(
                    "add",
                    files={"file": ("data.json", json_data, "application/json")}
                )
                logger.info(f"✅ Uploaded to Local IPFS: {response_data['Hash']}")
                return response_data["Hash"]

        except Exception as e:
            logger.error(f"Error uploading JSON to IPFS: {str(e)}")
            raise Exception(f"Failed to upload JSON to IPFS: {str(e)}")

    async def download_json(self, cid: str) -> Dict[str, Any]:
        """
        Download and parse JSON data from IPFS.
        
        Args:
            cid: IPFS content identifier (hash)
            
        Returns:
            Dict[str, Any]: Parsed JSON data
            
        Raises:
            Exception: If download or parsing fails
        """
        try:
            # First try the gateway
            try:
                response = requests.get(f"{self.gateway_url}/ipfs/{cid}")
                if response.status_code == 200:
                    return json.loads(response.text)
            except Exception as e:
                logger.debug(f"Gateway download failed, trying API: {str(e)}")
            
            # Fallback to API endpoint
            response = requests.post(f"{self.api_url}/cat", params={'arg': cid})
            response.raise_for_status()
            
            # Parse the JSON content
            content = json.loads(response.text)
            logger.info(f"Data retrieved from IPFS with hash: {cid}")
            return content
            
        except Exception as e:
            logger.error(f"Error downloading JSON from IPFS: {str(e)}")
            raise Exception(f"Failed to download JSON from IPFS: {str(e)}")

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

    async def get_file(self, cid: str) -> bytes:
        """
        Download raw file data from IPFS.
        
        Args:
            cid: IPFS content identifier (hash)
            
        Returns:
            bytes: Raw file data
            
        Raises:
            Exception: If download fails
        """
        try:
            async with ClientSession() as session:
                async with session.get(f"{self.ipfs_gateway}/{cid}") as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download from IPFS: {response.status}")
                    return await response.read()
                    
        except Exception as e:
            logger.error(f"Error downloading file from IPFS: {str(e)}")
            raise Exception(f"Failed to download file from IPFS: {str(e)}")

    async def close(self):
        """Close any open connections."""
        try:
            if hasattr(self, 'session') and self.session:
                await self.session.close()
            logger.info("IPFS service connections closed")
        except Exception as e:
            logger.error(f"Error closing IPFS connections: {str(e)}") 