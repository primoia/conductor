import os
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings


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
        """
        gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        # The gcloud config directory inside the Docker container.
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
                "     or setting the GOOGLE_APPLICATION_CREDENTIALS environment variable."
                "\n" + "="*80
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
