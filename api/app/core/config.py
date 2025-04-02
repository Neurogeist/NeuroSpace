from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Base Chain Configuration
    BASE_RPC_URL: str
    PRIVATE_KEY: str
    
    # IPFS Configuration (Pinata)
    PINATA_API_KEY: str
    PINATA_API_SECRET: str
    PINATA_JWT: str
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # LLM Configuration
    LLM_MODEL_NAME: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Default to TinyLlama
    LLM_MAX_LENGTH: int = 512
    LLM_TEMPERATURE: float = 0.7
    LLM_TOP_P: float = 0.9
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 