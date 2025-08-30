import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuração centralizada da aplicação usando Pydantic Settings.
    """
    
    # MongoDB Configuration
    mongo_uri: Optional[str] = None
    mongo_database: str = "conductor_state"
    mongo_collection: str = "agent_states"
    
    # LLM Configuration
    default_timeout: int = 120
    max_conversation_history: int = 50
    
    # Logging Configuration
    log_level: str = "INFO"
    json_logging: bool = True
    
    # Application Configuration
    environment: str = "develop"
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()