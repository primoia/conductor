# SAGA-017 Plano de Execução V2: O Protocolo Ponte Unificado

**Autor:** Gemini, validado pelo Arquiteto do Projeto
**Status:** Proposta Final
**Versão:** 2.0

---

## 1. Mandato e Visão Estratégica

Esta SAGA-017 é a iniciativa de engenharia mais crítica do projeto Conductor até o momento. Seu mandato é eliminar o **cisma arquitetônico** entre a SAGA-016 e a base de código legada. A visão é executar uma **"cirurgia de transplante de coração"**, substituindo o núcleo lógico (`AgentLogic`) por um `ConductorService` robusto e service-oriented, enquanto se preserva a camada de UI existente (`admin.py`, `agent.py`, `REPLManager`) como "cascas finas".

Este plano é a especificação definitiva para essa transformação, garantindo que cada passo seja deliberado, testável e alinhado com a visão de futuro de uma plataforma escalável (Orquestrador -> Maestro -> Executor).

---

## 2. Fases e Estágios de Execução

### **Fase I: A Fundação - Forjando o Novo Núcleo de Serviços (Estágios 1-10)**

*   **Estágio 1:** Definir a Interface `IConductorService` em `src/ports/`.
*   **Estágio 2:** Implementar o Carregador e Validador de `config.yaml` (com schema Pydantic).
*   **Estágio 3:** Definir a Interface `IStateRepository` em `src/ports/`.
*   **Estágio 4:** Implementar a `StorageFactory` que instancia `FileSystemStateRepository` ou `MongoStateRepository` baseado na configuração.
*   **Estágio 5:** Implementar o método `discover_agents()` no `ConductorService` para consultar o backend de armazenamento.
*   **Estágio 6:** Implementar o Carregador de Ferramentas Híbrido (`Core` + `Plugins` de `config.yaml`).
*   **Estágio 7:** Definir o Contrato de Dados da Tarefa (ex: `TaskDTO` em `src/core/domain.py`).
*   **Estágio 8:** Criar a classe `AgentExecutor` em `src/core/agent_executor.py`, como uma evolução stateless do `AgentLogic`.
*   **Estágio 9:** Integrar o `PromptEngine` ao `AgentExecutor`, garantindo que persona, contexto e ferramentas sejam corretamente formatados no prompt.
*   **Estágio 10:** Implementar o método `execute_task(task: TaskDTO)` no `ConductorService`, que orquestra a descoberta, o carregamento de ferramentas e a execução via `AgentExecutor`.

### **Fase II: Containerização e Fundação DevOps (Estágios 11-14)**

*   **Estágio 11:** Criar um `Dockerfile` multicamada (`Dockerfile.service`) que cria uma imagem otimizada para rodar o `ConductorService`.
*   **Estágio 12:** Criar um `docker-compose.yml` para desenvolvimento, que sobe o `ConductorService` e uma instância do MongoDB, facilitando testes de integração.
*   **Estágio 13:** Escrever um script de "health check" para o serviço rodando no contêiner.
*   **Estágio 14:** Criar um teste de "smoke" (`tests/e2e/test_containerized_service.py`) que usa a imagem Docker para iniciar o serviço e fazer uma chamada básica de descoberta de agentes.

### **Fase III: A Cirurgia - O Transplante do Núcleo (Estágios 15-18)**

*   **Estágio 15:** Atualizar o `src/container.py` para construir e fornecer a instância singleton do `ConductorService`.
*   **Estágio 16:** Refatorar `src/cli/admin.py`, removendo `AgentLogic` e transformando-o em uma casca fina que traduz argumentos de CLI para uma chamada ao `ConductorService.execute_task`.
*   **Estágio 17:** Refatorar `src/cli/agent.py`, aplicando a mesma cirurgia.
*   **Estágio 18:** Validar a funcionalidade do `REPLManager` com os CLIs refatorados, garantindo que o modo interativo (`--repl`) e seus comandos customizados permaneçam intactos.

