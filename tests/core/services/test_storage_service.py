# tests/core/services/test_storage_service.py
import pytest
from unittest.mock import MagicMock, patch

from src.core.services.storage_service import StorageService
from src.core.services.configuration_service import ConfigurationService
from src.core.exceptions import ConfigurationError
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository


class TestStorageService:
    """Tests for StorageService."""

    @patch('src.core.services.storage_service.FileSystemStateRepository')
    def test_create_filesystem_backend_success(self, mock_fs_repo):
        """Testa a criação bem-sucedida do backend filesystem."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        mock_config_service.get_storage_config.return_value = mock_storage_config
        
        mock_fs_instance = MagicMock()
        mock_fs_repo.return_value = mock_fs_instance
        
        # Act
        service = StorageService(mock_config_service)
        repository = service.get_repository()
        
        # Assert
        mock_fs_repo.assert_called_once_with(base_path="/test/path")
        assert repository == mock_fs_instance

    @patch('src.core.services.storage_service.MongoStateRepository')
    def test_create_mongodb_backend_success(self, mock_mongo_repo):
        """Testa a criação bem-sucedida do backend MongoDB."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "mongodb"
        mock_storage_config.connection_string = "mongodb://localhost:27017"
        mock_config_service.get_storage_config.return_value = mock_storage_config
        
        mock_mongo_instance = MagicMock()
        mock_mongo_repo.return_value = mock_mongo_instance
        
        # Act
        service = StorageService(mock_config_service)
        repository = service.get_repository()
        
        # Assert
        # Verifica se foi chamado com os parâmetros do settings (que vem do .env nos testes)
        mock_mongo_repo.assert_called_once()
        assert repository == mock_mongo_instance

    def test_create_unknown_backend_raises_error(self):
        """Testa erro para tipo de backend desconhecido."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "unknown_type"
        mock_config_service.get_storage_config.return_value = mock_storage_config
        
        # Act & Assert
        with pytest.raises(ConfigurationError, match="Tipo de armazenamento desconhecido: unknown_type"):
            StorageService(mock_config_service)

    def test_get_repository_returns_same_instance(self):
        """Testa se get_repository sempre retorna a mesma instância (singleton behavior)."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test"
        mock_config_service.get_storage_config.return_value = mock_storage_config
        
        with patch('src.core.services.storage_service.FileSystemStateRepository') as mock_fs_repo:
            mock_instance = MagicMock()
            mock_fs_repo.return_value = mock_instance
            
            # Act
            service = StorageService(mock_config_service)
            repo1 = service.get_repository()
            repo2 = service.get_repository()
            
            # Assert
            assert repo1 is repo2
            assert repo1 == mock_instance

    @patch('src.core.services.storage_service.FileSystemStateRepository')
    def test_config_service_integration(self, mock_fs_repo):
        """Testa integração correta com ConfigurationService."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/integration/test"
        mock_config_service.get_storage_config.return_value = mock_storage_config
        
        # Act
        service = StorageService(mock_config_service)
        
        # Assert
        mock_config_service.get_storage_config.assert_called_once()
        mock_fs_repo.assert_called_once_with(base_path="/integration/test")

    def test_storage_service_caches_repository_creation(self):
        """Testa se o serviço não recria o repositório desnecessariamente."""
        # Arrange
        mock_config_service = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/cache/test"
        mock_config_service.get_storage_config.return_value = mock_storage_config
        
        with patch('src.core.services.storage_service.FileSystemStateRepository') as mock_fs_repo:
            mock_instance = MagicMock()
            mock_fs_repo.return_value = mock_instance
            
            # Act
            service = StorageService(mock_config_service)
            service.get_repository()
            service.get_repository()
            service.get_repository()
            
            # Assert - repository should only be created once during __init__
            mock_fs_repo.assert_called_once()