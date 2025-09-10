### Plano de Execução: Estágio 37 - Definir a Interface `ITaskQueue`

#### Contexto Arquitetônico

A visão de longo prazo para o Conductor é uma arquitetura escalável onde o `ConductorService` (ou um `Orquestrador`) não executa tarefas diretamente, mas as publica em uma fila para que "workers" (`AgentExecutor`) possam processá-las de forma assíncrona. Para preparar o terreno para essa arquitetura, precisamos definir um contrato de abstração para a fila, seguindo o Princípio da Inversão de Dependência.

#### Propósito Estratégico

O objetivo é desacoplar o nosso núcleo de serviços da implementação concreta de uma fila de mensagens. Ao definir uma interface `ITaskQueue` em `src/ports/`, podemos desenvolver a lógica do serviço para operar de forma assíncrona sem nos prendermos a uma tecnologia específica (SQS, RabbitMQ, Celery). Isso também nos permite criar uma implementação "em memória" simples para desenvolvimento e testes locais, e usar uma implementação robusta para produção.

#### Checklist de Execução

- [x] Criar um novo arquivo em `src/ports/task_queue.py`.
- [x] No arquivo, definir a interface `ITaskQueue(ABC)`.
- [x] A interface deve ter métodos abstratos essenciais como `publish(task: 'TaskDTO') -> str` (retornando um ID de tarefa) e `consume() -> Optional['TaskDTO']`.
- [x] Adicionar docstrings e type hints claros.
- [x] Criar uma implementação simples em memória (`InMemoryTaskQueue`) em `src/infrastructure/queues/memory_queue.py` que implemente a interface, para fins de teste.
