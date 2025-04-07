import os
import logging
import requests
from typing import Optional
from ..core.config import get_settings
from .model_registry import ModelConfig

settings = get_settings()
logger = logging.getLogger(__name__)

class RemoteLLMClient:
    """Client for remote LLM inference."""
    
    def __init__(self):
        self.together_base_url = "https://api.together.xyz/v1/completions"
        self.replicate_base_url = "https://api.replicate.com/v1/predictions"
    
    def generate(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using a remote LLM provider."""
        if config.provider == "together":
            return self._generate_together(model_id, prompt, system_prompt, config)
        elif config.provider == "replicate":
            return self._generate_replicate(model_id, prompt, system_prompt, config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    def _generate_together(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using Together.ai."""
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {config.api_key_env}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Format the prompt with system message if provided
        formatted_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "model": model_id,
            "prompt": formatted_prompt,
            "max_tokens": config.max_new_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stop": ["<|endoftext|>", "<|im_end|>"]
        }
        
        try:
            response = requests.post(
                self.together_base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["text"].strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Together.ai API: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _generate_replicate(self, model_id: str, prompt: str, system_prompt: Optional[str], config: ModelConfig) -> str:
        """Generate a response using Replicate."""
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {config.api_key_env}")
        
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        
        # Format the prompt with system message if provided
        formatted_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "version": model_id,  # Replicate uses version IDs
            "input": {
                "prompt": formatted_prompt,
                "max_length": config.max_new_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p
            }
        }
        
        try:
            # Create prediction
            response = requests.post(
                self.replicate_base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            prediction = response.json()
            
            # Poll for completion
            while True:
                status_response = requests.get(
                    f"{self.replicate_base_url}/{prediction['id']}",
                    headers=headers,
                    timeout=60
                )
                status_response.raise_for_status()
                status = status_response.json()
                
                if status["status"] == "succeeded":
                    return status["output"].strip()
                elif status["status"] in ["failed", "canceled"]:
                    raise Exception(f"Prediction failed: {status.get('error', 'Unknown error')}")
                
                # Wait before polling again
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Replicate API: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}") 