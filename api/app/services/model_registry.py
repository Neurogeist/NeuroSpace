from typing import Dict, Any, Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from functools import lru_cache
from ..core.config import get_settings
from huggingface_hub import hf_hub_download
from tqdm import tqdm
import os

settings = get_settings()
logger = logging.getLogger(__name__)

class ModelConfig:
    """Configuration for a specific model."""
    def __init__(
        self,
        model_id: str,
        max_new_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        num_beams: int = 1,
        early_stopping: bool = True,
        system_prompt: str = "You are a helpful assistant. Be concise and clear.",
        is_gated: bool = False,
        local_files_only: bool = False
    ):
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.do_sample = do_sample
        self.num_beams = num_beams
        self.early_stopping = early_stopping
        self.system_prompt = system_prompt
        self.is_gated = is_gated
        self.local_files_only = local_files_only

class ModelRegistry:
    """Registry for managing different language models."""
    
    def __init__(self):
        # Define available models with their configurations
        self.models = {
            "tinyllama": ModelConfig(
                model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=True,
                system_prompt="You are a helpful assistant. Be concise and clear.",
                is_gated=False
            ),
            "mistral": ModelConfig(
                model_id="mistralai/Mistral-7B-Instruct-v0.2",
                max_new_tokens=150,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=True,
                system_prompt="You are a helpful assistant. Be concise and clear.",
                is_gated=True
            ),
            "phi": ModelConfig(
                model_id="microsoft/phi-2",
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_beams=1,
                early_stopping=True,
                system_prompt="You are a helpful assistant. Be concise and clear.",
                is_gated=False
            )
        }
        
        # Cache for loaded models and tokenizers
        self._model_cache = {}
        self._tokenizer_cache = {}
        
        # Determine device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        logger.info(f"Using device: {self.device}")
    
    def get_available_models(self) -> Dict[str, str]:
        """Get a list of available models with their display names."""
        return {name: config.model_id for name, config in self.models.items()}
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get the configuration for a specific model."""
        return self.models.get(model_name)
    
    @lru_cache(maxsize=10)
    def get_model_and_tokenizer(self, model_name: str) -> Tuple[Any, Any]:
        """Get or load a model and tokenizer by name."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found. Available models: {list(self.models.keys())}")
        
        config = self.models[model_name]
        
        # Check if model is already loaded
        if model_name in self._model_cache and model_name in self._tokenizer_cache:
            logger.info(f"Using cached model and tokenizer for {model_name}")
            return self._model_cache[model_name], self._tokenizer_cache[model_name]
        
        # Check if model is gated and token is available
        if config.is_gated and not settings.HUGGINGFACE_TOKEN:
            raise ValueError(
                f"Model '{model_name}' is a gated repository. "
                "Please set the HUGGINGFACE_TOKEN environment variable and ensure you have access to the model."
            )
        
        # Load model
        logger.info(f"Loading model {config.model_id} on {self.device}")
        try:
            # Set environment variables for longer timeouts
            os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'  # 10 minutes
            os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'  # Enable faster downloads
            
            # Determine if we should use device_map="auto"
            # For larger models like Phi, use device_map="auto" to handle memory constraints
            use_device_map = model_name in ["phi", "mistral"]
            
            # For MPS device, we need to be careful with device_map
            if self.device == "mps" and use_device_map:
                logger.info("Using CPU for device_map with MPS device")
                device_map = "cpu"  # Use CPU for device_map on MPS
            else:
                device_map = "auto" if use_device_map else None
            
            model = AutoModelForCausalLM.from_pretrained(
                config.model_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map=device_map,
                use_cache=True,
                token=settings.HUGGINGFACE_TOKEN if config.is_gated else None,
                local_files_only=config.local_files_only
            )
            model.eval()
            
            # Load tokenizer
            logger.info(f"Loading tokenizer for {config.model_id}")
            tokenizer = AutoTokenizer.from_pretrained(
                config.model_id,
                token=settings.HUGGINGFACE_TOKEN if config.is_gated else None,
                local_files_only=config.local_files_only
            )
            tokenizer.pad_token = tokenizer.eos_token
            
            # Cache the model and tokenizer
            self._model_cache[model_name] = model
            self._tokenizer_cache[model_name] = tokenizer
            
            return model, tokenizer
            
        except Exception as e:
            if "gated repo" in str(e).lower():
                raise ValueError(
                    f"Model '{model_name}' is a gated repository. "
                    "Please ensure you have access to the model and have set the HUGGINGFACE_TOKEN environment variable."
                )
            elif "timeout" in str(e).lower():
                raise ValueError(
                    f"Timeout while downloading model '{model_name}'. "
                    "The model is large and may take several minutes to download. "
                    "Please try again with a stable internet connection."
                )
            elif "connection" in str(e).lower():
                raise ValueError(
                    f"Connection error while downloading model '{model_name}'. "
                    "Please check your internet connection and try again."
                )
            raise ValueError(f"Failed to load model '{model_name}': {str(e)}")
    
    def clear_cache(self):
        """Clear the model and tokenizer cache."""
        self._model_cache.clear()
        self._tokenizer_cache.clear()
        self.get_model_and_tokenizer.cache_clear() 