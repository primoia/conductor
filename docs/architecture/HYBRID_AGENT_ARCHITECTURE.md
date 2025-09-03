# Agent Architecture: The Hybrid "Stabilized Local Cache" Model

**Status:** Proposed and Accepted
**Date:** August 24, 2025

This document describes the agent execution architecture for the Conductor Framework. It was designed to be robust, scalable, and to support complex workflows for both development teams and non-interactive automation.

## 1. Overview and Principles

This architecture resolves the conflict between an agent's need for **access to a project's context** and, at the same time, maintaining its **identity and state**. It is based on three principles:

1.  **Centralization of Intelligence:** Agents are designed and maintained in a central location (the "Factory"), allowing intelligence to be enhanced and reused.
2.  **Local Stabilization:** The version of an agent used by a team on a daily basis is versioned along with the project's code, ensuring compatibility and stability.
3.  **Contextualized Execution:** Agent execution always occurs with the process running from within the target project directory, ensuring full and secure access to files.

## 2. Architectural Components

### a. The "Agent Factory" (The Conductor Repository)

-   **Purpose:** It is the center for designing, creating, and maintaining all agents.
-   **Key Components:**
    -   `projects/_common/agents/`: Contains meta-agents.
    -   `projects/<env>/<proj>/agents/`: Contains the "master" versions of project agents.
    -   `src/cli/admin.py`: The CLI tool for the "Agent Engineer," used to create, test, and deploy agents.
    -   The orchestrator for autonomous plan-based execution.

### b. The Target Project (e.g., `nex-web-backend`)

-   **Purpose:** It is the production environment for the agents. It is self-contained and autonomous.
-   **Key Components:**
    -   `agents/`: A folder versioned by the project's Git, which contains the **stabilized** copy of the agents that have been tested and approved for the current code version. This is the "Local Cache."
    -   `.conductor/client.py`: A lightweight executor, also versioned, that the team uses to interact with agents in the "Local Cache."
    -   `state.json` (inside each agent folder): Stores conversation history. It is recommended to add `**/state.json` to the project's `.gitignore`.

## 3. Actors and Workflows

### a. The "Agent Engineer/Curator" (e.g., Tech Lead)

This is the workflow for updating an agent for a project.

1.  **Design in the Factory:** The Engineer works in the Conductor repository to create or improve an agent.
2.  **Remote Testing:** Using `src/cli/admin.py`, they test the new agent version (from the Factory) against the target project's code, without modifying the project yet.
    -   `poetry run python src/cli/admin.py test-agent --agent MyAgent-v1.3 --on-project /path/to/nex-web-backend`
3.  **Publishing (Deploy):** Once satisfied, they "publish" the agent. The command copies the agent files from the Factory to the target project's `agents/` folder.
    -   `poetry run python src/cli/admin.py deploy-agent --agent MyAgent-v1.3 --to-project /path/to/nex-web-backend`
4.  **Stabilization and Commit:** The Engineer, now working in the target project repository, runs the project's regression tests to ensure the new agent hasn't broken anything. If all is OK, they **commit the new agent version** in the target project repository. The new version is now "stabilized."

### b. The "Agent Consumer" (Team Developer)

-   **Workflow:** Simple and straightforward.
    1.  `git pull` in the target project.
    2.  Executes `python .conductor/client.py --agent MyAgent --repl` to interact with the agent version that is guaranteed to work with the code they just downloaded.
    3.  They don't need to know about the "Factory" or Conductor.

### c. The Autonomous Orchestrator

-   **Workflow:** The orchestrator executes a plan (`.yaml`) that specifies which agent to execute in which project. It has two operating modes, defined in the plan:
    -   **`version: stable` (Default):** The orchestrator executes the agent that is in the target project's "Local Cache." This is the safe, predictable mode, ideal for production automation, as it uses the version that has been explicitly tested and committed with the code.
    -   **`version: latest` (Experimental):** The orchestrator ignores the local cache and uses the "Launcher Pattern" to inject the latest agent version directly from the "Factory." Useful for continuous integration testing of the Agent Factory itself.

## 4. Conclusion

This hybrid model offers a robust balance between centralization and distribution. It ensures that:
-   The **intelligence** of agents can be developed and maintained centrally.
-   **Stability** is guaranteed by versioning agents along with the code they manipulate.
-   The **team's workflow** is simple and decoupled from the complexity of AI management.
-   **Automation** can operate safely and predictably, with the option to use cutting-edge features when needed.