# Plano 002: Refatorar State Repository para Alinhamento com a SAGA-16

## 1. Contexto e Problema

A implementação anterior do `FileSystemStateRepository` foi baseada em uma especificação incompleta que considerava apenas `session` e `memory`. O documento de referência oficial da SAGA-16 (`AGENT_ARTIFACTS_REFERENCE.md`) especifica uma arquitetura de múltiplos artefatos (`session.json`, `knowledge.json`, `playbook.yaml`, `history.log`, etc.).

Esta implementação está, portanto, desalinhada com a arquitetura mestre.

## 2. Objetivo

Refatorar a camada de persistência (`IStateRepository` e `FileSystemStateRepository`) para que ela gerencie cada artefato do agente de forma granular, conforme especificado na SAGA-16.

## 3. Plano de Execução

### Tarefa 1: Refatorar a Interface `IStateRepository`

**Local:** `src/ports/state_repository.py`

**Checklist:**
- [ ] Remover os métodos `save_state` e `load_state`.
- [ ] Adicionar novos métodos para o gerenciamento granular de cada artefato principal:
  - `load_definition(agent_id: str) -> Dict`
  - `load_persona(agent_id: str) -> str`
  - `save_session(agent_id: str, session_data: Dict) -> bool`
  - `load_session(agent_id: str) -> Dict`
  - `save_knowledge(agent_id: str, knowledge_data: Dict) -> bool`
  - `load_knowledge(agent_id: str) -> Dict`
  - `save_playbook(agent_id: str, playbook_data: Dict) -> bool`
  - `load_playbook(agent_id: str) -> Dict`
  - `append_to_history(agent_id: str, history_entry: Dict) -> bool`
  - `load_history(agent_id: str) -> List[Dict]`

### Tarefa 2: Implementar `FileSystemStateRepository`

**Local:** `src/infrastructure/storage/filesystem_repository.py`

**Checklist:**
- [ ] Implementar todos os novos métodos da interface `IStateRepository`.
- [ ] Cada método deve ler ou escrever o arquivo correspondente no diretório `<base_path>/agents/<agent_id>/` (ex: `save_session` escreve em `session.json`, `load_playbook` lê de `playbook.yaml`).
- [ ] O método `append_to_history` deve adicionar uma nova linha ao arquivo `history.log` no formato JSON Lines.
- [ ] Os métodos de `load` devem retornar valores vazios apropriados (ex: `[]` para `load_history`, `{}` para `load_session`) se o arquivo não existir, sem gerar erro.
- [ ] O método `list_agents` deve ser mantido e implementado para listar os subdiretórios em `<base_path>/agents/`.

### Tarefa 3: Atualizar o `ConductorService`

**Local:** `src/core/conductor_service.py` (e onde mais for necessário)

**Checklist:**
- [ ] Atualizar o serviço para usar os novos métodos granulares do repositório de estado em vez dos antigos `save_state` e `load_state`.

## 4. Critérios de Aceitação

1.  A interface `IStateRepository` reflete a nova arquitetura granular.
2.  A classe `FileSystemStateRepository` implementa corretamente a leitura e escrita de todos os artefatos (`session.json`, `knowledge.json`, `playbook.yaml`, `history.log`).
3.  O `ConductorService` utiliza a nova interface para gerenciar o estado do agente.
4.  Os testes existentes são adaptados e todos continuam passando após a refatoração.
