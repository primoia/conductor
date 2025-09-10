### Plano de Execução: Estágio 17 - Refatorar o `src/cli/agent.py`

#### Contexto Arquitetônico

Seguindo o mesmo procedimento do estágio anterior, esta tarefa foca em refatorar o segundo ponto de entrada legado, o `agent.py`. Ele também contém lógica de descoberta de caminhos de agente (baseada em `environment` e `project`) e instancia o `AgentLogic` diretamente. O objetivo é remover essa lógica e transformá-lo em uma "casca fina" sobre o `ConductorService`.

#### Propósito Estratégico

Completar esta tarefa significa que **todos** os pontos de entrada de usuário do sistema estarão unificados sob a nova arquitetura. O `agent.py` também passará a se beneficiar das capacidades do `ConductorService`, como a descoberta agnóstica de armazenamento e o carregamento de plugins. Isso conclui a "cirurgia", deixando o sistema internamente coeso, mesmo que as duas interfaces de CLI ainda existam externamente.

#### Checklist de Execução

- [ ] Abrir o arquivo `src/cli/agent.py`.
- [ ] No `__init__` da classe `AgentCLI`, remover a instanciação do `AgentLogic`.
- [ ] Obter a instância singleton do `ConductorService` a partir do `container`.
- [ ] Remover a lógica de descoberta de caminhos baseada em `environment` e `project`.
- [ ] Modificar o método `chat` para criar um `TaskDTO`.
- [ ] O `TaskDTO` deve incluir o `agent_id`, `user_input`, e o contexto relevante (`environment`, `project`).
- [ ] Chamar o método `self.conductor_service.execute_task(task_dto)`.
- [ ] Adaptar o código para processar o `TaskResultDTO` retornado.
- [ ] Garantir que os argumentos de linha de comando (`--environment`, `--project`) continuem funcionando como contexto para a tarefa.
