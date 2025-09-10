# src/infrastructure/storage/filesystem_repository.py
from src.ports.state_repository import IStateRepository
from typing import Dict, Any, List

class FileSystemStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em sistema de arquivos."""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path

    def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        # A ser implementado
        return True

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # Retorna um mock para fins de desenvolvimento
        if agent_id == "CodeReviewer_Agent":
            return {
                "definition": {
                    "name": "Code Reviewer Agent",
                    "version": "1.0.0",
                    "schema_version": "1.0",
                    "description": "Um agente especialista em revisar código.",
                    "author": "system",
                    "tags": [],
                    "capabilities": [],
                    "allowed_tools": []
                }
            }
        elif agent_id == "fs_agent":
            # Use the configured base path if available
            agent_home_path = f"{self.base_path}/agents/fs_agent" if self.base_path else "/fake/path/to/fs_agent"
            return {
                "definition": {
                    "name": "FS Agent", 
                    "version": "1.0", 
                    "schema_version": "1.0",
                    "description": "", 
                    "author": "test",
                    "tags": [],
                    "capabilities": [],
                    "allowed_tools": []
                },
                "agent_home_path": agent_home_path
            }
        return {}

    def list_agents(self) -> List[str]:
        # Retorna uma lista mockada para fins de desenvolvimento
        return ["fs_agent"]