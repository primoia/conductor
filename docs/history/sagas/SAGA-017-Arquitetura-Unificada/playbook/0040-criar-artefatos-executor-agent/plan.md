### Plano de Execução: Estágio 40 - Criação dos Artefatos do Executor Agent

#### Contexto Arquitetônico

Estamos na Fase VII da SAGA-017, continuando a preparação da arquitetura Maestro-Executor. O Executor Agent é o componente de execução de baixo nível que recebe tarefas específicas do Maestro Agent e as executa de forma segura e controlada. Este estágio cria os artefatos fundamentais do Executor Agent: o arquivo `agent.yaml` com sua definição e o arquivo `persona.md` com sua personalidade e comportamento. Estes artefatos seguem o padrão estabelecido na SAGA-016 e serão descobertos pelo ConductorService através do backend de armazenamento.

#### Propósito Estratégico

O propósito desta tarefa é criar formalmente o Executor Agent como um agente de execução especializado. Este agente será responsável por executar tarefas específicas delegadas pelo Maestro Agent, focando em escrita de código e execução de comandos shell seguros. A criação destes artefatos estabelece o Executor como um componente fundamental da arquitetura de três camadas, preparando-o para receber e executar tarefas de forma isolada e controlada.

#### Checklist de Execução

- [ ] Navegar até o diretório de agentes do sistema.
- [ ] Criar o diretório específico para o Executor Agent.
- [ ] Criar o arquivo `definition.yaml` com a definição básica do agente.
- [ ] Criar o arquivo `persona.md` com a personalidade e comportamento do agente.
- [ ] Definir as informações básicas: nome, descrição, tipo, e metadados.
- [ ] Estruturar os artefatos seguindo o padrão da SAGA-016.
- [ ] Validar que os artefatos estão prontos para descoberta pelo ConductorService.
