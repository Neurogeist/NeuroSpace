from pydantic import BaseModel, ConfigDict
from functools import lru_cache
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # Blockchain settings
    BASE_RPC_URL: str = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
    PRIVATE_KEY: str = os.getenv("PRIVATE_KEY", "")
    CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "")
    
    # IPFS settings
    IPFS_API_URL: str = os.getenv("IPFS_API_URL", "http://localhost:5001/api/v0")
    PINATA_JWT: str = os.getenv("PINATA_JWT", "")
    
    # Hugging Face settings
    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "")
    
    # LLM settings
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "microsoft/phi-2")
    LLM_MAX_LENGTH: int = int(os.getenv("LLM_MAX_LENGTH", "512"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.9"))
    LLM_NUM_BEAMS: int = int(os.getenv("LLM_NUM_BEAMS", "1"))
    LLM_DO_SAMPLE: bool = bool(os.getenv("LLM_DO_SAMPLE", "False"))
    LLM_EARLY_STOPPING: bool = bool(os.getenv("LLM_EARLY_STOPPING", "False"))
    LLM_USE_CACHE: bool = bool(os.getenv("LLM_USE_CACHE", "True"))
    LLM_DEVICE: str = os.getenv("LLM_DEVICE", "cuda")
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    class Config:
        env_file = ".env"

# Create a global settings instance
settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return settings 