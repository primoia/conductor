# Guia de Referência Unificado dos Artefatos de Agente (SAGA-16)

**Status:** Defined
**SAGA Relacionada:** SAGA-16

Este documento é a fonte única da verdade para a estrutura e o conteúdo de cada artefato que compõe uma **Instância de Agente**. Ele é agnóstico ao backend de armazenamento e usa a nomenclatura final padronizada.

---

## Nomenclatura Padrão

*   **`definition.yaml`**: A identidade estática do agente.
*   **`knowledge`**: A base de conhecimento semântica e curada do agente (o que ele sabe).
*   **`history`**: O log de eventos imutável de tarefas executadas (o que ele fez).
*   **`playbook.md`**: O manual de regras prescritivas (como ele deve agir).
*   **`persona.md`**: O guia de comportamento e estilo.
*   **`session`**: O estado volátil da tarefa atual.

---

## Detalhamento dos Artefatos

### 1. `definition.yaml`

*   **Propósito:** A identidade do agente, usada para filtragem rápida pelo Orquestrador.
*   **Manifestação (Filesystem):** Um arquivo `definition.yaml` dentro da pasta da instância do agente (ex: `.conductor_workspace/agents/MyAgent/definition.yaml`).
*   **Manifestação (MongoDB):** Um campo `definition` (objeto JSON) dentro do documento principal do agente na coleção `agents`.
*   **Exemplo e Campos:**
    ```yaml
    name: "DevOps_Monitoring_Agent"
    version: "1.0.0"
    description: "Agente especialista em configurar stacks de monitoramento."
    author: "PrimoIA"
    tags: ["devops", "monitoring", "prometheus"]
    capabilities: ["setup_structured_logging", "add_application_metrics"]
    ```

### 2. `persona.md`

*   **Propósito:** O guia de comportamento para o LLM.
*   **Manifestação (Filesystem):** Um arquivo `persona.md` na pasta da instância.
*   **Manifestação (MongoDB):** Um campo `persona` (string) no documento do agente.
*   **Exemplo:** Um documento Markdown detalhando a especialidade, os princípios e o modo de trabalho do agente.

### 3. `playbook.md`

*   **Propósito:** O manual de conhecimento prescritivo (regras e heurísticas).
*   **Manifestação (Filesystem):** Um arquivo `playbook.md` na pasta da instância.
*   **Manifestação (MongoDB):** Um campo `playbook` (string ou objeto) no documento do agente.
*   **Exemplo:** Um documento Markdown com as seções `## Best Practices` e `## Anti-Patterns`.

### 4. `knowledge`

*   **Propósito:** A memória semântica (o que o agente sabe sobre os artefatos que gerencia).
*   **Manifestação (Filesystem):** Um arquivo `knowledge.json` na pasta da instância.
*   **Manifestação (MongoDB):** Um campo `knowledge` (objeto JSON) no documento do agente.
*   **Exemplo:**
    ```json
    {
      "src/test/UserServiceTest.kt": {
        "summary": "Testes unitários para UserService.",
        "purpose": "Garante a lógica de criação e busca de usuários.",
        "last_modified_by_task": "task-456"
      }
    }
    ```

### 5. `history`

*   **Propósito:** A memória episódica (o log imutável do que o agente fez).
*   **Manifestação (Filesystem):** Um arquivo `history.log` (ou `.jsonl`) na pasta da instância, onde cada linha é um evento JSON. Este formato evita carregar um array JSON gigante na memória.
*   **Manifestação (MongoDB):** Documentos individuais em uma coleção dedicada `history`.
*   **Exemplo de um Evento/Documento:**
    ```json
    {
      "_id": "hist_task_001",
      "agent_id": "CodeRefactor_Agent",
      "task_id": "task-001",
      "status": "completed_success",
      "summary": "Refatorou calculateTotal para usar reduce.",
      "git_commit_hash": "b1a2c3d4",
      "completion_timestamp": "2025-09-07T10:05:30Z"
    }
    ```

### 6. `session`

*   **Propósito:** O estado volátil da tarefa atual.
*   **Manifestação (Filesystem):** Um arquivo `session.json` na pasta da instância. É criado no início de uma tarefa e destruído no final.
*   **Manifestação (MongoDB):** Um documento em uma coleção dedicada `sessions`, com um índice de TTL para auto-expiração.
*   **Exemplo:**
    ```json
    {
      "_id": "session_run124_task_metrics",
      "agent_id": "DevOps_Monitoring_Agent",
      "task_id": "add-application-metrics",
      "status": "in_progress",
      "expiresAt": "2025-09-08T11:00:00Z"
    }
    ```
