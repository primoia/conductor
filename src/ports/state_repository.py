# src/ports/state_repository.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IStateRepository(ABC):
    """
    Define o contrato para a camada de persistência de estado dos agentes.
    Qualquer backend de armazenamento (filesystem, MongoDB, etc.) deve implementar esta interface.
    """

    @abstractmethod
    def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Salva o dicionário de estado completo para um determinado agente.
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Carrega o dicionário de estado completo para um determinado agente.
        Retorna um dicionário vazio se o estado não for encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def list_agents(self) -> List[str]:
        """
        Lista os IDs de todos os agentes disponíveis no backend de armazenamento.
        """
        raise NotImplementedError