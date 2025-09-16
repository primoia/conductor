# Plan 004: Validate the Persistence Layer with an End-to-End Test

## 1. Context and Problem

The implementation of Plan 003 introduced the persistence logic in `ConductorService`. Although existing unit tests pass, there is no dedicated integration test that validates the complete end-to-end flow: from the execution of a task to the verification that the physical files (`session.json`, `knowledge.json`, `history.log`) were correctly written to disk.

## 2. Objective

Create a new end-to-end (`e2e`) test that simulates the execution of an agent and verifies that the state artifacts are correctly persisted in the filesystem, within `.conductor_workspace`, ensuring that the solution is functional and robust in practice.

## 3. Execution Plan

### Task 1: Create the Test File

**Checklist:**
- [ ] Create a new test file at `tests/e2e/test_persistence_flow.py`.

### Task 2: Structure the Test

**Location:** `tests/e2e/test_persistence_flow.py`

**Checklist:**
- [ ] Import the necessary modules (`pytest`, `os`, `json`, `shutil`, `ConductorService`, `TaskDTO`).
- [ ] Define a test function, for example, `test_full_persistence_flow_for_agent_task`.
- [ ] Use a `pytest` fixture or a `try/finally` block to ensure that the test environment (temporary agent directories) is cleaned up at the end of the execution, even in case of failure.

### Task 3: Implement the Test Logic (Arrange & Act)

**Location:** Inside the test function.

**Checklist:**
- [ ] **Arrange:**
  - [ ] Define a test `agent_id` (e.g., `test_persistence_agent`).
  - [ ] Manually create the test agent's directory in `.conductor_workspace/agents/test_persistence_agent/`.
  - [ ] Create minimal `agent.yaml` and `persona.md` files within this directory so that the agent can be discovered and loaded.
  - [ ] Instantiate the `ConductorService`.
  - [ ] Create a `TaskDTO` for the test agent with a simple input.
- [ ] **Act:**
  - [ ] Execute the task using `conductor_service.execute_task(task)`.

### Task 4: Implement the Assertions

**Location:** Inside the test function, after the action.

**Checklist:**
- [ ] Verify that the task execution was successful (`result.status == "success"`).
- [ ] **Persistence Assertions:**
  - [ ] Check if the file `.conductor_workspace/agents/test_persistence_agent/session.json` exists.
  - [ ] Load the content of `session.json` and verify that it contains the expected data (e.g., `last_task_id`).
  - [ ] Check if the file `.conductor_workspace/agents/test_persistence_agent/knowledge.json` exists and contains the expected data.
  - [ ] Check if the file `.conductor_workspace/agents/test_persistence_agent/history.log` exists and contains a valid log entry.

## 4. Acceptance Criteria

1.  The new test file `tests/e2e/test_persistence_flow.py` has been created.
2.  When running `pytest tests/e2e/test_persistence_flow.py`, the test passes successfully.
3.  The test unequivocally validates the creation and content of the `session.json`, `knowledge.json`, and `history.log` files as a result of executing a task.