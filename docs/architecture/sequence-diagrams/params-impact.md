# 🧩 Parâmetros do ConductorCLI e Seus Efeitos

> Referência rápida do impacto dos parâmetros do `ConductorCLI` nos fluxos de execução.

## Mapa de Impacto (Mermaid)

```mermaid
flowchart LR
    A[Parametros CLI] --> B[ConductorCLI.__init__]
    B --> C{Efeitos}

    A1[--agent <id>] -->|alimenta| B
    A2[--environment] -->|context| B
    A3[--project] -->|context| B
    A4[--meta] -->|context/meta| B
    A5[--new-agent-id] -->|context/meta| B
    A6[--simulate] -->|simulate_mode| B
    A7[--timeout] -->|context.timeout| B
    A8[--chat] -->|include/save history| D
    A9[--interactive] -->|REPL| E

    C --> D[TaskDTO context]
    C --> E[REPLManager]
    C --> F[Logging via configure_logging debug_mode]

    E -->|dev/advanced| E1[comandos debug, prompt, simulate]
    D -->|entregue a| G[ConductorService.execute_task]
```

## Tabela de Parâmetros e Efeitos

| Parâmetro | Onde atua | Efeito principal |
|---|---|---|
| `--agent <id>` | `ConductorCLI.embodied`, `AgentDiscoveryService` | Seleciona agente, valida existência e definição |
| `--environment` | `TaskDTO.context.environment` | Contexto de ambiente para o executor |
| `--project` | `TaskDTO.context.project` | Contexto de projeto para o executor |
| `--meta` | `TaskDTO.context.meta` | Habilita comportamento de meta-agente e prompt especial |
| `--new-agent-id` | `TaskDTO.context.new_agent_id` | Usado quando `meta=true` para criação/alteração de agente |
| `--simulate` | `ConductorCLI.simulate_mode` e `TaskDTO.context.simulate_mode` | Simula resposta (short-circuit no chat ou via executor) |
| `--timeout` | `TaskDTO.context.timeout` | Teto de tempo para execução/integração com provider |
| `--chat` | Flags internas `include_history`/`save_to_history` | Ativa histórico e permite REPL/Chat |
| `--interactive` | `REPLManager.start_session` | Inicia REPL com proteções e comandos |
| `--debug mode` (implícito em `repl --mode dev`) | `configure_logging(debug_mode)` | Aumenta verbosidade de logs |

## Observações
- O histórico é exibido/limpo via `ConductorCLI.get/clear_conversation_history()` e persistido pelo executor.
- `get_full_prompt()` usa `meta`/`new_agent_id` para construir o prompt completo quando suportado pelo agente.
