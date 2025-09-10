# src/infrastructure/storage/mongo_repository.py
from src.ports.state_repository import IStateRepository
from typing import Dict, Any, List

class MongoStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em MongoDB."""
    
    def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        # Placeholder implementation
        return True
    
    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # Placeholder implementation
        return {}
    
    def list_agents(self) -> List[str]:
        # Placeholder implementation
        return []