# Issue 001: Implement the `FileSystemStateRepository` Persistence Layer

## 1. Problem Description

The architecture investigation revealed that the `FileSystemStateRepository`, the central component responsible for saving and loading agent state to disk, is not implemented. The `save_state`, `load_state`, and `list_agents` methods contain only stubs and mocked data, rendering the new architecture's persistence layer inoperative.

This failure causes the system to rely on legacy and broken saving mechanisms in the CLI, resulting in incorrect behavior and state persistence in obsolete directories.

## 2. Requirements (Expected Behavior)

As the guardian of the SAGA-017 requirements, the correct implementation must follow the `IStateRepository` contract and the following guidelines:

1.  **Use of the Configured Workspace:** The implementation must operate exclusively within the `base_path` provided at its initialization (which corresponds to `storage.path` in `config.yaml`, i.e., `.conductor_workspace`).

2.  **Implementation of `save_state`:**
    *   Receives `agent_id` and a `state_data` dictionary.
    *   The `state_data` contains the keys `session` and `memory`.
    *   The method must create the `<base_path>/agents/<agent_id>/` directory if it does not exist.
    *   It must serialize and save the content of `state_data['session']` to the file `<base_path>/agents/<agent_id>/session.json`.
    *   It must serialize and save the content of `state_data['memory']` to the file `<base_path>/agents/<agent_id>/memory.json`.

3.  **Implementation of `load_state`:**
    *   Receives `agent_id`.
    *   It must read the `session.json` and `memory.json` files from within the agent's directory.
    *   It must reconstruct and return a single dictionary in the format `{ "session": {...}, "memory": {...} }`.
    *   It must return a dictionary with empty keys and values (`{ "session": {}, "memory": {} }`) if the files or directory do not exist.

4.  **Implementation of `list_agents`:**
    *   It must scan the `<base_path>/agents/` directory.
    *   It must return a list of strings with the names of all subdirectories, as each one represents an agent.

## 3. Acceptance Criteria

1.  The stubs and mocked data in `src/infrastructure/storage/filesystem_repository.py` are replaced with functional file manipulation logic.
2.  Calling `conductor_service.save_state(agent_id, data)` results in the creation/update of the `session.json` and `memory.json` files in the correct directory within `.conductor_workspace`.
3.  Calling `conductor_service.load_state(agent_id)` correctly reconstructs the state from the JSON files.
4.  The original bug that caused writing to the `_common` directory is resolved as a side effect of the correct implementation.