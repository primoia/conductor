### Plano de Execução: Estágio 28.13 - Garantir Descoberta e Carregamento de Agentes Mockados em `FileSystemStateRepository`

#### Contexto Arquitetônico

Os testes `tests/e2e/test_full_flow.py::test_filesystem_flow` e os testes de integração do Maestro-Executor continuam falhando porque o `FileSystemStateRepository` não está descobrindo ou carregando corretamente os agentes mockados criados nos fixtures. Isso indica que a lógica de `list_agents` e `load_state` no `FileSystemStateRepository` precisa ser revisada para garantir que ela interaja corretamente com os arquivos de teste.

#### Propósito Estratégico

O objetivo é garantir que o `FileSystemStateRepository` seja capaz de descobrir e carregar os agentes mockados criados pelos testes, permitindo que os testes de integração passem. Isso é fundamental para validar a funcionalidade do `ConductorService` com o backend de filesystem e para a conclusão da Fase VII.

#### Checklist de Execução

- [x] **Revisar `src/infrastructure/persistence/state_repository.py`:**
    -   Garantir que o `__init__` de `FileStateRepository` use o `base_path` corretamente para definir o diretório onde os agentes são procurados.
    -   Verificar se `list_agents` está iterando sobre o diretório correto (`self.agents_path`) e coletando os nomes dos arquivos JSON.
    -   Verificar se `load_state` está lendo o arquivo JSON correto e retornando o conteúdo esperado.
- [x] **Revisar `tests/e2e/test_full_flow.py`:**
    -   No fixture `filesystem_service`, garantir que o `agent.yaml` criado para o agente mockado seja um arquivo JSON (`.json`) e que seu conteúdo seja compatível com o que `FileStateRepository` espera carregar.
    -   Ajustar o `agent_id` no `TaskDTO` para corresponder ao nome do arquivo JSON criado.
- [x] **Executar `poetry run pytest`:**
    -   Confirmar que todos os testes passam após as correções.
