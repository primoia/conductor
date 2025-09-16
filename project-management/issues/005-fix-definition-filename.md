# Plan 005: Correct Definition File Name in Repository

## 1. Context and Problem

E2E tests revealed a "Failed to embody meta-agent" error. The root cause is an inconsistency between the SAGA-16 specification and the `FileSystemStateRepository` implementation.

-   **Specification (SAGA-16):** The agent definition file should be named `definition.yaml`.
-   **Current Implementation:** The `load_definition` method in `FileSystemStateRepository` is looking for `agent.yaml`.

This discrepancy prevents any agent from being loaded.

## 2. Objective

Correct the file name in the code to align it with the SAGA-16 specification, fixing the "embody" bug.

## 3. Execution Plan

**Location:** `src/infrastructure/storage/filesystem_repository.py`

**Checklist:**
- [ ] Locate the `load_definition` method.
- [ ] Change the line `definition_file = os.path.join(agent_dir, "agent.yaml")` to `definition_file = os.path.join(agent_dir, "definition.yaml")`.
- [ ] Update the method's docstring to reflect the change from `(agent.yaml)` to `(definition.yaml)`.

## 4. Acceptance Criteria

1.  The `FileSystemStateRepository` now looks for `definition.yaml` to load the agent's definition.
2.  After the fix, the command `python -m src.cli.admin --meta --agent AgentCreator_Agent --repl` should be able to successfully embody the agent.