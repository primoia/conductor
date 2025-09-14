# src/infrastructure/repository_factory.py

from pathlib import Path
from typing import Dict
from src.config import ConfigManager
from src.infrastructure.filesystem_storage import FileSystemStorage
from src.infrastructure.mongodb_storage import MongoDbStorage
from src.ports.agent_storage import IAgentStorage


class RepositoryFactory:
    """
    Factory class para criar instâncias de repositório baseadas na configuração.
    """

    @staticmethod
    def get_repository(config: Dict) -> IAgentStorage:
        """Cria e retorna a instância de repositório apropriada com base na configuração."""
        repo_type = config.get('type')
        if repo_type == 'filesystem':
            # Assumindo que o path está na config
            workspace_path = config.get('workspace_path', '.conductor_workspace')
            return FileSystemStorage(base_path=Path(workspace_path))
        elif repo_type == 'mongodb':
            return MongoDbStorage(
                connection_string=config.get('connection_string'),
                db_name=config.get('db_name', 'conductor')
            )
        else:
            raise ValueError(f"Tipo de repositório desconhecido: {repo_type}")