### Plano de Execução: Estágio 28.8 - Refatorar `repl_manager.py` e `state_manager.py`

#### Contexto Arquitetônico

A investigação revelou que `src/cli/shared/repl_manager.py` e `src/cli/shared/state_manager.py` ainda possuem referências diretas a `agent_logic`, que foi removido. Isso causa `ImportError` e impede a execução correta dos CLIs refatorados.

#### Propósito Estratégico

O objetivo é eliminar todas as dependências de `agent_logic` nos módulos compartilhados, garantindo que eles operem diretamente através da instância do CLI (que agora usa `ConductorService`). Isso resolverá o `ImportError` e permitirá que os CLIs funcionem corretamente com a nova arquitetura.

#### Checklist de Execução

- [x] Modificar `src/cli/shared/repl_manager.py`:
    -   Remover todas as referências a `agent_logic`.
    -   Ajustar os métodos (`_show_agent_state`, `_show_conversation_history`, `_clear_conversation_history`, `_show_debug_info`) para obter as informações diretamente de `self.cli_instance` (que agora é uma instância de `AdminCLI` ou `AgentCLI` refatorada).
    -   Remover o import de `AgentLogic`.
- [x] Modificar `src/cli/shared/state_manager.py`:
    -   Remover todas as referências a `agent_logic`.
    -   Ajustar os métodos (`save_agent_state`, `get_agent_status`, `get_conversation_history`, `clear_conversation_history`) para obter as informações diretamente de `self.cli_instance`.
    -   Remover o import de `AgentLogic`.
- [x] Executar `poetry run pytest` para confirmar que os testes passam após as correções.
