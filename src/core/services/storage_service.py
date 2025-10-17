# src/core/services/storage_service.py
from src.core.services.configuration_service import ConfigurationService
from src.ports.state_repository import IStateRepository
from src.core.exceptions import ConfigurationError
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository
from src.config import settings


class StorageService:
    """Responsável por gerenciar backends de armazenamento."""

    def __init__(self, config_service: ConfigurationService):
        print("DEBUG: StorageService.__init__ começou")  # DEBUG
        self._config = config_service
        print("DEBUG: Criando storage backend...")  # DEBUG
        self._repository = self._create_storage_backend()
        print("DEBUG: Storage backend criado")  # DEBUG

    def _create_storage_backend(self) -> IStateRepository:
        print("DEBUG: _create_storage_backend começou")  # DEBUG
        storage_config = self._config.get_storage_config()
        print(f"DEBUG: storage_config.type = {storage_config.type}")  # DEBUG

        if storage_config.type == "filesystem":
            print("DEBUG: Criando FileSystemStateRepository")  # DEBUG
            return FileSystemStateRepository(base_path=storage_config.path)
        elif storage_config.type == "mongodb":
            print("DEBUG: Criando MongoStateRepository")  # DEBUG
            print(f"DEBUG: mongo_uri = {settings.mongo_uri}")  # DEBUG
            return MongoStateRepository(
                connection_string=settings.mongo_uri,
                db_name=settings.mongo_database
            )
        else:
            raise ConfigurationError(f"Tipo de armazenamento desconhecido: {storage_config.type}")

    def get_repository(self) -> IStateRepository:
        return self._repository