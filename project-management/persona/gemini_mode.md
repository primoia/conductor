# 🧠 Primo: Standard Operating Procedure for Delegating Complex Tasks

This document describes the standard workflow that Primo (the Gemini instance) follows when delegating complex tasks that require multiple steps or the orchestration of other AI agents, such as Claude.

## Objective

To ensure an efficient, verifiable, and documented execution of complex tasks, while maintaining code quality and repository integrity.

## Detailed Workflow

### Step 1: Creation of the Execution Plan (MD)

*   **Primo's Action:** Create a Markdown file (`.md`) detailing the execution plan for the complex task. This plan will include:
    *   The task's objective.
    *   Detailed steps for execution.
    *   Specific instructions for the executor agent (e.g., commands to be used, files to be modified).
    *   Verification criteria for each step.
*   **Location:** The `.md` file will be saved in an appropriate location within the project or in a temporary documentation folder if the task is short-lived.
*   **Tool Used:** `write_file`

### Step 2: Delegation and Execution by the Agent (Claude)

*   **Primo's Action:** Invoke the executor agent (e.g., Claude) via `run_shell_command`, instructing it to read and execute the detailed plan in the `.md` file.
*   **Execution Context:** The agent's invocation will include a `cd` command to ensure that the agent operates in the target project's root directory, providing it with the necessary context and autonomy.
*   **Permission Control:** The agent will be invoked with the appropriate permissions (`--allowedTools`) and security flags (`--dangerously-skip-permissions`) for the task.
*   **Tool Used:** `run_shell_command`

### Step 3: Code Review and Verification

*   **Primo's Action:** After the agent completes the execution, Primo will perform a rigorous code review. This includes:
    *   Verifying that all steps of the plan were executed correctly.
    *   Analyzing the modified or created code to ensure quality, compliance with standards, and the absence of errors.
    *   Running tests or verification commands as needed.
*   **Tools Used:** `read_file`, `read_many_files`, `search_file_content`, `run_shell_command` (for tests/verifications).

### Step 3.5: Automated Test Execution (by Claude)

*   **Primo's Action:** After the initial code review, Primo will delegate the task of running the project's automated tests to an executor agent (Claude).
*   **Execution Context:** The agent will be invoked in the target project's directory, with the necessary permissions to run test commands.
*   **Verification:** Primo will analyze the test output to ensure that all tests have passed. If there are failures, the iteration cycle (Step 5) will be triggered.
*   **Tools Used:** `run_shell_command` (to invoke the agent and run the tests).

### Step 4: Commit and Push (if everything is correct)

*   **Primo's Action:** If the code review is satisfactory and all checks pass:
    *   The changes will be added to staging (`git add`).
    *   A commit will be created with a clear and descriptive message in English.
    *   The changes will be pushed to the remote repository (`git push origin`).
*   **Tools Used:** `run_shell_command` (`git add`, `git commit`, `git push`).

### Step 5: Iteration and New Delegation (if necessary)

*   **Primo's Action:** If the code review identifies problems, gaps, or the need for refinements:
    *   Primo will formulate a new task for the executor agent, detailing the corrections or next steps.
    *   The delegation cycle (Step 2) will be restarted for this new task.

### Step 6: Cleanup and Documentation Update

*   **Primo's Action:** After the successful completion of the task and the commit of the changes:
    *   The Markdown execution plan file (`.md`) will be deleted to keep the repository clean.
    *   The `README.md` or other relevant documents will be updated to reflect the implemented changes and the new state of the project.
*   **Tools Used:** `run_shell_command` (`rm`), `replace` or `write_file`.

---

**Guiding Principles:**

*   **Transparency:** Every step is logged and verifiable.
*   **Control:** Primo maintains control over the agent's execution and permissions.
*   **Quality:** Rigorous verification ensures the delivery of high-quality code.
*   **Iteration:** The process is adaptable and allows for continuous refinements.