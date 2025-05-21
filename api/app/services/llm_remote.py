import os
import logging
import requests
import aiohttp
import asyncio
from typing import Optional
from ..core.config import get_settings
from .model_registry import ModelConfig
from openai import AsyncOpenAI

settings = get_settings()
logger = logging.getLogger(__name__)

class RemoteLLMClient:
    """Client for remote LLM inference."""
    
    def __init__(self):
        self.together_base_url = "https://api.together.xyz/v1/completions"
        self.replicate_base_url = "https://api.replicate.com/v1/predictions"
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def generate(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using a remote LLM provider."""
        if config.provider == "together":
            return await self._generate_together(model_id, prompt, system_prompt, config)
        elif config.provider == "replicate":
            return await self._generate_replicate(model_id, prompt, system_prompt, config)
        elif config.provider == "openai":
            return await self._generate_openai(model_id, prompt, system_prompt, config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def _generate_together(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using Together API."""
        try:
            # Get API key from environment
            api_key = os.getenv(config.api_key_env)
            if not api_key:
                raise ValueError(f"API key not found in environment variable {config.api_key_env}")
            
            # Prepare request data
            data = {
                "model": model_id,
                "prompt": prompt,
                "max_tokens": config.max_new_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": 50,
                "repetition_penalty": 1.1,
                "stop": ["</s>", "User:", "Assistant:"]
            }
            
            # Add system prompt if provided
            if system_prompt:
                data["system_prompt"] = system_prompt
            
            # Make request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.together_base_url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Together API error: {error_text}")
                    
                    result = await response.json()
                    return result["choices"][0]["text"].strip()
                    
        except Exception as e:
            logger.error(f"Error generating with Together: {str(e)}")
            raise
            
    async def _generate_replicate(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using Replicate API."""
        try:
            # Get API key from environment
            api_key = os.getenv(config.api_key_env)
            if not api_key:
                raise ValueError(f"API key not found in environment variable {config.api_key_env}")
            
            # Prepare request data
            data = {
                "version": model_id,
                "input": {
                    "prompt": prompt,
                    "max_length": config.max_new_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "repetition_penalty": 1.1,
                    "stop_sequences": ["</s>", "User:", "Assistant:"]
                }
            }
            
            # Add system prompt if provided
            if system_prompt:
                data["input"]["system_prompt"] = system_prompt
            
            # Make request
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Create prediction
                async with session.post(self.replicate_base_url, json=data, headers=headers) as response:
                    if response.status != 201:
                        error_text = await response.text()
                        raise ValueError(f"Replicate API error: {error_text}")
                    
                    result = await response.json()
                    prediction_id = result["id"]
                    
                    # Poll for completion
                    while True:
                        async with session.get(f"{self.replicate_base_url}/{prediction_id}", headers=headers) as status_response:
                            if status_response.status != 200:
                                error_text = await status_response.text()
                                raise ValueError(f"Replicate API error: {error_text}")
                            
                            status_result = await status_response.json()
                            if status_result["status"] == "succeeded":
                                return status_result["output"].strip()
                            elif status_result["status"] in ["failed", "canceled"]:
                                raise ValueError(f"Replicate prediction {status_result['status']}: {status_result.get('error', 'Unknown error')}")
                            
                            # Wait before polling again
                            await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Error generating with Replicate: {str(e)}")
            raise

    async def _generate_openai(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using OpenAI API."""
        try:
            # Get API key from environment
            api_key = os.getenv(config.api_key_env)
            if not api_key:
                raise ValueError(f"API key not found in environment variable {config.api_key_env}")
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Make request
            response = await self.openai_client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_new_tokens,
                top_p=config.top_p,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {str(e)}")
            raise 