# Especificação Técnica e Plano de Execução: 0037-definir-interface-task-queue

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação. Você é um arquiteto de software definindo as abstrações para um sistema de enfileiramento de tarefas.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa estabelece a fundação para a execução assíncrona no Conductor. Ao definir uma interface clara para a fila de tarefas, desacoplamos a lógica de negócios da tecnologia de enfileiramento, permitindo implementações intercambiáveis (ex: in-memory para testes, SQS para produção) e promovendo uma arquitetura escalável e resiliente.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização da Interface:** A interface `ITaskQueue` **DEVE** ser criada em um novo arquivo `src/ports/task_queue.py`.
- **Localização da Implementação:** A implementação em memória **DEVE** ser criada em um novo arquivo `src/infrastructure/queues/memory_queue.py`.
- **Abstração Pura:** A `ITaskQueue` **DEVE** ser uma classe abstrata (`abc.ABC`) com métodos abstratos.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar dois novos arquivos. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `src/ports/task_queue.py`**
```python
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
```

**Arquivo 2 (Novo): `src/infrastructure/queues/memory_queue.py`**
```python
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
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando os arquivos `src/ports/task_queue.py` e `src/infrastructure/queues/memory_queue.py` forem criados exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
