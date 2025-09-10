### Plano de Execução: Estágio 16 - Refatorar o `src/cli/admin.py`

#### Contexto Arquitetônico

Este é o primeiro passo da "cirurgia" real. O `admin.py` atualmente contém a lógica de descoberta de meta-agentes e instancia diretamente o `AgentLogic` legado. Esta tarefa consiste em remover essa lógica e transformá-lo em uma "casca fina". Ele deixará de ter seu próprio cérebro e passará a ser apenas um tradutor, que recebe os comandos do usuário e os repassa para o `ConductorService`.

#### Propósito Estratégico

O objetivo é unificar o fluxo de execução. Ao final desta tarefa, o `admin.py` passará a operar inteiramente sobre a nova arquitetura da SAGA-016. Isso significa que ele ganhará, "de graça", a capacidade de usar diferentes backends de armazenamento e carregar plugins de ferramentas, pois toda essa lógica está encapsulada no `ConductorService`. Estamos efetivamente transplantando o novo coração para o primeiro corpo.

#### Checklist de Execução

- [x] Abrir o arquivo `src/cli/admin.py`.
- [x] No `__init__` da classe `AdminCLI`, remover a instanciação do `AgentLogic`.
- [x] Em seu lugar, obter a instância singleton do `ConductorService` a partir do `container`.
- [x] Remover a lógica de descoberta de caminhos de agente (ex: `projects/_common/agents/`).
- [x] Modificar o método `chat` (e outros métodos relevantes).
- [x] O método `chat` deve agora criar um `TaskDTO` com os dados da requisição (agent_id, user_input).
- [x] Chamar o método `self.conductor_service.execute_task(task_dto)`.
- [x] Adaptar o código para lidar com o `TaskResultDTO` retornado.
- [x] Garantir que os argumentos de linha de comando existentes continuem funcionando, apenas agora como parâmetros para o `TaskDTO`.
