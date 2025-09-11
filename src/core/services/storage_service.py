# src/core/services/storage_service.py
from src.core.services.configuration_service import ConfigurationService
from src.ports.state_repository import IStateRepository
from src.core.exceptions import ConfigurationError
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository


class StorageService:
    """Responsável por gerenciar backends de armazenamento."""

    def __init__(self, config_service: ConfigurationService):
        self._config = config_service
        self._repository = self._create_storage_backend()

    def _create_storage_backend(self) -> IStateRepository:
        storage_config = self._config.get_storage_config()
        
        if storage_config.type == "filesystem":
            return FileSystemStateRepository(base_path=storage_config.path)
        elif storage_config.type == "mongodb":
            return MongoStateRepository(
                database_name="conductor_state", 
                collection_name="agent_states"
            )
        else:
            raise ConfigurationError(f"Tipo de armazenamento desconhecido: {storage_config.type}")

    def get_repository(self) -> IStateRepository:
        return self._repository