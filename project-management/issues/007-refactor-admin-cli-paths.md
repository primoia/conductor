# Plan 007: Remove Legacy Path Logic from AdminCLI

## 1. Goal

Refactor the `AdminCLI` to completely eliminate any hardcoded path logic (like `_common`) and make it depend exclusively on the `ConductorService` for all agent discovery and loading. The CLI should have no knowledge of the directory structure.

## 2. Problem

The `AdminCLI` still displays and uses legacy paths (`_common`) during its initialization. This causes confusion and maintains a dependency on an obsolete directory structure, creating a "split-brain" behavior where the CLI interface reports one thing, while the backend service executes another (the correct one).

## 3. Expected Outcome

The `AdminCLI` should be agnostic to the location of the agents. It only informs the `ConductorService` of an `agent_id` and trusts that the service will find it.

**Implementation Checklist:**

1.  **Refactor `src/cli/admin.py`:**
    -   Remove the logic in `__init__` that defines `self.environment` and `self.project` as `"_common"` when the `--meta` flag is used.
    -   Remove the `destination_path` parameter and any logic associated with it.
    -   Remove the lines in `main()` that print `Target: _common/agents/`. The CLI should no longer display this information.
2.  **Simplify `_build_enhanced_message`:**
    -   Remove the parts that add `AGENT_ENVIRONMENT`, `AGENT_PROJECT`, and `DESTINATION_PATH` to the message. The context is now managed entirely by the `ConductorService` and the agent's state.

## 4. Rules and Restrictions (Guardrails)

-   **USE OF `_common` IS PROHIBITED:** The name `_common` should no longer exist in the `AdminCLI` code.
-   **CLI MUST BE AGNOSTIC:** The `AdminCLI` must not build, manipulate, or have knowledge of any file system paths related to the agents. Its sole responsibility is to pass the `agent_id` to the `ConductorService`.

## 5. Final Acceptance Criterion

- After the refactoring, running the command `python -m src.cli.admin --meta --agent AgentCreator_Agent --repl` should start successfully, and the initialization log **must not** contain the line `Target: _common/agents/`.
- The execution of a simple task (e.g., "hello") should continue to work normally.