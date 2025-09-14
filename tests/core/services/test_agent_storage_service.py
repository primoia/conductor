# tests/core/services/test_agent_storage_service.py
import pytest
import tempfile
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.core.services.agent_storage_service import AgentStorageService
from src.core.services.configuration_service import ConfigurationService
from src.core.exceptions import ConfigurationError
from src.infrastructure.filesystem_storage import FileSystemStorage
from src.infrastructure.mongodb_storage import MongoDbStorage


class TestAgentStorageService:
    """Tests for AgentStorageService."""

    def test_create_filesystem_storage_success(self):
        """Testa criação bem-sucedida do storage filesystem."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        mock_config_service.get_storage_config.return_value = mock_storage_config

        # Act
        service = AgentStorageService(mock_config_service)
        storage = service.get_storage()

        # Assert
        assert isinstance(storage, FileSystemStorage)

    def test_create_mongodb_storage_success(self):
        """Testa criação bem-sucedida do storage MongoDB."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "mongodb"
        mock_storage_config.connection_string = "mongodb://localhost:27017"
        mock_config_service.get_storage_config.return_value = mock_storage_config

        # Act
        with patch('src.infrastructure.storage.mongo_repository.MongoClient'):
            service = AgentStorageService(mock_config_service)
            storage = service.get_storage()

        # Assert
        assert isinstance(storage, MongoDbStorage)

    def test_unknown_storage_type_raises_error(self):
        """Testa erro para tipo de storage desconhecido."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "unknown_type"
        mock_config_service.get_storage_config.return_value = mock_storage_config

        # Act & Assert
        with pytest.raises(ConfigurationError, match="Tipo de armazenamento desconhecido: unknown_type"):
            AgentStorageService(mock_config_service)

    def test_mongodb_without_connection_string_raises_error(self):
        """Testa erro quando MongoDB não tem connection_string no .env."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "mongodb"
        mock_config_service.get_storage_config.return_value = mock_storage_config

        # Mock settings sem mongo_uri
        with patch('src.config.settings') as mock_settings:
            mock_settings.mongo_uri = None
            mock_settings.mongo_database = "test_db"

            # Act & Assert
            with pytest.raises(ConfigurationError, match="MongoDB connection_string é obrigatória"):
                AgentStorageService(mock_config_service)

    def test_get_state_repository_for_migration(self):
        """Testa método para obter repository de baixo nível para migração."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        mock_config_service.get_storage_config.return_value = mock_storage_config

        # Act
        service = AgentStorageService(mock_config_service)
        repository = service.get_state_repository_for_migration()

        # Assert
        assert repository is not None
        # Verifica se retorna um IStateRepository (baixo nível)
        assert hasattr(repository, 'load_definition')
        assert hasattr(repository, 'list_agents')

    def test_integration_filesystem_storage_works(self):
        """Teste de integração básico com FileSystemStorage."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config_service = MagicMock()
            mock_storage_config = MagicMock()
            mock_storage_config.type = "filesystem"
            mock_storage_config.path = temp_dir
            mock_config_service.get_storage_config.return_value = mock_storage_config

            # Act
            service = AgentStorageService(mock_config_service)
            storage = service.get_storage()

            # Assert
            assert isinstance(storage, FileSystemStorage)

            # Verifica se pode listar agentes (mesmo que vazio)
            agents = storage.list_agents()
            assert isinstance(agents, list)