## 3. Guia de Referência Unificado dos Artefatos

Esta seção detalha cada artefato que compõe uma Instância de Agente, sua nomenclatura padrão e sua manifestação em cada tipo de backend.

### 3.1. `definition.yaml`
*   **Propósito:** A identidade do agente para filtragem rápida.
*   **Manifestação:** Arquivo em `.../agents/MyAgent/` (filesystem) ou campo `definition` (MongoDB).
*   **Campos e Exemplo:**
    ```yaml
    name: "DevOps_Monitoring_Agent"
    version: "1.0.0"
    schema_version: "1.0" # Para controle de versão do esquema do artefato
    description: "Agente especialista em configurar stacks de monitoramento."
    author: "PrimoIA"
    tags: ["devops", "monitoring", "prometheus"]
    capabilities: ["setup_structured_logging", "add_application_metrics"]
    allowed_tools: ["file.read", "file.write", "shell.run"]
    ```

### 3.2. `persona.md`
*   **Propósito:** O guia de comportamento para o LLM.
*   **Manifestação:** Arquivo em `.../agents/MyAgent/` (filesystem) ou campo `persona` (MongoDB).
*   **Exemplo:** Um documento Markdown detalhando a especialidade, os princípios e o modo de trabalho do agente.

### 3.3. `playbook.yaml`
*   **Propósito:** O manual de conhecimento prescritivo (regras), armazenado de forma estruturada (YAML) para ser atualizado de forma segura.
*   **Manifestação:** Arquivo `playbook.yaml` na pasta da instância (filesystem) ou campo `playbook` (objeto, MongoDB).
*   **Exemplo:**
    ```yaml
    best_practices:
      - id: BP001
        title: Use Tipos Apropriados
        description: Para relacionamentos, use Set<T>...
    anti_patterns:
      - id: AP001
        title: Evite Fetch Eager
        description: Nunca use FetchType.EAGER...
    ```

### 3.4. `knowledge.json`
*   **Propósito:** A memória semântica (o que o agente sabe sobre os artefatos que gerencia).
*   **Manifestação:** Arquivo `knowledge.json` na pasta da instância (filesystem) ou campo `knowledge` (objeto, MongoDB).
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

### 3.5. `history.log`
*   **Propósito:** A memória episódica (o log imutável do que o agente fez).
*   **Manifestação:** Arquivo `history.log` (formato JSON Lines) na pasta da instância (filesystem) ou documentos em uma coleção `history` (MongoDB).
*   **Exemplo de uma linha/documento:**
    ```json
    {"_id": "hist_task_001", "agent_id": "CodeRefactor_Agent", "task_id": "task-001", "status": "completed_success", "summary": "Refatorou calculateTotal.", "git_commit_hash": "b1a2c3d4"}
    ```

### 3.6. `session.json`
*   **Propósito:** O estado volátil da tarefa atual.
*   **Manifestação:** Arquivo `session.json` na pasta da instância (filesystem) ou documento em uma coleção `sessions` com TTL (MongoDB).