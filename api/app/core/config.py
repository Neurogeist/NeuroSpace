from pydantic import BaseModel, ConfigDict, Field
from functools import lru_cache
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NeuroChain"
    
    # Model settings
    MODEL_REGISTRY_DEVICE: str = "auto"  # "auto", "cpu", "cuda", or "mps"
    MODEL_REGISTRY_MAX_MEMORY_CPU: str = "8GB"
    MODEL_REGISTRY_MAX_MEMORY_GPU: str = "8GB"
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Remote LLM settings
    TOGETHER_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    
    # Blockchain settings
    BLOCKCHAIN_NETWORK: str = "base"
    BLOCKCHAIN_RPC_URL: str = "https://mainnet.base.org"
    BLOCKCHAIN_PRIVATE_KEY: Optional[str] = None
    
    # IPFS settings
    IPFS_GATEWAY_URL: str = "https://ipfs.io"
    IPFS_API_URL: str = "https://ipfs.infura.io:5001"
    IPFS_PROJECT_ID: Optional[str] = None
    IPFS_PROJECT_SECRET: Optional[str] = None
    
    # Base Chain Configuration
    BASE_RPC_URL: str = Field(..., env="BASE_RPC_URL")
    PRIVATE_KEY: str = Field(..., env="PRIVATE_KEY")
    
    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # LLM Configuration
    LLM_MODEL_NAME: str = Field(..., env="LLM_MODEL_NAME")
    LLM_MAX_LENGTH: int = Field(default=256, env="LLM_MAX_LENGTH")
    LLM_TEMPERATURE: float = Field(default=0.3, env="LLM_TEMPERATURE")
    LLM_TOP_P: float = Field(default=0.7, env="LLM_TOP_P")
    LLM_NUM_BEAMS: int = Field(default=1, env="LLM_NUM_BEAMS")
    LLM_DO_SAMPLE: bool = Field(default=True, env="LLM_DO_SAMPLE")
    LLM_EARLY_STOPPING: bool = Field(default=True, env="LLM_EARLY_STOPPING")
    LLM_USE_CACHE: bool = Field(default=True, env="LLM_USE_CACHE")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        protected_namespaces=('settings_',)
    )

# Create a global settings instance
settings = Settings()

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return settings 