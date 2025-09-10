### Plano de Execução: Estágio 28.3 - Corrigir Múltiplos Erros nos Testes

#### Contexto Arquitetônico

Após a execução dos testes para validar o Passo 28, uma série de erros e falhas foram identificados em diversas partes da suíte de testes. Isso indica que as refatorações anteriores introduziram incompatibilidades ou que os testes não foram atualizados para refletir as mudanças na arquitetura. Os principais problemas incluem:

-   `TypeError` ao instanciar `MockStateRepository` e `FileStateRepository` (devido à falta de implementação de `list_agents`).
-   `TypeError` em `AgentDefinition.__init__` (devido à duplicação da classe `AgentDefinition` e à nova não aceitar `agent_id` no construtor).
-   `FileNotFoundError` para `docker-compose` em testes containerizados.
-   Falhas em testes de `PromptEngine` relacionados a carregamento de contexto.
-   Falha em `test_conductor_service.py` (`test_load_tools_invalid_plugin_path`) devido a uma asserção incorreta.

#### Propósito Estratégico

O objetivo é restaurar a estabilidade da suíte de testes, corrigindo todos os erros e falhas identificados. Uma suíte de testes funcional é crucial para garantir a qualidade e a confiabilidade do projeto, permitindo que futuras refatorações e desenvolvimentos sejam feitos com confiança. Esta correção é fundamental para que a validação do Passo 28 possa ser concluída com sucesso.

#### Checklist de Execução

- [x] **Corrigir `TypeError` em `MockStateRepository` e `FileStateRepository`:**
    -   Implementar o método `list_agents` nessas classes (pode ser um `return []` ou `return []` e `return {}` para `load_state` para mocks simples).
- [x] **Corrigir `TypeError` em `AgentDefinition.__init__`:**
    -   Remover a definição duplicada de `AgentDefinition` em `src/core/domain.py`, mantendo apenas a versão mais recente (sem `agent_id` no `__init__`).
    -   Ajustar os testes que ainda esperam `agent_id` no construtor de `AgentDefinition` para usar os campos corretos.
- [x] **Corrigir `FileNotFoundError` para `docker-compose`:**
    -   Garantir que `docker-compose` esteja disponível no PATH do ambiente de teste ou ajustar os testes para usar `docker compose` (com espaço) se for a versão mais recente.
- [x] **Corrigir falhas em `PromptEngine`:**
    -   Revisar `test_prompt_engine.py` e `src/core/prompt_engine.py` para garantir que o carregamento de contexto e a validação funcionem corretamente.
- [x] **Corrigir `test_load_tools_invalid_plugin_path`:**
    -   Ajustar a asserção no teste para verificar a mensagem de log correta (`logger.error` em vez de `print`).
- [x] **Executar `poetry run pytest`:**
    -   Confirmar que todos os testes passam após as correções.
