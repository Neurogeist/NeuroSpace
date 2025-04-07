from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Optional, Dict, Any
import os
from functools import lru_cache
from datetime import datetime
import logging
from ..core.config import get_settings
from .model_registry import ModelRegistry
from .llm_remote import RemoteLLMClient

settings = get_settings()
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Initialize the model registry
        self.registry = ModelRegistry()
        
        # Default model name
        self.default_model = "mixtral-remote"
        
        # Current model and tokenizer
        self.current_model_name = self.default_model
        self.model = None
        self.tokenizer = None
        self.config = None
        
        # Initialize remote client
        self.remote_client = RemoteLLMClient()
        
        # Load the default model
        self._load_model(self.default_model)
    
    def _load_model(self, model_name: str):
        """Load a specific model and tokenizer."""
        try:
            # Get model config
            self.config = self.registry.get_model_config(model_name)
            if not self.config:
                raise ValueError(f"Model '{model_name}' not found")
            
            # Only load model and tokenizer if using local provider
            if self.config.provider == "local":
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
    def generate_response(self, prompt: str, model_name: Optional[str] = None, chat_history: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response with the specified model."""
        try:
            # Set model if specified
            if model_name and model_name != self.current_model_name:
                self.set_model(model_name)
            
            # Format the prompt with chat history
            formatted_prompt = self._format_prompt(prompt, chat_history)
            logger.info(f"Formatted prompt: {formatted_prompt}")
            
            # Generate response based on provider
            if self.config.provider == "local":
                # Use existing local generation flow
                inputs = self.tokenizer(formatted_prompt, return_tensors="pt", padding=True, truncation=True)
                
                # Determine the correct device for inputs
                if hasattr(self.model, 'device_map') and self.model.device_map is not None:
                    for param in self.model.parameters():
                        if param.device.type != 'meta':
                            target_device = param.device
                            break
                    else:
                        target_device = torch.device('cpu')
                    inputs = {k: v.to(target_device) for k, v in inputs.items()}
                    logger.info(f"Using device {target_device} for inputs with device_map model")
                else:
                    if self.registry.device == "mps":
                        self.model = self.model.to(self.registry.device)
                    inputs = {k: v.to(self.registry.device) for k, v in inputs.items()}
                    logger.info(f"Using device {self.registry.device} for inputs")
                
                # Set generation parameters
                generation_config = {
                    "max_new_tokens": self.config.max_new_tokens,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                    "do_sample": self.config.do_sample,
                    "num_beams": self.config.num_beams,
                    "pad_token_id": self.tokenizer.eos_token_id,
                    "eos_token_id": self.tokenizer.eos_token_id,
                    "early_stopping": self.config.early_stopping,
                    "return_dict_in_generate": True,
                    "output_scores": False
                }
                
                # Add timeout for generation
                if self.registry.device == "mps":
                    generation_config["max_time"] = 60.0
                
                logger.info(f"Generation config: {generation_config}")
                
                # Generate response with model-specific parameters
                with torch.no_grad():
                    try:
                        outputs = self.model.generate(
                            **inputs,
                            **generation_config
                        )
                        # Get the sequences from the output
                        sequences = outputs.sequences if hasattr(outputs, 'sequences') else outputs
                        logger.info(f"Raw model output shape: {sequences.shape}")
                        # Get input length from the inputs dictionary
                        input_length = inputs['input_ids'].shape[1]
                        logger.info(f"Generated token count: {sequences.shape[1] - input_length}")
                    except RuntimeError as e:
                        if "out of memory" in str(e).lower():
                            raise ValueError(
                                "Model ran out of memory. Try using a smaller model or reducing max_new_tokens."
                            )
                        elif "timeout" in str(e).lower():
                            raise ValueError(
                                "Generation timed out. The model is taking too long to respond. "
                                "Try using a smaller model or reducing max_new_tokens."
                            )
                        raise
                
                # Decode the response
                response = self.tokenizer.decode(sequences[0], skip_special_tokens=True)
            else:
                # Use remote client for generation
                response = self.remote_client.generate(
                    model_id=self.config.model_id,
                    prompt=prompt,
                    system_prompt=self.config.system_prompt,
                    config=self.config
                )
            
            logger.info(f"Raw decoded response: {response}")
            
            # Clean the response
            cleaned_response = self._clean_response(response, formatted_prompt)
            logger.info(f"Cleaned response: {cleaned_response}")
            
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
    
    def _format_prompt(self, prompt: str, chat_history: Optional[str] = None) -> str:
        """Format the prompt with system message and chat history."""
        if self.current_model_name == "tinyllama":
            # TinyLlama uses a specific chat format
            formatted_prompt = f"<|system|>\n{self.config.system_prompt}\n\n"
            
            # Add chat history if provided
            if chat_history:
                # Process chat history more robustly
                current_role = None
                current_message = []
                
                # Split chat history by lines and process line by line
                for line in chat_history.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("User:"):
                        # If we were building a previous message, add it to the prompt
                        if current_role and current_message:
                            msg_text = '\n'.join(current_message).strip()
                            if current_role == "user":
                                formatted_prompt += f"<|user|>\n{msg_text}\n\n"
                            elif current_role == "assistant":
                                formatted_prompt += f"<|assistant|>\n{msg_text}\n\n"
                        
                        # Start a new user message
                        current_role = "user"
                        current_message = [line[5:].strip()]
                    elif line.startswith("Assistant:"):
                        # If we were building a previous message, add it to the prompt
                        if current_role and current_message:
                            msg_text = '\n'.join(current_message).strip()
                            if current_role == "user":
                                formatted_prompt += f"<|user|>\n{msg_text}\n\n"
                            elif current_role == "assistant":
                                formatted_prompt += f"<|assistant|>\n{msg_text}\n\n"
                        
                        # Start a new assistant message
                        current_role = "assistant"
                        current_message = [line[10:].strip()]
                    else:
                        # Continue building the current message
                        if current_role:
                            current_message.append(line)
                
                # Add the final message if there is one
                if current_role and current_message:
                    msg_text = '\n'.join(current_message).strip()
                    if current_role == "user":
                        formatted_prompt += f"<|user|>\n{msg_text}\n\n"
                    elif current_role == "assistant":
                        formatted_prompt += f"<|assistant|>\n{msg_text}\n\n"
            
            # Add the current user message
            formatted_prompt += f"<|user|>\n{prompt}\n\n<|assistant|>\n"
            return formatted_prompt
        else:
            # Default format for other models
            formatted_prompt = f"{self.config.system_prompt}\n\n"
            
            # Add chat history if provided
            if chat_history:
                # Process chat history more robustly
                current_role = None
                current_message = []
                
                # Split chat history by lines and process line by line
                for line in chat_history.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("User:"):
                        # If we were building a previous message, add it to the prompt
                        if current_role and current_message:
                            msg_text = '\n'.join(current_message).strip()
                            formatted_prompt += f"{current_role}: {msg_text}\n\n"
                        
                        # Start a new user message
                        current_role = "User"
                        current_message = [line[5:].strip()]
                    elif line.startswith("Assistant:"):
                        # If we were building a previous message, add it to the prompt
                        if current_role and current_message:
                            msg_text = '\n'.join(current_message).strip()
                            formatted_prompt += f"{current_role}: {msg_text}\n\n"
                        
                        # Start a new assistant message
                        current_role = "Assistant"
                        current_message = [line[10:].strip()]
                    else:
                        # Continue building the current message
                        if current_role:
                            current_message.append(line)
                
                # Add the final message if there is one
                if current_role and current_message:
                    msg_text = '\n'.join(current_message).strip()
                    formatted_prompt += f"{current_role}: {msg_text}\n\n"
            
            # Add the current user message
            formatted_prompt += f"User: {prompt}\nAssistant:"
            return formatted_prompt
    
    def _clean_response(self, response: str, formatted_prompt: str) -> str:
        """Clean the model's response to only include the assistant's reply."""
        # Remove the prompt from the response
        response = response.replace(formatted_prompt, "").strip()
        
        # Handle TinyLlama specific format
        if self.current_model_name == "tinyllama":
            # Split at any subsequent markers
            # Truncate response at any known markers that indicate a new message
            for marker in ["<|system|>", "<|user|>", "<|assistant|>", "User:", "Assistant:", "AI:", "<|endoftext|>"]:
                idx = response.find(marker)
                if idx != -1:
                    response = response[:idx].strip()
            
            # Remove any remaining conversation markers
            response = response.replace("Question:", "").replace("Answer:", "").strip()
            
            # Format numbered lists with line breaks
            response = self._format_lists(response)
            
            # Remove any trailing newlines and whitespace
            response = response.strip()
            
            return response
        else:
            # Handle other models
            if "User:" in response:
                response = response.split("User:")[0].strip()
            if "Assistant:" in response:
                response = response.split("Assistant:")[0].strip()
            
            # Remove any other conversation markers
            response = response.replace("Question:", "").replace("Answer:", "").strip()
            
            # Format numbered lists with line breaks
            response = self._format_lists(response)
            
            return response
            
    def _format_lists(self, text: str) -> str:
        """Format numbered or bulleted lists with proper line breaks."""
        import re
        
        # Already has proper line breaks
        if "\n1." in text or "\n2." in text or "\n3." in text:
            return text
            
        # Fix numbered lists without line breaks (e.g., "1. item 2. item")
        # This matches patterns like "1. text 2. text" and adds line breaks
        text = re.sub(r'(\d+\.\s*[^.0-9]+)(?=\d+\.)', r'\1\n', text)
        
        # Improved handling for numbered lists with multiple digits
        text = re.sub(r'(\d{1,2}\.\s*[^\n.]+?)(\s+\d{1,2}\.)', r'\1\n\2', text)
        
        # Fix numbered lists with missing line breaks after the numbers (e.g., "1.item 2.item")
        text = re.sub(r'(\d+\.)([^\s])', r'\1 \2', text)
        
        # Fix bullet points without line breaks
        text = re.sub(r'(•\s*[^•]+)(?=•)', r'\1\n', text)
        
        # Fix dash bullet points without line breaks
        text = re.sub(r'(-\s*[^-]+)(?=-\s)', r'\1\n', text)
        
        # Handle cases where there might be a colon followed by a list
        parts = text.split(':')
        if len(parts) > 1:
            first_part = parts[0] + ':'
            rest = ':'.join(parts[1:])
            
            # Check if the rest starts with what looks like a list item
            if re.match(r'\s*\d+\.', rest):
                # Split by number+period+space pattern
                list_items = re.split(r'(\s*\d+\.\s+)', rest)
                if len(list_items) > 2:  # We have at least one item
                    formatted_list = []
                    for i in range(1, len(list_items), 2):
                        if i+1 < len(list_items):
                            formatted_list.append(list_items[i] + list_items[i+1].strip())
                    
                    # Join with newlines
                    formatted_rest = '\n'.join(formatted_list)
                    text = first_part + '\n' + formatted_rest
        
        return text 