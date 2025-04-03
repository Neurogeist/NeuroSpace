from transformers import AutoModelForCausalLM, AutoTokenizer
from ..core.config import get_settings
import torch
from typing import Optional

class LLMService:
    def __init__(self):
        settings = get_settings()
        self.model_name = settings.LLM_MODEL_NAME
        self.max_length = settings.LLM_MAX_LENGTH
        self.temperature = settings.LLM_TEMPERATURE
        self.top_p = settings.LLM_TOP_P
        
        # Initialize model and tokenizer
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Set padding token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.model.config.eos_token_id

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