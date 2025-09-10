import os
import yaml
from pathlib import Path
from typing import Optional, Dict
from pydantic import model_validator
from pydantic_settings import BaseSettings


class InvalidConfigurationError(Exception):
    pass


class Settings(BaseSettings):
    """
    Configuração centralizada da aplicação usando Pydantic Settings.
    """

    # --- AI Provider API Keys ---
    # At least one of these (or GCP auth) is required.
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

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

    @model_validator(mode='after')
    def check_credentials(self) -> 'Settings':
        """
        Ensures that at least one AI provider credential is configured.
        Only enforced when running in Docker containers - local development bypasses this check.
        Local development can use Claude Code CLI without API keys.
        """
        # Check if running in Docker container
        is_docker = (
            os.path.exists("/.dockerenv") or 
            os.getenv("DOCKER_CONTAINER") == "true" or
            os.path.exists("/root/.config/gcloud")  # Docker-specific gcloud path
        )
        
        # Skip credential validation for local development (Claude Code CLI available)
        if not is_docker:
            # Check if Claude Code CLI is available locally
            try:
                import subprocess
                result = subprocess.run(["claude", "--version"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=3)
                if result.returncode == 0:
                    # Claude Code CLI available - no API credentials needed
                    return self
            except:
                pass
            
            # If no Claude Code CLI, still allow local development without strict validation
            return self
            
        # For Docker containers, validate credentials
        gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        gcloud_config_exists = os.path.exists("/root/.config/gcloud")

        has_api_key = self.GEMINI_API_KEY or self.ANTHROPIC_API_KEY
        has_gcp_auth = gcp_creds or gcloud_config_exists

        if not (has_api_key or has_gcp_auth):
            raise ValueError(
                "\n" + "="*80 + "\n"
                "CONFIGURATION ERROR: No AI credentials found!\n\n"
                "To fix this, please:\n"
                "  1. Copy the '.env.example' file to '.env' (`cp .env.example .env`).\n"
                "  2. Add your API key (e.g., GEMINI_API_KEY) to the .env file.\n"
                "  OR\n"
                "  3. Configure Google Cloud authentication by mounting your gcloud config\n"
                "     or setting the GOOGLE_APPLICATION_CREDENTIALS environment variable.\n"
                "  OR\n"
                "  4. For local development, install Claude Code CLI (`curl -fsSL https://claude.ai/install.sh | sh`)"
                "\n" + "="*80
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class ConfigManager:
    """
    Gerenciador centralizado de configuração que carrega e valida o config.yaml.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config_data = None
    
    def _load_config(self) -> Dict:
        """Carrega o arquivo config.yaml."""
        if self._config_data is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        
        return self._config_data
    
    def load_storage_config(self) -> Dict:
        """Carrega e valida a seção storage_backend do config.yaml."""
        config = self._load_config()
        
        if 'storage_backend' not in config:
            raise InvalidConfigurationError("Missing 'storage_backend' section in config.yaml")
        
        storage_config = config['storage_backend']
        
        if 'type' not in storage_config:
            raise InvalidConfigurationError("Missing 'type' field in storage_backend section")
        
        storage_type = storage_config['type']
        if storage_type not in ['filesystem', 'mongodb']:
            raise InvalidConfigurationError(
                f"Invalid storage type '{storage_type}'. Must be 'filesystem' or 'mongodb'"
            )
        
        return storage_config


# Schema version constant
CURRENT_SUPPORTED_SCHEMA_VERSION = "1.0"

# Global settings instance
settings = Settings()
