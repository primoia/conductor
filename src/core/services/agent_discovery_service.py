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

    def get_conversation_history(self, agent_id: str) -> List[dict]:
        """Carrega o histórico de conversas de um agente."""
        return self._storage.load_history(agent_id)

    def clear_conversation_history(self, agent_id: str) -> bool:
        """Limpa o histórico de conversas de um agente."""
        try:
            import os
            
            # Clear the history log file by truncating it
            agent_home_path = self._storage.get_agent_home_path(agent_id)
            history_file = os.path.join(agent_home_path, "history.log")
            
            # Truncate the file by opening in write mode
            with open(history_file, 'w', encoding='utf-8') as f:
                pass  # Just open and close to truncate
            
            # Optionally clear session conversation data if present
            try:
                session_data = self._storage.load_session(agent_id)
                # Remove any conversation-related fields from session
                conversation_fields = ["conversation_history", "last_messages", "chat_history"]
                for field in conversation_fields:
                    if field in session_data:
                        del session_data[field]
                self._storage.save_session(agent_id, session_data)
            except Exception:
                # Don't fail completely if session clearing fails
                pass
            
            return True
        except Exception:
            return False

    def agent_exists(self, agent_id: str) -> bool:
        """Verifica se um agente existe no sistema."""
        try:
            agents = self.discover_agents()
            return any(agent.agent_id == agent_id for agent in agents)
        except Exception:
            return False

    def build_meta_agent_context(self, message: str, meta: bool = False, new_agent_id: str = None) -> str:
        """Constrói contexto enhanced para meta-agents."""
        context_parts = []

        # Add new agent ID if specified
        if new_agent_id:
            context_parts.append(f"NEW_AGENT_ID={new_agent_id}")

        # Add meta flag context only if meta is explicitly True or new_agent_id is provided
        if meta or new_agent_id:
            if meta:
                context_parts.append("AGENT_TYPE=meta")
            else:
                context_parts.append("AGENT_TYPE=project")

        # Build final message
        if context_parts:
            context_header = "\n".join(context_parts)
            enhanced_message = f"{context_header}\n\n{message}"
            return enhanced_message
        else:
            return message

    def get_agent_output_scope(self, agent_id: str) -> List[str]:
        """Obtém o escopo de output de um agente."""
        try:
            agent_definition = self.get_agent_definition(agent_id)
            if agent_definition and hasattr(agent_definition, 'capabilities'):
                # Look for output scope in capabilities
                for capability in agent_definition.capabilities:
                    if isinstance(capability, dict) and 'output_scope' in capability:
                        return capability['output_scope']
            return []  # No restrictions by default
        except Exception:
            return []

    def save_agent_state(self, agent_id: str) -> bool:
        """Salva o estado de um agente."""
        try:
            # This could be expanded to save additional state information
            # For now, we'll just ensure the agent directory exists
            agent_home_path = self._storage.get_agent_home_path(agent_id)
            import os
            os.makedirs(agent_home_path, exist_ok=True)
            return True
        except Exception:
            return False

    def list_all_agent_definitions(self) -> List['AgentDefinition']:
        """Lista todas as definições de agente (compatibilidade com AgentService legado)."""
        return self.discover_agents()