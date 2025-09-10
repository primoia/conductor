### Plano de Execução: Estágio 28.11 - Corrigir Testes de `FileStateRepository` e Inicialização do `ConductorService`

#### Contexto Arquitetônico

Após a implementação da descoberta de agentes no `FileSystemStateRepository` (Passo 28.10), os testes ainda falham devido a duas causas principais:

1.  **Assinaturas de Método Incompatíveis:** Os testes em `tests/test_state_management.py` ainda usam as assinaturas antigas para `save_state` e `load_state` do `FileStateRepository`, que foram alteradas para receber apenas `agent_id` e `state_data` (ou `agent_id`).
2.  **Inicialização Incorreta do `ConductorService`:** Os testes de integração do Maestro-Executor falham porque o `ConductorService` não está sendo inicializado com o `base_path` correto para o `FileSystemStateRepository`, impedindo a descoberta dos agentes.

#### Propósito Estratégico

O objetivo é corrigir essas incompatibilidades para restaurar a estabilidade da suíte de testes. Isso é crucial para validar a Fase VII e garantir que o `ConductorService` possa operar corretamente com o backend de filesystem para a descoberta de agentes.

#### Checklist de Execução

- [x] **Corrigir `tests/test_state_management.py`:**
    -   Ajustar as chamadas para `self.repo.save_state` e `self.repo.load_state` para corresponder às novas assinaturas de `FileStateRepository`.
    -   Remover `agent_home_path` e `state_file_name` dos argumentos, passando apenas `agent_id` e `state_data` (ou `agent_id`).
- [x] **Corrigir `src/core/conductor_service.py`:**
    -   No método `_create_storage_backend`, ao instanciar `FileSystemStateRepository`, passar o `path` da configuração (`storage_config.path`) como argumento `base_path`.
- [x] **Executar `poetry run pytest`:**
    -   Confirmar que todos os testes passam após as correções.
