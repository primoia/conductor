# src/infrastructure/queues/memory_queue.py
import uuid
from collections import deque
from typing import Optional
from src.ports.task_queue import ITaskQueue
from src.core.domain import TaskDTO

class InMemoryTaskQueue(ITaskQueue):
    """
    Uma implementação simples de fila de tarefas em memória para desenvolvimento e testes.
    NÃO É SEGURA PARA USO EM AMBIENTES MULTI-THREADING/MULTI-PROCESSAMENTO.
    """
    def __init__(self):
        self._queue: deque = deque()

    def publish(self, task: TaskDTO) -> str:
        task_id = str(uuid.uuid4())
        # Em um sistema real, o ID seria adicionado ao DTO ou a um envelope
        self._queue.append((task_id, task))
        print(f"Tarefa {task_id} publicada na fila em memória.")
        return task_id

    def consume(self) -> Optional[TaskDTO]:
        if not self._queue:
            return None
        
        task_id, task = self._queue.popleft()
        print(f"Tarefa {task_id} consumida da fila em memória.")
        return task