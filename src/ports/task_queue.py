# src/ports/task_queue.py
from abc import ABC, abstractmethod
from typing import Optional
from src.core.domain import TaskDTO

class ITaskQueue(ABC):
    """
    Define o contrato para um sistema de fila de tarefas.
    """

    @abstractmethod
    def publish(self, task: TaskDTO) -> str:
        """
        Publica uma tarefa na fila.
        Retorna um ID único para a tarefa enfileirada.
        """
        raise NotImplementedError

    @abstractmethod
    def consume(self) -> Optional[TaskDTO]:
        """
        Consome a próxima tarefa disponível da fila.
        Retorna None se a fila estiver vazia.
        """
        raise NotImplementedError