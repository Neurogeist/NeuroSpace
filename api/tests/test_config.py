from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class TestSettings(BaseSettings):
    """Test settings for the application."""
    # Base Chain Configuration
    BASE_RPC_URL: str = "https://goerli.base.org"
    PRIVATE_KEY: str = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    
    # IPFS Configuration (Pinata)
    PINATA_API_KEY: str = "test_api_key"
    PINATA_API_SECRET: str = "test_api_secret"
    PINATA_JWT: str = "test_jwt_token"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # LLM Configuration
    LLM_MODEL_NAME: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    LLM_MAX_LENGTH: int = 100
    LLM_TEMPERATURE: float = 0.3
    LLM_TOP_P: float = 0.7
    
    model_config = ConfigDict(env_file=".env.test") 