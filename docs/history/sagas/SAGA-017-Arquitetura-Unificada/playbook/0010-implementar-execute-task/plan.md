### Plano de Execução: Estágio 10 - Implementação do `execute_task`

#### Contexto Arquitetônico

Este é o estágio culminante da Fase I. Temos todos os componentes individuais: o `ConductorService` com seu carregador de configuração e factory de armazenamento, o `AgentExecutor` stateless e o `PromptEngine` integrado. Esta tarefa consiste em conectar todas as peças, implementando a lógica do método `execute_task` no `ConductorService`. Este método se tornará o principal ponto de entrada para toda a lógica de execução de agentes no sistema.

#### Propósito Estratégico

O objetivo é orquestrar o fluxo de dados e o ciclo de vida de uma execução de tarefa dentro da nova arquitetura. Ao implementar `execute_task`, estamos criando a "montagem final" do nosso novo motor. Este método encapsulará toda a complexidade de encontrar um agente, instanciar seu executor com as dependências corretas (ferramentas, LLM, etc.) e invocar a execução, retornando um resultado padronizado. Isso completa a fundação do nosso novo núcleo de serviços.

#### Checklist de Execução

- [x] Modificar o `ConductorService` em `src/core/conductor_service.py`.
- [x] Implementar a lógica do método `execute_task(task: TaskDTO)`.
- [x] Chamar `self.repository.load_state(task.agent_id)` para obter a definição e os caminhos do agente.
- [x] Instanciar o `PromptEngine` com o `agent_home_path` obtido.
- [x] Determinar as ferramentas permitidas para o agente a partir de sua definição.
- [x] Instanciar o `AgentExecutor`, injetando todas as dependências (definição, cliente LLM, `PromptEngine`, ferramentas).
- [x] Chamar o método `executor.run(task)`.
- [x] Retornar o `TaskResultDTO` resultante.
