# src/core/services/agent_storage_service.py
from src.core.services.configuration_service import ConfigurationService
from src.core.services.storage_service import StorageService
from src.ports.agent_storage import IAgentStorage
from src.infrastructure.filesystem_storage import FileSystemStorage
from src.infrastructure.mongodb_storage import MongoDbStorage
from src.core.exceptions import ConfigurationError
from pathlib import Path


class AgentStorageService:
    """
    Serviço que fornece acesso de alto nível aos agentes usando IAgentStorage.

    Esta é a camada intermediária que os services de aplicação deveriam usar
    quando precisam trabalhar com objetos de domínio (AgentDefinition, etc.)
    ao invés de primitivos (Dict, str).
    """

    def __init__(self, config_service: ConfigurationService):
        self._config = config_service
        self._storage = self._create_agent_storage()

    def _create_agent_storage(self) -> IAgentStorage:
        """Cria a instância de IAgentStorage apropriada."""
        storage_config = self._config.get_storage_config()

        if storage_config.type == "filesystem":
            return FileSystemStorage(base_path=Path(storage_config.path))
        elif storage_config.type == "mongodb":
            # Para MongoDB, precisamos da connection_string
            connection_string = storage_config.connection_string
            if not connection_string:
                raise ConfigurationError("MongoDB connection_string é obrigatória")

            return MongoDbStorage(
                connection_string=connection_string,
                db_name=getattr(storage_config, 'database_name', 'conductor')
            )
        else:
            raise ConfigurationError(f"Tipo de armazenamento desconhecido: {storage_config.type}")

    def get_storage(self) -> IAgentStorage:
        """Retorna a instância de IAgentStorage."""
        return self._storage

    def get_state_repository_for_migration(self):
        """
        Retorna o repository de baixo nível para operações de migração.

        Este método existe para casos especiais onde é necessário acesso
        direto aos primitivos (Dict/str) para performance ou migração.
        """
        # Delega para o StorageService existente para manter compatibilidade
        storage_service = StorageService(self._config)
        return storage_service.get_repository()