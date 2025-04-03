from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional, Dict, Any
import os
from functools import lru_cache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.model_name = os.getenv("LLM_MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        self.max_length = int(os.getenv("LLM_MAX_LENGTH", "256"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.top_p = float(os.getenv("LLM_TOP_P", "0.7"))
        self.num_beams = int(os.getenv("LLM_NUM_BEAMS", "1"))
        self.do_sample = os.getenv("LLM_DO_SAMPLE", "false").lower() == "true"
        self.early_stopping = os.getenv("LLM_EARLY_STOPPING", "false").lower() == "true"
        self.use_cache = os.getenv("LLM_USE_CACHE", "true").lower() == "true"
        
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
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    num_beams=self.num_beams,
                    do_sample=self.do_sample,
                    early_stopping=self.early_stopping,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean the response
            cleaned_response = self._clean_response(response, prompt)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")

    def clear_cache(self):
        """Clear the response cache."""
        self.generate_response.cache_clear()

    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt for the model."""
        return f"Question: {prompt}\nAnswer:"

    def _clean_response(self, response: str, prompt: str) -> str:
        """Clean the model's response."""
        # Remove the prompt from the response
        response = response.replace(self._format_prompt(prompt), "").strip()
        
        # Remove any additional question/answer markers
        response = response.replace("Question:", "").replace("Answer:", "").strip()
        
        # Remove any student/teacher markers
        response = response.replace("Student:", "").replace("Teacher:", "").strip()
        
        return response 