# src/core/services/agent_discovery_service.py
from typing import List, Optional
from src.core.services.storage_service import StorageService
from src.core.domain import AgentDefinition


class AgentDiscoveryService:
    """Responsável por descobrir e listar agentes."""

    def __init__(self, storage_service: StorageService):
        self._storage = storage_service.get_repository()

    def discover_agents(self) -> List[AgentDefinition]:
        """Descobre e retorna todas as definições de agentes disponíveis."""
        agent_ids = self._storage.list_agents()
        definitions = []
        
        for agent_id in agent_ids:
            definition = self.get_agent_definition(agent_id)
            if definition:
                definitions.append(definition)
        
        return definitions

    def get_agent_definition(self, agent_id: str) -> Optional[AgentDefinition]:
        """Carrega a definição de um agente específico."""
        definition_data = self._storage.load_definition(agent_id)
        
        if not definition_data:
            return None
        
        # Remove agent_id from definition before creating AgentDefinition
        definition_data = definition_data.copy()
        definition_data.pop("agent_id", None)  # Remove agent_id if present
        
        # Add agent_id as optional parameter
        return AgentDefinition(**definition_data, agent_id=agent_id)