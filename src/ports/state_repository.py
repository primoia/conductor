from abc import ABC, abstractmethod
from typing import Dict, Any


class StateRepository(ABC):
    """
    Interface abstrata para gerenciamento de persistência de estado do agente.
    """

    @abstractmethod
    def load_state(self, agent_home_path: str, state_file_name: str) -> Dict[str, Any]:
        """
        Carrega o estado de um agente.

        Args:
            agent_home_path: Caminho do diretório home do agente
            state_file_name: Nome do arquivo de estado

        Returns:
            Dicionário com o estado ou um estado inicial padrão se não existir
        """
        pass

    @abstractmethod
    def save_state(
        self, agent_home_path: str, state_file_name: str, state_data: Dict[str, Any]
    ) -> bool:
        """
        Salva o estado de um agente.

        Args:
            agent_home_path: Caminho do diretório home do agente
            state_file_name: Nome do arquivo de estado
            state_data: Dados do estado para salvar

        Returns:
            True em caso de sucesso, False caso contrário
        """
        pass
