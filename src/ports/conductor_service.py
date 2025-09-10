# src/ports/conductor_service.py
from abc import ABC, abstractmethod
from typing import List

class IConductorService(ABC):
    """
    Define o contrato para o serviço central que orquestra todo o ecossistema do Conductor.
    Esta interface desacopla a lógica do núcleo dos pontos de entrada (CLIs, APIs).
    """

    @abstractmethod
    def discover_agents(self) -> List['AgentDefinition']:
        """
        Consulta o backend de armazenamento configurado e retorna a definição de todos os agentes disponíveis.
        """
        raise NotImplementedError

    @abstractmethod
    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        """
        Orquestra a execução de uma única tarefa, desde a seleção do agente até a sua conclusão.
        Este é o principal ponto de entrada para a lógica de execução.
        """
        raise NotImplementedError

    @abstractmethod
    def load_tools(self) -> None:
        """
        Carrega as ferramentas (core e plugins) conforme a configuração global.
        Deve ser chamado durante a inicialização do serviço.
        """
        raise NotImplementedError