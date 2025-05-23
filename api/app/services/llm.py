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
from .chat_session import ChatSessionService
import tiktoken  # Add this to your imports
import hashlib
import json

settings = get_settings()
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, chat_session_service: ChatSessionService):
        # Initialize the model registry
        self.registry = ModelRegistry()
        
        # Default model name
        self.default_model = "mixtral-8x7b-instruct"
        
        # Current model and tokenizer
        self.current_model_name = self.default_model
        self.model = None
        self.tokenizer = None
        self.config = None
        
        # Initialize remote client
        self.remote_client = RemoteLLMClient()
        
        # Store the chat session service
        self.chat_session_service = chat_session_service
        
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
    async def generate_response(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate a response using the specified model."""
        try:
            # Sanitize session_id length
            if session_id and len(session_id) > 100:
                logger.warning(f"⚠️ Received overly long session_id: {session_id[:80]}...")
                session_id = None  # Treat as new session
            
            # Get model config
            model_config = self.registry.get_model_config(model_id)
            if not model_config:
                raise ValueError(f"Model {model_id} not found")
            
            # Override config values if specified
            if temperature is not None:
                model_config.temperature = temperature
            if max_tokens is not None:
                model_config.max_new_tokens = max_tokens
            if system_prompt is not None:
                model_config.system_prompt = system_prompt
            
            # Format the prompt with conversation history
            formatted_prompt = self._format_prompt(prompt, session_id)
            logger.info(f"Formatted prompt with session {session_id}: {formatted_prompt}")
            
            try:
                # Try generating with the requested model
                response = await self.remote_client.generate(
                    model_id=model_config.model_id,
                    prompt=formatted_prompt,
                    system_prompt=model_config.system_prompt,
                    config=model_config
                )
            except Exception as e:
                logger.warning(f"Error with primary model {model_id}: {str(e)}")
                
                # If the model is remote and fails, try falling back to a local model
                if model_config.provider != "local":
                    logger.info("Attempting to fall back to local model...")
                    # Get a local model config
                    local_model = "tinyllama"  # or any other local model you prefer
                    local_config = self.registry.get_model_config(local_model)
                    if local_config and local_config.provider == "local":
                        # Load the local model
                        self._load_model(local_model)
                        # Generate with local model
                        response = await self.remote_client.generate(
                            model_id=local_config.model_id,
                            prompt=formatted_prompt,
                            system_prompt=local_config.system_prompt,
                            config=local_config
                        )
                    else:
                        raise Exception("No fallback local model available")
                else:
                    raise
            
            # Clean the response
            cleaned_response = self._clean_response(response, formatted_prompt)
            logger.info(f"Cleaned response: {cleaned_response}")

            logger.info(f"Returning session_id: {session_id}")
            
            return {
                "response": cleaned_response
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def clear_cache(self):
        """Clear the response cache."""
        self.generate_response.cache_clear()

    def _format_prompt(self, prompt: str, session_id: Optional[str] = None) -> str:
        """Format the prompt with system message and conversation history, truncated to fit token budget."""
        try:
            # Configuration for token limits
            context_window = 8192  # You can make this dynamic based on model
            response_tokens = 512
            available_tokens = context_window - response_tokens

            encoding = tiktoken.get_encoding("cl100k_base")
            system_prompt = self.config.system_prompt or ""
            formatted_prompt = f"{system_prompt}\n\n"

            messages = []
            
            # Add session messages
            if session_id:
                logger.info(f"Getting session history for session {session_id}")
                session = self.chat_session_service.get_session(session_id)
                if session:
                    logger.info(f"Found session with {len(session.messages)} messages")
                    messages.extend(session.messages)
                else:
                    logger.warning(f"No session found for ID {session_id}")

            # Add current prompt as the final message
            messages.append(type('Msg', (), {"role": "user", "content": prompt}))

            # Format messages and trim to token budget
            token_count = self._count_tokens(system_prompt)
            selected_messages = []

            for msg in reversed(messages):  # Add recent messages first
                formatted_msg = f"{msg.role.capitalize()}: {msg.content}\n"
                msg_tokens = self._count_tokens(formatted_msg)
                if token_count + msg_tokens <= available_tokens:
                    selected_messages.insert(0, formatted_msg)
                    token_count += msg_tokens
                else:
                    logger.info("Truncating older message to fit token budget")
                    break

            # Combine
            for msg_str in selected_messages:
                formatted_prompt += msg_str
            formatted_prompt += "Assistant:"


            logger.info(f"🧠 Selected {len(selected_messages)} messages out of {len(messages)} total")

            #logger.info(f"Final prompt token count: {token_count}")
            return formatted_prompt

        except Exception as e:
            logger.error(f"Error formatting prompt: {str(e)}")
            raise

    def _count_tokens(self, text: str) -> int:
        """Utility to count tokens using tiktoken."""
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    
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

        
    def create_verification_hash(self, data: Dict[str, Any]) -> str:
        """Create a verification hash for the full generation payload."""
        try:
            import json
            import hashlib

            # Log the data being hashed
            logger.info(f"📝 Backend verification data: {data}")
            
            # Serialize with consistent formatting
            data_bytes = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
            serialized_data = data_bytes.decode('utf-8')
            logger.info(f"📝 Backend serialized data: {serialized_data}")
            
            hash_hex = hashlib.sha256(data_bytes).hexdigest()
            logger.info(f"🔐 Generated hash: {hash_hex}")
            return hash_hex
        except Exception as e:
            logger.error(f"❌ Error creating verification hash: {str(e)}")
            raise
