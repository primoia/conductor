# ⚙️ Modos de Execução do Conductor

> Diagramas de sequência para: Stateless, Chat (com histórico) e Simulação.

## 1) Execução Stateless (rápida, sem histórico)

```mermaid
sequenceDiagram
    participant User
    participant ConductorCLI
    participant AgentDiscovery as AgentDiscoveryService
    participant Conductor as ConductorService
    participant TaskExec as TaskExecutionService

    User->>ConductorCLI: conductor --agent X --input "..." [--timeout]
    ConductorCLI->>AgentDiscovery: agent_exists(X)
    AgentDiscovery-->>ConductorCLI: boolean
    alt agente existe
        ConductorCLI->>Conductor: execute_task(TaskDTO{context:{timeout, env?, project?}})
        Conductor->>TaskExec: execute_task(task)
        TaskExec-->>Conductor: TaskResultDTO(status, output)
        Conductor-->>ConductorCLI: TaskResultDTO
        ConductorCLI-->>User: output
    else agente não existe
        ConductorCLI-->>User: erro + sugestões
    end
```

## 2) Chat Contextual (com histórico)

```mermaid
sequenceDiagram
    participant User
    participant ConductorCLI
    participant Conductor as ConductorService
    participant TaskExec as TaskExecutionService

    User->>ConductorCLI: --agent X --chat --input "..." [--timeout]
    Note over ConductorCLI: include_history=true\nsave_to_history=true
    ConductorCLI->>Conductor: execute_task(TaskDTO{context:{history:true, meta?, env?, project?, timeout}})
    Conductor->>TaskExec: execute_task(task)
    TaskExec->>TaskExec: carregar contexto/sessão do agente
    TaskExec-->>Conductor: TaskResultDTO(output)
    Conductor-->>ConductorCLI: TaskResultDTO
    ConductorCLI-->>User: output (persistido no histórico)
```

## 3) Simulação (sem chamada real à IA)

```mermaid
sequenceDiagram
    participant User
    participant ConductorCLI
    participant Conductor as ConductorService
    participant TaskExec as TaskExecutionService

    User->>ConductorCLI: --chat --interactive --simulate
    alt via ConductorCLI.chat()
        Note over ConductorCLI: simulate_mode==true
        ConductorCLI-->>User: "🎭 SIMULATION: Would send '...'"
    else via contexto de tarefa
        ConductorCLI->>Conductor: execute_task(TaskDTO{context:{simulate_mode:true}})
        Conductor->>TaskExec: execute_task(task)
        TaskExec-->>Conductor: TaskResultDTO(simulado ou no-op)
        Conductor-->>ConductorCLI: TaskResultDTO
        ConductorCLI-->>User: mensagem de simulação
    end
```

## 📝 Observações
- `--timeout` sempre é propagado em `TaskDTO.context` e pode influenciar o executor de tarefas.
- `--meta` e `--new-agent-id` ajustam o contexto e a construção de prompt quando aplicável.
