# Plan 003: Implement Persistence in ConductorService

## 1. Context and Problem

The previous code review (Plan 002) revealed that although the repository layer (`IStateRepository` and `FileSystemStateRepository`) was correctly refactored, the `ConductorService` does not use it to save an agent's state after executing a task. It only loads data but does not persist changes, making the agents "memoryless".

## 2. Objective

Implement the missing state persistence logic in the `execute_task` method of `ConductorService`, ensuring that changes to the agent's session, knowledge, and history are saved after each successful task.

## 3. Execution Plan

**Location:** `src/core/conductor_service.py`

**Checklist:**

- [ ] Locate the `execute_task` method.
- [ ] Inside the `try` block, after the line `result = executor.run(task)`, add a check for `if result.status == "success":`.
- [ ] Inside this `if`, add the logic to persist the data contained in the `result` object:
  - [ ] Call `self.repository.save_session(task.agent_id, result.updated_session)` to save the updated session state.
  - [ ] Call `self.repository.save_knowledge(task.agent_id, result.updated_knowledge)` to save the updated knowledge memory.
  - [ ] Call `self.repository.append_to_history(task.agent_id, result.history_entry)` to add the task record to the history.
- [ ] Ensure that the correct data from the `TaskResultDTO` (`updated_session`, `updated_knowledge`, `history_entry`) is passed to the repository methods.

## 4. Acceptance Criteria

1.  After the successful execution of a task via `ConductorService`, the `session.json`, `knowledge.json`, and `history.log` files in the agent's directory (within `.conductor_workspace`) are created/updated.
2.  The save logic is only triggered if `result.status` is `"success"`.
3.  The `TaskResultDTO` must be adapted, if necessary, to contain the `updated_session`, `updated_knowledge`, and `history_entry` fields so that `ConductorService` can access them.