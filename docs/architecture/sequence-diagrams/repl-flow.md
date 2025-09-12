# 🎮 Fluxo do REPL (REPLManager)

> Baseado em `src/cli/shared/repl_manager.py` e integração com `ConductorCLI`.

## Sequência de Interação no REPL

```mermaid
sequenceDiagram
    participant User
    participant REPL as REPLManager
    participant CLI as ConductorCLI

    User->>REPL: start_session()
    REPL-->>User: ajuda + limites (rate limit, circuit breaker)

    loop até sair
        User->>REPL: entrada (comandos ou mensagem múltiplas linhas)
        alt comando interno
            REPL->>REPL: state/history/clear/save/tools/scope/status/reset/emergency
            REPL-->>User: saída do comando
        else mensagem normal
            REPL->>CLI: chat(message)
            alt simulate_mode
                CLI-->>REPL: "SIMULATION: Would send ..."
            else execução real
                CLI->>CLI: monta TaskDTO(context)
                CLI->>CLI: conductor_service.execute_task(...)
                CLI-->>REPL: resposta
            end
            REPL-->>User: imprime resposta
            REPL->>REPL: atualiza rate-limit e contadores
        end
        REPL->>REPL: verifica circuit breaker/limites
    end
```

## Comandos Extras por Modo
- **advanced/dev**: adiciona `debug`, `prompt`.
- **dev**: adiciona `simulate`, `export-debug`.

## Proteções
- **Rate limit**: intervalo mínimo entre interações.
- **Circuit breaker**: bloqueio após N erros consecutivos com reset temporizado.
- **Emergency stop**: interrupção imediata da sessão.
