### Plano de Execução: Estágio 28.10 - Implementar Descoberta de Agentes em `FileSystemStateRepository`

#### Contexto Arquitetônico

Os testes de integração do Maestro-Executor estão falhando porque o `ConductorService` não consegue descobrir os agentes `Maestro_Agent` e `Executor_Agent`. A causa raiz é que a implementação atual de `FileSystemStateRepository.list_agents` sempre retorna uma lista vazia, e `load_state` não está configurado para carregar os artefatos JSON dos agentes.

#### Propósito Estratégico

O objetivo é fazer com que o `FileSystemStateRepository` seja capaz de descobrir e carregar corretamente os artefatos JSON dos agentes (`.conductor_workspace/agents/*.json`). Isso permitirá que os testes de integração do Maestro-Executor passem, validando a Fase VII e garantindo que o `ConductorService` possa operar com o backend de filesystem para a descoberta de agentes.

#### Checklist de Execução

- [x] Modificar `src/infrastructure/persistence/state_repository.py`:
    -   Implementar `FileStateRepository.list_agents` para escanear o diretório `.conductor_workspace/agents/` e retornar os IDs dos agentes (nomes dos arquivos JSON sem a extensão).
    -   Implementar `FileStateRepository.load_state` para carregar o conteúdo de um arquivo JSON de agente (`.conductor_workspace/agents/<agent_id>.json`).
- [x] Executar `poetry run pytest` para confirmar que os testes passam após as correções.
