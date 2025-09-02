from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuracoes centralizadas da aplicacao.
    
    Carrega configuracoes de variaveis de ambiente e arquivo .env.
    """
    
    DATA_FILE_PATH: str = "data/items.json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Instancia global das configuracoes
settings = Settings()