# src/infrastructure/storage/filesystem_repository.py
from src.ports.state_repository import IStateRepository

class FileSystemStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em sistema de arquivos."""
    pass