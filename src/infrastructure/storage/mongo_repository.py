# src/infrastructure/storage/mongo_repository.py
from src.ports.state_repository import IStateRepository

class MongoStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em MongoDB."""
    pass