# src/ports/agent_storage.py
from abc import ABC, abstractmethod
from typing import List

from src.core.domain import (
    AgentDefinition, AgentPersona, AgentPlaybook, AgentKnowledge,
    HistoryEntry, AgentSession
)


class IAgentStorage(ABC):
    """
    Interface comum para operações de alto nível com artefatos de agente.
    Trabalha com objetos de domínio (AgentDefinition, AgentPersona, etc.).
    """

    @abstractmethod
    def load_definition(self, agent_id: str) -> AgentDefinition:
        """Carrega a definição do agente."""
        pass

    @abstractmethod
    def save_definition(self, agent_id: str, definition: AgentDefinition):
        """Salva a definição do agente."""
        pass

    @abstractmethod
    def load_persona(self, agent_id: str) -> AgentPersona:
        """Carrega a persona do agente."""
        pass

    @abstractmethod
    def save_persona(self, agent_id: str, persona: AgentPersona):
        """Salva a persona do agente."""
        pass

    @abstractmethod
    def load_playbook(self, agent_id: str) -> AgentPlaybook:
        """Carrega o playbook do agente."""
        pass

    @abstractmethod
    def save_playbook(self, agent_id: str, playbook: AgentPlaybook):
        """Salva o playbook do agente."""
        pass

    @abstractmethod
    def load_knowledge(self, agent_id: str) -> AgentKnowledge:
        """Carrega o conhecimento do agente."""
        pass

    @abstractmethod
    def save_knowledge(self, agent_id: str, knowledge: AgentKnowledge):
        """Salva o conhecimento do agente."""
        pass

    @abstractmethod
    def load_history(self, agent_id: str) -> List[HistoryEntry]:
        """Carrega o histórico do agente."""
        pass

    @abstractmethod
    def append_to_history(self, agent_id: str, entry: HistoryEntry, user_input: str = None, ai_response: str = None):
        """
        Adiciona uma entrada ao histórico do agente.

        Args:
            agent_id: ID do agente
            entry: Entrada de histórico (com summary truncado)
            user_input: Input completo do usuário (opcional)
            ai_response: Resposta completa do LLM (opcional, usado para construir próximos prompts)
        """
        pass

    @abstractmethod
    def load_session(self, agent_id: str) -> AgentSession:
        """Carrega a sessão do agente."""
        pass

    @abstractmethod
    def save_session(self, agent_id: str, session: AgentSession):
        """Salva a sessão do agente."""
        pass

    @abstractmethod
    def list_agents(self) -> List[str]:
        """Lista todos os agentes disponíveis."""
        pass