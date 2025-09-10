# src/infrastructure/storage/filesystem_repository.py
from src.ports.state_repository import IStateRepository
from typing import Dict, Any, List

class FileSystemStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em sistema de arquivos."""

    def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        # A ser implementado
        return True

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # Retorna um mock para fins de desenvolvimento
        if agent_id == "CodeReviewer_Agent":
            return {
                "definition": {
                    "agent_id": "CodeReviewer_Agent",
                    "name": "Code Reviewer Agent",
                    "version": "1.0.0",
                    "description": "Um agente especialista em revisar código."
                }
            }
        return {}

    def list_agents(self) -> List[str]:
        # Retorna uma lista mockada para fins de desenvolvimento
        return ["CodeReviewer_Agent"]