### **Fase IV: Validação Rigorosa e Garantia de Qualidade (Estágios 19-24)**

*   **Estágio 19:** Escrever testes unitários para `ConductorService` (Cobertura > 90%).
*   **Estágio 20:** Escrever testes unitários para `AgentExecutor` e sua interação com `PromptEngine` (Cobertura > 90%).
*   **Estágio 21:** Escrever testes de integração (`tests/e2e/`) para o fluxo completo via CLIs refatorados, testando ambos os backends de armazenamento.
*   **Estágio 22:** Implementar o "Golden Master Testing": script que compara a saída dos CLIs antigos com os novos para garantir ausência de regressão.
*   **Estágio 23:** Realizar benchmarking de performance (cold start, tempo de resposta) para garantir que a nova arquitetura não é significativamente mais lenta.
*   **Estágio 24:** Realizar uma análise de segurança básica, garantindo que o carregamento de `tool_plugins` não permite vulnerabilidades óbvias (ex: path traversal).

### **Fase V: Migração do Ecossistema de Agentes (Estágios 25-28)**

*   **Estágio 25:** Criar um script de migração (`scripts/migrate_legacy_agents.py`) que converte a estrutura de pastas antiga para a nova estrutura de artefatos da SAGA-016.
*   **Estágio 26:** Executar a migração para todos os meta-agentes em `projects/_common/agents/`.
*   **Estágio 27:** Executar a migração para os agentes do projeto de exemplo `desafio-meli` e validar que eles são descobertos e executados pelo novo `ConductorService`.
*   **Estágio 28:** Depreciar formalmente o `config/workspaces.yaml`, movendo toda a lógica de descoberta para o `config.yaml` e o backend de armazenamento.

### **Fase VI: Consolidação e Atualização da Documentação (Estágios 29-34)**

*   **Estágio 29:** Depreciar formalmente `src/core/agent_logic.py`, adicionando um `DeprecationWarning`.
*   **Estágio 30:** Após um período de carência e com todos os testes passando, remover o arquivo `src/core/agent_logic.py`.
*   **Estágio 31:** Atualizar o `README.md` principal com as novas instruções de uso e a filosofia arquitetônica.
*   **Estágio 32:** Atualizar os diagramas e textos em `docs/architecture/` para refletir a nova arquitetura service-oriented.
*   **Estágio 33:** Criar um novo guia (`docs/guides/creating_tool_plugins.md`) explicando como desenvolver e registrar ferramentas customizadas.
*   **Estágio 34:** Criar um novo guia (`docs/guides/agent_migration_guide.md`) explicando como migrar agentes legados para o novo padrão.

### **Fase VII: Preparação para a Arquitetura Maestro-Executor (Estágios 35-42)**

*   **Estágio 35:** Criar o ponto de entrada `src/cli/conductor.py` como um facade unificado.
*   **Estágio 36:** Definir os DTOs da API (`ExecuteTaskRequest`, `TaskStatusResponse`) em `src/core/domain.py`.
*   **Estágio 37:** Definir a interface `ITaskQueue` em `src/ports/` e criar uma implementação em memória para testes.
*   **Estágio 38:** Criar os artefatos de definição (`definition.yaml`, `persona.md`) para o `Maestro_Agent` em um novo diretório de agentes do sistema.
*   **Estágio 39:** Definir as `capabilities` e `allowed_tools` iniciais para o `Maestro_Agent` em seu `definition.yaml`, focando em manipulação de arquivos e estado.
*   **Estágio 40:** Criar os artefatos de definição (`definition.yaml`, `persona.md`) para o `Executor_Agent`.
*   **Estágio 41:** Definir as `capabilities` e `allowed_tools` para o `Executor_Agent`, focando em escrita de código e execução de comandos shell seguros.
*   **Estágio 42:** Escrever um teste de integração final que usa o `ConductorService` para descobrir e carregar as definições dos novos agentes `Maestro` e `Executor`, provando que eles são parte do ecossistema.
