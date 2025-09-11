# Plano 004: Validar a Camada de Persistência com Teste End-to-End

## 1. Contexto e Problema

A implementação do Plano 003 introduziu a lógica de persistência no `ConductorService`. Embora os testes unitários existentes passem, não há um teste de integração dedicado que valide o fluxo completo de ponta a ponta: desde a execução de uma tarefa até a verificação de que os arquivos físicos (`session.json`, `knowledge.json`, `history.log`) foram corretamente escritos no disco.

## 2. Objetivo

Criar um novo teste end-to-end (`e2e`) que simule a execução de um agente e verifique se os artefatos de estado são corretamente persistidos no filesystem, dentro do `.conductor_workspace`, garantindo que a solução é funcional e robusta na prática.

## 3. Plano de Execução

### Tarefa 1: Criar o Arquivo de Teste

**Checklist:**
- [ ] Criar um novo arquivo de teste em `tests/e2e/test_persistence_flow.py`.

### Tarefa 2: Estruturar o Teste

**Local:** `tests/e2e/test_persistence_flow.py`

**Checklist:**
- [ ] Importar os módulos necessários (`pytest`, `os`, `json`, `shutil`, `ConductorService`, `TaskDTO`).
- [ ] Definir uma função de teste, por exemplo, `test_full_persistence_flow_for_agent_task`.
- [ ] Usar um `fixture` do `pytest` ou um bloco `try/finally` para garantir que o ambiente de teste (diretórios de agentes temporários) seja limpo ao final da execução, mesmo em caso de falha.

### Tarefa 3: Implementar a Lógica do Teste (Arrange & Act)

**Local:** Dentro da função de teste.

**Checklist:**
- [ ] **Arrange (Preparação):**
  - [ ] Definir um `agent_id` de teste (ex: `test_persistence_agent`).
  - [ ] Criar manualmente o diretório do agente de teste em `.conductor_workspace/agents/test_persistence_agent/`.
  - [ ] Criar um arquivo `agent.yaml` e `persona.md` mínimos dentro deste diretório para que o agente possa ser descoberto e carregado.
  - [ ] Instanciar o `ConductorService`.
  - [ ] Criar um `TaskDTO` para o agente de teste com um input simples.
- [ ] **Act (Ação):**
  - [ ] Executar a tarefa usando `conductor_service.execute_task(task)`.

### Tarefa 4: Implementar as Verificações (Assert)

**Local:** Dentro da função de teste, após a ação.

**Checklist:**
- [ ] Verificar se a execução da tarefa foi bem-sucedida (`result.status == "success"`).
- [ ] **Assert de Persistência:**
  - [ ] Verificar se o arquivo `.conductor_workspace/agents/test_persistence_agent/session.json` existe.
  - [ ] Carregar o conteúdo do `session.json` e verificar se ele contém os dados esperados (ex: `last_task_id`).
  - [ ] Verificar se o arquivo `.conductor_workspace/agents/test_persistence_agent/knowledge.json` existe e contém os dados esperados.
  - [ ] Verificar se o arquivo `.conductor_workspace/agents/test_persistence_agent/history.log` existe e contém uma entrada de log válida.

## 4. Critérios de Aceitação

1.  O novo arquivo de teste `tests/e2e/test_persistence_flow.py` foi criado.
2.  Ao executar `pytest tests/e2e/test_persistence_flow.py`, o teste passa com sucesso.
3.  O teste valida de forma inequívoca a criação e o conteúdo dos arquivos `session.json`, `knowledge.json` e `history.log` como resultado da execução de uma tarefa.
