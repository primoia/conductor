# src/ports/state_repository.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IStateRepository(ABC):
    """
    Define o contrato para a camada de persistência de estado dos agentes.
    Qualquer backend de armazenamento (filesystem, MongoDB, etc.) deve implementar esta interface.
    """

    @abstractmethod
    def load_definition(self, agent_id: str) -> Dict:
        """
        Carrega a definição do agente (agent.yaml).
        Retorna um dicionário vazio se não encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def save_definition(self, agent_id: str, definition_data: Dict) -> bool:
        """
        Salva a definição do agente (agent.yaml).
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_persona(self, agent_id: str) -> str:
        """
        Carrega a persona do agente (persona.md).
        Retorna string vazia se não encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def save_persona(self, agent_id: str, persona_content: str) -> bool:
        """
        Salva a persona do agente (persona.md).
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def save_session(self, agent_id: str, session_data: Dict) -> bool:
        """
        Salva os dados da sessão (session.json).
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_session(self, agent_id: str) -> Dict:
        """
        Carrega os dados da sessão (session.json).
        Retorna um dicionário vazio se não encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def save_knowledge(self, agent_id: str, knowledge_data: Dict) -> bool:
        """
        Salva os dados de conhecimento (knowledge.json).
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_knowledge(self, agent_id: str) -> Dict:
        """
        Carrega os dados de conhecimento (knowledge.json).
        Retorna um dicionário vazio se não encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def save_playbook(self, agent_id: str, playbook_data: Dict) -> bool:
        """
        Salva os dados do playbook (playbook.yaml).
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_playbook(self, agent_id: str) -> Dict:
        """
        Carrega os dados do playbook (playbook.yaml).
        Retorna um dicionário vazio se não encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def append_to_history(self, agent_id: str, history_entry: Dict) -> bool:
        """
        Adiciona uma entrada ao histórico (history.log) no formato JSON Lines.
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_history(self, agent_id: str) -> List[Dict]:
        """
        Carrega o histórico completo (history.log).
        Retorna uma lista vazia se não encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def list_agents(self) -> List[str]:
        """
        Lista os IDs de todos os agentes disponíveis no backend de armazenamento.
        """
        raise NotImplementedError

    @abstractmethod
    def get_agent_home_path(self, agent_id: str) -> str:
        """
        Retorna o caminho absoluto do diretório home do agente.
        """
        raise NotImplementedError