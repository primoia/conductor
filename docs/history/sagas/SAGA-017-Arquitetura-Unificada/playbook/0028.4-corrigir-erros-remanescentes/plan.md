### Plano de Execução: Estágio 28.4 - Corrigir Erros Remanescentes nos Testes

#### Contexto Arquitetônico

Após as correções anteriores, ainda existem falhas nos testes que impedem a conclusão do Passo 28. Os problemas remanescentes são:

-   `tests/test_container.py`: Falhas relacionadas a `load_workspaces_config_missing_file` e `resolve_agent_paths_common`. Isso ocorre porque os testes ainda esperam que esses métodos existam, mas eles foram removidos no Passo 28.1.
-   `tests/e2e/test_containerized_service.py`: Erro no `test_service_smoke_run` relacionado à falha do `docker compose up`. Isso pode ser devido a um problema no ambiente Docker ou na construção da imagem.

#### Propósito Estratégico

O objetivo é eliminar todas as falhas de teste restantes para restaurar a estabilidade completa da suíte de testes. Isso é essencial para validar a depreciação do `workspaces.yaml` e garantir que o projeto esteja em um estado saudável para futuras refatorações.

#### Checklist de Execução

- [x] **Corrigir `tests/test_container.py`:**
    -   Remover ou ajustar os testes `test_load_workspaces_config_missing_file` e `test_resolve_agent_paths_common`, pois os métodos correspondentes foram removidos.
- [x] **Corrigir `tests/e2e/test_containerized_service.py`:**
    -   Investigar a causa da falha do `docker compose up`. Pode ser necessário:
        -   Garantir que o Docker esteja rodando e acessível.
        -   Verificar logs de build do Docker para erros.
        -   Adicionar um `try-except` mais robusto ou um `pytest.mark.skipif` se o Docker não for um requisito universal para o teste.
- [x] **Executar `poetry run pytest`:**
    -   Confirmar que todos os testes passam após as correções.
