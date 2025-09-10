# Plano: 0011-K - Finalização: Versionamento e HITL

## Contexto

Este plano foca em duas funcionalidades de "qualidade de vida" e segurança que são essenciais para a V1 da nova arquitetura.

1.  **Versionamento de Esquema:** Implementar a lógica que lê o campo `schema_version` de um `definition.yaml` para garantir que o Conductor não tente carregar um agente com uma estrutura de artefatos incompatível.
2.  **Human-in-the-Loop (HITL):** Implementar o prompt de confirmação `[y/N]` no terminal antes de ações críticas, como a execução de um plano por um agente.

## Checklist de Verificação

- [x] **Versionamento:**
    - [x] No `ConfigManager` ou em uma constante global, definir a `CURRENT_SUPPORTED_SCHEMA_VERSION` (ex: "1.0").
    - [x] Na lógica de carregamento do `AgentService`, comparar a `schema_version` do `definition.yaml` do agente com a versão suportada pelo Conductor.
    - [x] Se as versões não forem compatíveis, lançar uma `CompatibilityError` informando o usuário.
- [x] **HITL:**
    - [x] Criar uma função utilitária `confirm_action(prompt_message: str) -> bool` em um módulo de `shared` do `cli`.
    - [x] A função deve exibir a mensagem para o usuário, seguida por `[y/N]`, e ler a entrada do terminal.
    - [x] A função deve retornar `True` apenas se o usuário digitar 'y' (case-insensitive).
    - [x] No `Orchestrator`, antes de delegar a execução final de uma tarefa a um agente, invocar `confirm_action` com uma mensagem clara (ex: "Delegar a tarefa 'X' ao agente 'Y'?").
    - [x] O processo deve ser abortado se a confirmação for negada.
