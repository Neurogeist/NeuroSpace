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
    PROJECT_NAME: str = "NeuroSpace"
    
    # Environment settings
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Model settings
    MODEL_REGISTRY_DEVICE: str = "auto"  # "auto", "cpu", "cuda", or "mps"
    MODEL_REGISTRY_MAX_MEMORY_CPU: str = "8GB"
    MODEL_REGISTRY_MAX_MEMORY_GPU: str = "8GB"
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Remote LLM settings
    TOGETHER_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Blockchain settings
    BLOCKCHAIN_NETWORK: str = Field(default="base", env="BLOCKCHAIN_NETWORK")
    BLOCKCHAIN_RPC_URL: str = Field(default="https://mainnet.base.org", env="BLOCKCHAIN_RPC_URL")
    BLOCKCHAIN_PRIVATE_KEY: Optional[str] = None
    
    # IPFS settings
    IPFS_PROVIDER: str = Field(default="local", env="IPFS_PROVIDER")  # "local" or "pinata"
    IPFS_GATEWAY_URL: str = Field(default="https://ipfs.io", env="IPFS_GATEWAY_URL")
    IPFS_API_URL: str = Field(default="http://localhost:5001/api/v0", env="IPFS_API_URL")
    
    # Pinata specific settings
    PINATA_API_KEY: Optional[str] = Field(None, env="PINATA_API_KEY")
    PINATA_API_SECRET: Optional[str] = Field(None, env="PINATA_API_SECRET")
    PINATA_GATEWAY_URL: str = Field(default="https://gateway.pinata.cloud", env="PINATA_GATEWAY_URL")
    PINATA_API_URL: str = Field(default="https://api.pinata.cloud", env="PINATA_API_URL")
    
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

    CONTRACT_ADDRESS: str = Field(..., env="CONTRACT_ADDRESS")
    
    # Payment Contract Configuration
    PAYMENT_CONTRACT_ADDRESS: str
    REACT_APP_PAYMENT_CONTRACT_ADDRESS: str
    NEUROCOIN_PAYMENT_CONTRACT_ADDRESS: str
    
    # Model Configuration
    DEFAULT_MODEL: str = "mixtral-remote"
    DEFAULT_TEMPERATURE: float = 0.8
    DEFAULT_MAX_TOKENS: int = 100
    
    # Database Configuration (optional for in-memory storage)
    DATABASE_URL: Optional[str] = None

    REDIS_URL: Optional[str] = None
    
    # JWT Settings
    JWT_SECRET: str = "supersecret"  # Fallback secret, should be overridden in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    
    @property
    def is_production(self) -> bool:
        """Check if the environment is production."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if the environment is development."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def chain_id(self) -> int:
        """Get the chain ID based on the environment."""
        return 8453 if self.is_production else 84532
    
    @property
    def block_explorer_url(self) -> str:
        """Get the block explorer URL based on the environment."""
        return "https://basescan.org" if self.is_production else "https://sepolia.basescan.org"
    
    @property
    def ipfs_gateway_url(self) -> str:
        """Get the IPFS gateway URL based on the provider."""
        return self.PINATA_GATEWAY_URL if self.IPFS_PROVIDER == "pinata" else self.IPFS_GATEWAY_URL
    
    @property
    def ipfs_api_url(self) -> str:
        """Get the IPFS API URL based on the provider."""
        return self.PINATA_API_URL if self.IPFS_PROVIDER == "pinata" else self.IPFS_API_URL
    
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