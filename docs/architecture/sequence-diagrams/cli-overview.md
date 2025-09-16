# 🧭 Conductor CLI - Overview

> Maps the main flow of `conductor` from `src/cli/conductor.py` and the scope described in `README.md`.

## 🔀 Input Flow and Command Routing

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

    subgraph System Operations
      G --> G1[ConfigurationService]
      G --> G2[StorageService]
      G --> G3[ConductorService.discover_agents]
      H --> H1[.conductor_workspace/agents]
      I --> I1[scripts/backup_agents.sh]
      J --> J1[scripts/restore_agents.sh]
    end

    subgraph Agent Execution
      K --> K1{chat?}
      K1 -->|no| K2[Stateless Execution]
      K1 -->|yes| K3[Contextual/REPL Execution]

      K2 --> K2a[TaskDTO context: timeout, env, project]
      K2a --> K2b[ConductorService.execute_task]

      K3 --> K3a[flags include_history/save_to_history]
      K3a --> K3b[TaskDTO context: history=true, meta?, simulate?, timeout]
      K3b --> K3c[ConductorService.execute_task]
    end
```

## 🧩 Main Components
- **ConductorCLI**: Orchestrates the command-line experience and builds `TaskDTO`.
- **ConductorService**: A facade that delegates to specialized services.
- **Configuration/Storage/AgentDiscovery/ToolManagement/TaskExecution**: Internal services used by `ConductorService`.

## 📌 Notes
- When `--chat` is used, the flow enables history (include/save) and can enter REPL (`--interactive`).
- `--simulate` in REPL/Chat can short-circuit in `ConductorCLI.chat()` or be propagated in the task's `context`.