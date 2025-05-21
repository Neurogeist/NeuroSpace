from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from functools import lru_cache
from ..core.config import get_settings
from huggingface_hub import hf_hub_download
from tqdm import tqdm
import os
from pydantic import BaseModel

settings = get_settings()
logger = logging.getLogger(__name__)

class ModelConfig(BaseModel):
    """Configuration for a model."""
    model_id: str
    system_prompt: str = "You are a helpful AI assistant. Answer questions accurately and concisely."
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    do_sample: bool = True
    num_beams: int = 1
    early_stopping: bool = False
    provider: str = "local"  # "local", "together", "replicate", or "openai"
    api_key_env: Optional[str] = None  # Environment variable name for API key

class ModelRegistry:
    """Registry for managing different language models."""
    
    def __init__(self):
        """Initialize the model registry."""
        # Get settings
        self.settings = get_settings()
        
        # Define available models with their configurations
        self.models = {
            "mixtral-8x7b-instruct": ModelConfig(
                model_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
                provider="together",
                api_key_env="TOGETHER_API_KEY",
                system_prompt="You are a helpful AI assistant. Format your responses using markdown for better readability. Use code blocks for code examples, bold for emphasis, and lists for structured information. Answer questions accurately and concisely.",
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=False
            ),
            "gemma-2-27b-it": ModelConfig(
                model_id="google/gemma-2-27b-it",
                provider="together",
                api_key_env="TOGETHER_API_KEY",
                system_prompt="You are a helpful AI assistant. Format your responses using markdown for better readability. Use code blocks for code examples, bold for emphasis, and lists for structured information. Answer questions accurately and concisely.",
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=False
            ),
            "gpt-4-turbo": ModelConfig(
                model_id="gpt-4-0125-preview",
                provider="openai",
                api_key_env="OPENAI_API_KEY",
                system_prompt="You are a helpful AI assistant. Format your responses using markdown for better readability. Use code blocks for code examples, bold for emphasis, and lists for structured information. Answer questions accurately and concisely.",
                max_new_tokens=4096,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=False
            ),
            "gpt-3.5-turbo": ModelConfig(
                model_id="gpt-3.5-turbo-0125",
                provider="openai",
                api_key_env="OPENAI_API_KEY",
                system_prompt="You are a helpful AI assistant. Format your responses using markdown for better readability. Use code blocks for code examples, bold for emphasis, and lists for structured information. Answer questions accurately and concisely.",
                max_new_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=False
            )
        }
        
        # Determine device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
            
        # Override with environment variable if set
        if self.settings.MODEL_REGISTRY_DEVICE != "auto":
            self.device = self.settings.MODEL_REGISTRY_DEVICE
            
        logger.info(f"Using device: {self.device}")
        
        # Set memory limits from settings
        self.max_memory_cpu = self.settings.MODEL_REGISTRY_MAX_MEMORY_CPU
        self.max_memory_gpu = self.settings.MODEL_REGISTRY_MAX_MEMORY_GPU
        
        # Set up max_memory dictionary based on device
        if self.device == "cuda":
            self.max_memory = {0: self.max_memory_gpu, "cpu": self.max_memory_cpu}
        else:
            self.max_memory = {"cpu": self.max_memory_cpu}
        
        # Set environment variables for better performance
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
        os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "600"  # 10 minutes timeout
        os.environ["TRANSFORMERS_CACHE"] = os.path.expanduser("~/.cache/huggingface")
        
        # Initialize model cache
        self._loaded_models = {}
    
    def get_available_models(self) -> Dict[str, str]:
        """Get a list of available models with their display names."""
        return {name: config.model_id for name, config in self.models.items()}
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get the configuration for a specific model."""
        return self.models.get(model_name)
    
    def get_model_and_tokenizer(self, model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """Get a model and tokenizer by name."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
            
        config = self.models[model_name]
        
        # Check if model is already loaded
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]
        
        try:
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                config.model_id,
                trust_remote_code=True,
                use_fast=True
            )
            
            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                config.model_id,
                device_map=self.device,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                max_memory=self.max_memory
            )
            
            # Cache the loaded model
            self._loaded_models[model_name] = (model, tokenizer)
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise Exception(f"Failed to load model: {str(e)}")
    
    def clear_cache(self):
        """Clear the model and tokenizer cache."""
        self._loaded_models.clear() 