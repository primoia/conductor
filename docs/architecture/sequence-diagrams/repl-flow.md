# 🎮 REPL Flow (REPLManager)

> Based on `src/cli/shared/repl_manager.py` and integration with `ConductorCLI`.

## REPL Interaction Sequence

```mermaid
sequenceDiagram
    participant User
    participant REPL as REPLManager
    participant CLI as ConductorCLI

    User->>REPL: start_session()
    REPL-->>User: help + limits (rate limit, circuit breaker)

    loop until exit
        User->>REPL: input (commands or multi-line message)
        alt internal command
            REPL->>REPL: state/history/clear/save/tools/scope/status/reset/emergency
            REPL-->>User: command output
        else normal message
            REPL->>CLI: chat(message)
            alt simulate_mode
                CLI-->>REPL: "SIMULATION: Would send ..."
            else real execution
                CLI->>CLI: builds TaskDTO(context)
                CLI->>CLI: conductor_service.execute_task(...)
                CLI-->>REPL: response
            end
            REPL-->>User: prints response
            REPL->>REPL: updates rate-limit and counters
        end
        REPL->>REPL: checks circuit breaker/limits
    end
```

## Extra Commands by Mode
- **advanced/dev**: adds `debug`, `prompt`.
- **dev**: adds `simulate`, `export-debug`.

## Protections
- **Rate limit**: minimum interval between interactions.
- **Circuit breaker**: blocks after N consecutive errors with a timed reset.
- **Emergency stop**: immediate session interruption.