### Plano de Execução: Estágio 28.2 - Corrigir Imports de `StateRepository` nos Testes Legados

#### Contexto Arquitetônico

Durante a validação do Passo 28, foi identificado que os testes legados `tests/test_core.py` e `tests/test_state_management.py` estão falhando devido a um `ImportError` (`cannot import name 'StateRepository'`). Isso ocorre porque a interface `IStateRepository` foi renomeada de `StateRepository` para `IStateRepository` em um passo anterior (Passo 3), mas os testes ainda referenciam o nome antigo.

#### Propósito Estratégico

O objetivo é corrigir os testes legados para que eles reflitam o nome correto da interface `IStateRepository`. Isso é crucial para restaurar a estabilidade da suíte de testes e permitir que a validação do Passo 28 seja concluída com sucesso. Esta correção garante que a base de testes permaneça funcional enquanto a migração para a nova arquitetura avança.

#### Checklist de Execução

- [x] Modificar `tests/test_core.py`.
- [x] Alterar a importação de `StateRepository` para `IStateRepository`.
- [x] Modificar `tests/test_state_management.py`.
- [x] Alterar a importação de `StateRepository` para `IStateRepository`.
- [x] Executar `poetry run pytest` para confirmar que os testes passam após a correção.
