from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional
from ..core.config import get_settings

settings = get_settings()

class LLMService:
    def __init__(self):
        self.model_name = settings.LLM_MODEL_NAME
        
        # Determine the device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
            
        print(f"Loading model {self.model_name} on {self.device}...")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Configure model loading based on device
        model_kwargs = {
            "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
            "device_map": "auto",
            "low_cpu_mem_usage": True  # Optimize memory usage
        }
        
        if self.device == "mps":
            # For MPS, we need to load in CPU first and then move to MPS
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            ).to(self.device)
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
        
        # Set generation parameters for faster responses
        self.max_length = 100  # Reduced from 512
        self.temperature = 0.3  # Reduced from 0.7 for more focused responses
        self.top_p = 0.7  # Reduced from 0.9
        self.num_return_sequences = 1
        self.do_sample = True
        self.pad_token_id = self.tokenizer.eos_token_id
        
    def generate_response(self, prompt: str) -> str:
        """Generate a response to the given prompt."""
        # Format the prompt according to the model's requirements
        formatted_prompt = self._format_prompt(prompt)
        
        # Tokenize input
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt")
        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate response with optimized parameters
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                num_return_sequences=self.num_return_sequences,
                do_sample=self.do_sample,
                pad_token_id=self.pad_token_id,
                early_stopping=True  # Stop when we have a complete response
            )
        
        # Decode and clean up response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = self._clean_response(response, prompt)
        
        return response
    
    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt according to the model's requirements."""
        # More focused prompt template
        return f"Question: {prompt}\nAnswer:"
    
    def _clean_response(self, response: str, prompt: str) -> str:
        """Clean up the generated response."""
        # Remove the prompt from the response
        response = response.replace(f"Question: {prompt}\nAnswer:", "").strip()
        # Remove any additional questions or conversation
        response = response.split("\n")[0].strip()
        return response 