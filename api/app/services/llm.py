from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional
import os
from functools import lru_cache

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
        self.device = os.getenv("LLM_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the model and tokenizer with optimized settings."""
        if self.model is None:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto",
                use_cache=self.use_cache
            )
            self.model.eval()
            
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token

    @lru_cache(maxsize=100)
    def generate_response(self, prompt: str) -> str:
        """Generate a response with optimized settings and caching."""
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
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
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt):].strip()

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

    async def generate_response(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        try:
            # Format the prompt
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize the input
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_length,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True,
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    # Remove early_stopping since we're not using beam search
                    # early_stopping=True
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean the response
            cleaned_response = self._clean_response(response, prompt)
            
            return cleaned_response
            
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}") 