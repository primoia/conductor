# Milestone 4: Refactoring Plan for Multi-Project/Multi-IA Support

**For: Senior Staff (Claude)**

**From: CTO**

**Status: Approved for Implementation**

## 1. Overview

This refactoring will evolve `genesis_agent.py` into a robust tool aware of the environment and project it is operating on. It also introduces the critical capability for each agent to define its required AI provider, enabling future cost and performance optimizations.

## 2. Agent Definition (`agent.yaml`) Modifications

The `agent.yaml` file for all existing and future agents must be updated to include a new mandatory key:

```yaml
# agent.yaml

id: AgentName
...
# NEW MANDATORY KEY
# Defines which AI engine to use for this agent.
# Valid values: 'claude' or 'gemini'.
ai_provider: 'claude'
...
```

## 3. `genesis_agent.py` Engine Refactoring

The core engine must be updated to handle the new context.

### 3.1. New Command-Line Arguments

The script must accept the following new mandatory argument:
*   `--project-root <path>`: The absolute path to the target project on which the agent will operate (e.g., `/mnt/ramdisk/main/your-project-name`).

### 3.2. Dynamic AI Provider Selection

1.  Upon loading an agent, read the `ai_provider` key from its `agent.yaml`.
2.  Refactor the `LLMClient` into a base class with specific implementations (e.g., `ClaudeCLIClient`, `GeminiCLIClient`).
3.  Instantiate the correct client based on the `ai_provider` value. Fail with a clear error if the value is invalid.

### 3.3. Contextual Path Management for Tools

1.  The path provided in `--project-root` must be stored as the session's "working directory".
2.  When an agent's AI calls a tool like `read_file` or `write_file` with a relative path (e.g., `src/service.py`), the Genesis engine **must** prepend the `--project-root` path to form the correct absolute path before executing the filesystem operation. This resolves the pathing bug.

## 4. `AgentCreator_Agent` Refactoring

The agent's persona and logic must be updated for the new contextual creation flow.

### 4.1. New Creation Dialogue (in `persona.md`)

The guided dialogue must now include these new questions at the beginning:

1.  "In which **environment** will this new agent operate? (e.g., `develop`, `main`)"
2.  "For which **project** within this environment will the agent be created? (e.g., `your-project-name`)"
3.  "Which **AI provider** (`claude` or `gemini`) should this agent use by default?"

### 4.2. New Path Creation Logic

The agent must use the answers to construct the full, correct path for the new agent's directory. Example: `projects/<environment>/<project>/agents/<agent_id>`.

## 5. Suggested Implementation Sequence

1.  **Cleanup:** First, confirm with the CEO the names of any agent directories that were created at the project root, and remove them.
2.  **Update `agent.yaml` Files:** Add the new `ai_provider` key to the `agent.yaml` files for the three existing agents: `ProblemRefiner_Agent`, `PlanCreator_Agent`, and `AgentCreator_Agent`.
3.  **Refactor `genesis_agent.py`:** Implement the changes from Section 3 (the new `--project-root` argument, AI client selection, and contextual path management).
4.  **Refactor `AgentCreator_Agent`:** Update its `persona.md` to include the new dialogue questions.
5.  **Validation Test:** Execute the agent creation scenario again. The new dialogue should appear, and the agent should be created in the correct hierarchical path.
