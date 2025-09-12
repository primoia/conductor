# 🧭 Conductor CLI - Visão Geral (Overview)

> Mapeia o fluxo principal do `conductor` a partir do `src/cli/conductor.py` e do escopo descrito no `README.md`.

## 🔀 Fluxo de Entrada e Roteamento de Comandos

```mermaid
flowchart TD
    A[User] --> B[conductor args]
    B --> C[CLIArgumentParser.create_main_parser]
    C --> D{Branch}

    D -->|--list| E[list_agents_command]
    D -->|--info <id>| F[info_agent_command_new]
    D -->|--validate| G[validate_config_command]
    D -->|--install ...| H[install_templates_command_new]
    D -->|--backup| I[backup_agents_command]
    D -->|--restore| J[restore_agents_command]
    D -->|--agent ...| K[handle_agent_interaction]

    subgraph Operações de Sistema
      G --> G1[ConfigurationService]
      G --> G2[StorageService]
      G --> G3[ConductorService.discover_agents]
      H --> H1[.conductor_workspace/agents]
      I --> I1[scripts/backup_agents.sh]
      J --> J1[scripts/restore_agents.sh]
    end

    subgraph Execução de Agente
      K --> K1{chat?}
      K1 -->|não| K2[Execução Stateless]
      K1 -->|sim| K3[Execução Contextual/REPL]

      K2 --> K2a[TaskDTO context: timeout, env, project]
      K2a --> K2b[ConductorService.execute_task]

      K3 --> K3a[flags include_history/save_to_history]
      K3a --> K3b[TaskDTO context: history=true, meta?, simulate?, timeout]
      K3b --> K3c[ConductorService.execute_task]
    end
```

## 🧩 Componentes Principais
- **ConductorCLI**: Orquestra a experiência de linha de comando e constrói `TaskDTO`.
- **ConductorService**: Fachada que delega para serviços especializados.
- **Configuration/Storage/AgentDiscovery/ToolManagement/TaskExecution**: Serviços internos usados pelo `ConductorService`.

## 📌 Notas
- Quando `--chat` é usado, o fluxo habilita histórico (include/save) e pode entrar em REPL (`--interactive`).
- `--simulate` no REPL/Chat pode short-circuit no `ConductorCLI.chat()` ou ser propagado no `context` da tarefa.
