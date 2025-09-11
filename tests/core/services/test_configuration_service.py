# tests/core/services/test_configuration_service.py
import pytest
from unittest.mock import patch, mock_open
import yaml

from src.core.services.configuration_service import ConfigurationService
from src.core.exceptions import ConfigurationError
from src.core.config_schema import GlobalConfig, StorageConfig


class TestConfigurationService:
    """Tests for ConfigurationService."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config_success(self, mock_safe_load, mock_open_file):
        """Testa o carregamento de configuração bem-sucedido."""
        mock_config = {
            "storage": {"type": "filesystem", "path": "/tmp/ws"},
            "tool_plugins": ["/plugins"]
        }
        mock_safe_load.return_value = mock_config
        
        service = ConfigurationService("test_config.yaml")
        
        storage_config = service.get_storage_config()
        assert storage_config.type == "filesystem"
        assert storage_config.path == "/tmp/ws"
        assert service.get_tool_plugins() == ["/plugins"]
        mock_open_file.assert_called_with("test_config.yaml", 'r')

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_config_not_found(self, mock_open_file):
        """Testa o erro quando o config não é encontrado."""
        with pytest.raises(ConfigurationError, match="não encontrado"):
            ConfigurationService("non_existent_file.yaml")

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML"))
    def test_load_config_invalid_yaml(self, mock_safe_load, mock_open_file):
        """Testa o erro quando o YAML é inválido."""
        with pytest.raises(ConfigurationError, match="Erro ao carregar ou validar"):
            ConfigurationService("test_config.yaml")

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_get_global_config(self, mock_safe_load, mock_open_file):
        """Testa se retorna a configuração global."""
        mock_config = {
            "storage": {"type": "filesystem", "path": "/tmp/ws"},
            "tool_plugins": []
        }
        mock_safe_load.return_value = mock_config
        
        service = ConfigurationService()
        
        global_config = service.get_global_config()
        assert isinstance(global_config, GlobalConfig)
        assert global_config.storage.type == "filesystem"