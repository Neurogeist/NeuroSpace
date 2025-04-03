from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional, Dict, Any
import os
from functools import lru_cache
from datetime import datetime
import logging
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model_name = settings.LLM_MODEL_NAME
        self.max_length = settings.LLM_MAX_LENGTH
        self.temperature = settings.LLM_TEMPERATURE
        self.top_p = settings.LLM_TOP_P
        self.num_beams = settings.LLM_NUM_BEAMS
        self.do_sample = settings.LLM_DO_SAMPLE
        self.early_stopping = settings.LLM_EARLY_STOPPING
        self.use_cache = settings.LLM_USE_CACHE
        
        # System prompt
        self.system_prompt = "You are a helpful assistant. Be concise and clear."
        
        # Check device availability
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        logger.info(f"Using device: {self.device}")
        
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the model and tokenizer with optimized settings."""
        try:
            if self.model is None:
                logger.info(f"Loading model {self.model_name} on {self.device}")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto",
                    use_cache=self.use_cache
                )
                self.model.eval()
                
            if self.tokenizer is None:
                logger.info("Loading tokenizer")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise Exception(f"Failed to load model: {str(e)}")

    @lru_cache(maxsize=100)
    def generate_response(self, prompt: str) -> str:
        """Generate a response with optimized settings and caching."""
        try:
            # Format the prompt
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize the input
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt", padding=True, truncation=True)
            
            # Move inputs to the correct device
            if self.device == "mps":
                # For MPS, we need to move the model to MPS first
                self.model = self.model.to(self.device)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response with improved parameters
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,  # Limit new tokens to prevent long responses
                    temperature=0.7,      # Balanced creativity
                    top_p=0.9,           # Nucleus sampling
                    do_sample=True,       # Enable sampling
                    num_beams=1,          # Use greedy decoding
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,  # Encourage stopping
                    early_stopping=True
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean the response to only include the first assistant reply
            cleaned_response = self._clean_response(response, prompt)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")

    def clear_cache(self):
        """Clear the response cache."""
        self.generate_response.cache_clear()

    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt with system message."""
        return f"{self.system_prompt}\n\nUser: {prompt}\nAssistant:"

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