# Plan 002: Refactor State Repository for Alignment with SAGA-16

## 1. Context and Problem

The previous implementation of `FileSystemStateRepository` was based on an incomplete specification that only considered `session` and `memory`. The official SAGA-16 reference document (`AGENT_ARTIFACTS_REFERENCE.md`) specifies a multi-artifact architecture (`session.json`, `knowledge.json`, `playbook.yaml`, `history.log`, etc.).

This implementation is therefore misaligned with the master architecture.

## 2. Objective

Refactor the persistence layer (`IStateRepository` and `FileSystemStateRepository`) so that it manages each agent artifact in a granular way, as specified in SAGA-16.

## 3. Execution Plan

### Task 1: Refactor the `IStateRepository` Interface

**Location:** `src/ports/state_repository.py`

**Checklist:**
- [ ] Remove the `save_state` and `load_state` methods.
- [ ] Add new methods for granular management of each main artifact:
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

### Task 2: Implement `FileSystemStateRepository`

**Location:** `src/infrastructure/storage/filesystem_repository.py`

**Checklist:**
- [ ] Implement all new methods of the `IStateRepository` interface.
- [ ] Each method must read or write the corresponding file in the `<base_path>/agents/<agent_id>/` directory (e.g., `save_session` writes to `session.json`, `load_playbook` reads from `playbook.yaml`).
- [ ] The `append_to_history` method must add a new line to the `history.log` file in JSON Lines format.
- [ ] The `load` methods must return appropriate empty values (e.g., `[]` for `load_history`, `{}` for `load_session`) if the file does not exist, without raising an error.
- [ ] The `list_agents` method must be maintained and implemented to list the subdirectories in `<base_path>/agents/`.

### Task 3: Update the `ConductorService`

**Location:** `src/core/conductor_service.py` (and wherever else is necessary)

**Checklist:**
- [ ] Update the service to use the new granular methods of the state repository instead of the old `save_state` and `load_state`.

## 4. Acceptance Criteria

1.  The `IStateRepository` interface reflects the new granular architecture.
2.  The `FileSystemStateRepository` class correctly implements the reading and writing of all artifacts (`session.json`, `knowledge.json`, `playbook.yaml`, `history.log`).
3.  The `ConductorService` uses the new interface to manage the agent's state.
4.  Existing tests are adapted and all continue to pass after the refactoring.