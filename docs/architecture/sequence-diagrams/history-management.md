# 📊 History Management - Sequence Diagrams

> **Purpose:** Document the communication flows for history save, load, and clear operations in the Conductor framework.

## 🔄 History Save Flow (Automatic)

This flow shows how conversation history is automatically saved after each task execution.

```mermaid
sequenceDiagram
    participant ConductorCLI
    participant ConductorService
    participant TaskExecutionService
    participant AgentExecutor
    participant StorageService
    participant Repository

    Note over ConductorCLI,Repository: AUTOMATIC SAVE FLOW

    ConductorCLI->>ConductorService: execute_task(task)
    ConductorService->>TaskExecutionService: execute_task(task)
    
    TaskExecutionService->>TaskExecutionService: _load_agent_definition(agent_id)
    TaskExecutionService->>TaskExecutionService: _load_session_data(agent_id)
    TaskExecutionService->>TaskExecutionService: _create_agent_executor()
    
    TaskExecutionService->>AgentExecutor: run(task)
    AgentExecutor->>AgentExecutor: build_prompt()
    AgentExecutor->>AgentExecutor: invoke_llm()
    AgentExecutor->>AgentExecutor: create_history_entry()
    
    Note over AgentExecutor: history_entry = {<br/>task_id, agent_id, timestamp,<br/>user_input, ai_response, status}
    
    AgentExecutor-->>TaskExecutionService: TaskResultDTO(history_entry)
    
    TaskExecutionService->>TaskExecutionService: _persist_task_result()
    TaskExecutionService->>StorageService: get_repository()
    StorageService-->>TaskExecutionService: repository
    TaskExecutionService->>Repository: append_to_history(agent_id, history_entry)
    Repository-->>TaskExecutionService: success
    
    TaskExecutionService-->>ConductorService: TaskResultDTO
    ConductorService-->>ConductorCLI: TaskResultDTO
```

## 📖 History Load Flow (REPL/CLI)

This flow shows how conversation history is retrieved when the user asks to view history.

```mermaid
sequenceDiagram
    participant ConductorCLI
    participant AgentDiscoveryService

    Note over ConductorCLI,AgentDiscoveryService: HISTORY RETRIEVAL FLOW

    ConductorCLI->>AgentDiscoveryService: get_conversation_history(agent_id)
    AgentDiscoveryService-->>ConductorCLI: history_list
```

## 🗑️ History Clear Flow (CLI)

This flow shows how conversation history is cleared when the user requests a clear.

```mermaid
sequenceDiagram
    participant ConductorCLI
    participant AgentDiscoveryService

    Note over ConductorCLI,AgentDiscoveryService: HISTORY CLEAR FLOW

    ConductorCLI->>AgentDiscoveryService: clear_conversation_history(agent_id)
    AgentDiscoveryService-->>ConductorCLI: success
```

## 🔍 Key Points

### 1. **Automatic Save:**
- **AgentExecutor** creates `history_entry`
- **TaskExecutionService** persists via repository (`append_to_history`)

### 2. **Manual Load/Clear via CLI:**
- **ConductorCLI** uses `AgentDiscoveryService.get_conversation_history/clear_conversation_history`
- No direct exposure of the `repository` by the `ConductorService`

## 🎯 Architecture Notes

The flow has been updated to reflect the current API of the `ConductorCLI` and internal services. If low-level access to the repository is needed by the CLI, consider adding dedicated methods in the `ConductorService` instead of exposing the `repository` directly.