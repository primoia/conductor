# Plan 006: Fix Runtime Errors in `admin.py` CLI

## 1. Context and Problem

After fixing the "embody" bug (Plan 005), the execution of the `admin.py` CLI now proceeds but fails with two new runtime errors:

1.  **`AttributeError: 'Namespace' object has no attribute 'mode'`**: Occurs because the `ArgumentParser` in `admin.py` does not define the `--mode` argument, which is expected by the `REPLManager` logic.
2.  **`AttributeError: 'REPLManager' object has no attribute 'project_config'`**: Occurs because `REPLManager` expects a `project_config` that is not provided in the `admin.py` flow, as meta-agents operate at the framework level, not for a specific project.

## 2. Objective

Fix both runtime errors to allow the `admin.py` CLI to successfully start a REPL session with a meta-agent.

## 3. Execution Plan

### Task 1: Fix the `mode` `AttributeError`

**Location:** `src/cli/admin.py`

**Checklist:**
- [ ] In the `ArgumentParser`, add the definition for the `--mode` argument:
  ```python
  parser.add_argument("--mode", type=str, default="dev", help="The REPL execution mode (dev, advanced, basic).")
  ```

### Task 2: Fix the `project_config` `AttributeError`

**Location:** `src/cli/admin.py`

**Checklist:**
- [ ] In the call to `REPLManager`, pass `project_config=None` to explicitly indicate that there is no project context.
  ```python
  repl_manager = REPLManager(
      agent=agent,
      conductor_service=conductor_service,
      mode=args.mode,
      project_config=None  # Add this parameter
  )
  ```

## 4. Acceptance Criteria

1.  The `admin.py` CLI now accepts the `--mode` argument.
2.  The `REPLManager` is instantiated with `project_config=None` when run from `admin.py`.
3.  The command `python -m src.cli.admin --meta --agent AgentCreator_Agent --repl` runs without `AttributeError` and successfully starts the REPL session.