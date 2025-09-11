# src/core/services/configuration_service.py
import yaml
from typing import List
from src.core.config_schema import GlobalConfig, StorageConfig
from src.core.exceptions import ConfigurationError


class ConfigurationService:
    """Responsável por carregar e validar configurações."""

    def __init__(self, config_path: str = "config.yaml"):
        self._config = self._load_and_validate_config(config_path)

    def _load_and_validate_config(self, config_path: str) -> GlobalConfig:
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return GlobalConfig(**config_data)
        except FileNotFoundError:
            raise ConfigurationError(f"Arquivo de configuração não encontrado em: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Erro ao carregar ou validar a configuração: {e}")

    def get_storage_config(self) -> StorageConfig:
        return self._config.storage

    def get_tool_plugins(self) -> List[str]:
        return self._config.tool_plugins

    def get_global_config(self) -> GlobalConfig:
        return self._config