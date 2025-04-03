from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional, Dict, Any
import os
from functools import lru_cache
from datetime import datetime
import logging
from ..core.config import get_settings
from .model_registry import ModelRegistry

settings = get_settings()
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Initialize the model registry
        self.registry = ModelRegistry()
        
        # Default model name
        self.default_model = "tinyllama"
        
        # Current model and tokenizer
        self.current_model_name = self.default_model
        self.model = None
        self.tokenizer = None
        self.config = None
        
        # Load the default model
        self._load_model(self.default_model)
    
    def _load_model(self, model_name: str):
        """Load a specific model and tokenizer."""
        try:
            # Get model config
            self.config = self.registry.get_model_config(model_name)
            if not self.config:
                raise ValueError(f"Model '{model_name}' not found")
            
            # Get model and tokenizer
            self.model, self.tokenizer = self.registry.get_model_and_tokenizer(model_name)
            
            # Update current model name
            self.current_model_name = model_name
            
            logger.info(f"Loaded model: {model_name} ({self.config.model_id})")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise Exception(f"Failed to load model: {str(e)}")
    
    def get_available_models(self) -> Dict[str, str]:
        """Get a list of available models."""
        return self.registry.get_available_models()
    
    def set_model(self, model_name: str):
        """Set the current model to use."""
        if model_name != self.current_model_name:
            self._load_model(model_name)
    
    @lru_cache(maxsize=100)
    def generate_response(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response with the specified model."""
        try:
            # Set model if specified
            if model_name and model_name != self.current_model_name:
                self.set_model(model_name)
            
            # Format the prompt
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize the input
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt", padding=True, truncation=True)
            
            # Determine the correct device for inputs
            # For models using device_map="auto" or with offloaded modules, we need to be careful
            if hasattr(self.model, 'device_map') and self.model.device_map is not None:
                # For models with device_map, find the device of the first parameter
                # that's not on the meta device (offloaded to disk)
                for param in self.model.parameters():
                    if param.device.type != 'meta':
                        target_device = param.device
                        break
                else:
                    # If all parameters are on meta device, use CPU
                    target_device = torch.device('cpu')
                
                # Move inputs to the target device
                inputs = {k: v.to(target_device) for k, v in inputs.items()}
                logger.info(f"Using device {target_device} for inputs with device_map model")
            else:
                # For models not using device_map, move to the specified device
                if self.registry.device == "mps":
                    # For MPS, we need to move the model to MPS first
                    self.model = self.model.to(self.registry.device)
                inputs = {k: v.to(self.registry.device) for k, v in inputs.items()}
                logger.info(f"Using device {self.registry.device} for inputs")
            
            # Generate response with model-specific parameters
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_new_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    do_sample=self.config.do_sample,
                    num_beams=self.config.num_beams,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    early_stopping=self.config.early_stopping
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean the response
            cleaned_response = self._clean_response(response, prompt)
            
            # Return response with metadata
            return {
                "response": cleaned_response,
                "model_name": self.current_model_name,
                "model_id": self.config.model_id
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def clear_cache(self):
        """Clear the response cache."""
        self.generate_response.cache_clear()
    
    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt with system message."""
        return f"{self.config.system_prompt}\n\nUser: {prompt}\nAssistant:"
    
    def _clean_response(self, response: str, prompt: str) -> str:
        """Clean the model's response to only include the first assistant reply."""
        # Remove the prompt from the response
        response = response.replace(self._format_prompt(prompt), "").strip()
        
        # Check if the response contains additional "User:" markers
        if "User:" in response:
            # Split at the first "User:" and take only the first part
            response = response.split("User:")[0].strip()
        
        # Remove any additional "Assistant:" markers
        if "Assistant:" in response:
            # Split at the first "Assistant:" and take only the first part
            response = response.split("Assistant:")[0].strip()
        
        # Remove any other conversation markers
        response = response.replace("Question:", "").replace("Answer:", "").strip()
        
        return response 