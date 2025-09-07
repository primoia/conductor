# SAGA-016: Plano Arquitetônico Final e Unificado

**Status:** Defined & Consolidated

Este documento é a fonte única e definitiva da verdade para a nova arquitetura de agentes do Conductor, conforme definido na SAGA-16. Ele consolida todas as discussões, refinamentos e decisões, e serve como o guia mestre para a implementação (Fase 2).

---

## 1. O Problema

A arquitetura inicial de agentes do Conductor, embora funcional, apresentava desafios de escalabilidade, segurança, manutenção e onboarding, principalmente devido ao acoplamento entre a definição do agente e seu estado, e à falta de um sistema de extensibilidade claro.

---

## 2. A Arquitetura Proposta: Princípios Fundamentais

A nova arquitetura se baseia em quatro princípios fundamentais:

1.  **Separação Clara entre Definição e Estado:** A identidade de um agente (seu "Template" versionado em Git) é separada de sua experiência e contexto (sua "Instância" não versionada).
2.  **Backend de Persistência Flexível:** O sistema abstrai a camada de armazenamento, oferecendo um modo `filesystem` (padrão, sem dependências) e um modo `mongodb` (avançado, para escalabilidade).
3.  **Sistema de Ferramentas Extensível (Plugins):** O framework fornece um core de ferramentas essenciais e permite que usuários carreguem suas próprias ferramentas de forma segura, evitando o inchaço do core.
4.  **Agentes Não Executam Código, Eles Usam Ferramentas:** Um princípio de segurança inegociável. A lógica de um agente é decidir e orquestrar, enquanto a execução de ações é delegada a `Tools` seguras, testadas e versionadas.

---

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

---

## 4. Configuração e Extensibilidade

### 4.1. `config.yaml`
*   **Propósito:** Controla o comportamento fundamental do Conductor.
*   **Estrutura:**
    ```yaml
    storage_backend:
      type: filesystem # ou mongodb
      workspace_path: ".conductor_workspace"
      # connection_string: ...

    tool_plugins:
      - "/path/to/my/custom_tools/"

    # Configuração de segurança granular para tools
    tool_config:
      shell.run:
        allowed_commands: ["git", "ls", "cat", "npm"]
    ```

### 4.2. Convenção de Commits
*   **Formato:** Conventional Commits + Git Trailers (`Conductor-Task-ID`, `Conductor-Agent-ID`, `Conductor-History-ID`).

---

## 5. Meta-Agentes e Fluxos de Trabalho

### 5.1. Meta-Agentes Essenciais
*   **`CommitMessage_Agent`**: Gera mensagens de commit padronizadas.
*   **`AgentCreator_Agent`**: Cria novos agentes a partir de um requisito.
*   **`AgentTuner_Agent`**: Refina os artefatos (`persona`, `playbook.yaml`) de agentes existentes.

### 5.2. Arquitetura do Orquestrador
*   O Orquestrador executa planos, e para cada tarefa, segue o fluxo: **Análise -> Filtragem Rápida (por `definition.yaml`) -> Decisão Semântica (por `persona.md`) -> Fallback de Criação -> Execução**.

### 5.3. Estratégia de Implementação
*   **Versionamento de Esquema:** Artefatos terão `schema_version` para controle de compatibilidade.
*   **HITL:** A V1 usará um prompt `[y/N]` no terminal para aprovações humanas.
*   **Sessões Órfãs:** O Conductor fará uma limpeza de sessões antigas no modo `filesystem` durante a inicialização.
