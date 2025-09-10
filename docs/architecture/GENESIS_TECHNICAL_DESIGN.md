# Execution and Design Plan: Master Agent (Conductor)

> **📌 NOTA DE ARQUITETURA:** Esta documentação descreve o design técnico original do Master Agent. Para uma visão unificada e atualizada de toda a arquitetura do sistema pós-SAGA-017, consulte: [UNIFIED_ARCHITECTURE.md](./UNIFIED_ARCHITECTURE.md)

**Document Version:** 2.1

**Status:** Final Proposal for Implementation (with command mechanism)

**Author:** CTO

**Reference:** This document is the implementation design for the **"Embodied Mode"** described in the [Conductor Architectural Specification](./GEMINI_ARCH_SPEC.md) and incorporates the metaprogramming capabilities for agent creation.

---

### 1. Objective and Philosophy

The `src/cli/agent.py` is the interactive core of the Conductor framework. Its function is to be a stateful command-line application (CLI) that **embodies** a Specialist Agent, serving as the primary interface for the Conductor (developer) in the analysis, planning, and debugging phases.

### 2. Initialization Logic and "Embodiment"

**2.1. Command-Line Argument Analysis:**
*   `--agent <agent_id>`: **(Required)** The ID of the Specialist Agent to be embodied.
*   `--state <path_to_state>`: **(Optional)** Loads a state file from a previous session.
*   `--verbose`: **(Optional)** Activates detailed logging.

**2.2. Agent Loading Process:**
1.  **Location:** Finds the directory `projects/<environment>/<project>/agents/<agent_id>/`.
2.  **DNA Reading:** Parses the `agent.yaml` to get the session configuration.
3.  **Persona Reading:** Loads the content of `persona.md`.
4.  **Memory Reading:** Loads the `state.json`.

**2.3. AI Engine Preparation (LLM):**
1.  **System Prompt Construction:** The system prompt will be composed of:
    *   **Master Instruction:** Defines the role of the Conductor as an agent embosser.
    *   **Agent Persona:** The content of the embodied agent's `persona.md`.
    *   **Tool and Command Instructions:** Describes the available tools and agent commands and the syntax for using them (see Section 4).
2.  **API Client Initialization:** Prepares the connection with the LLM API.

### 3. The Interactive Conversation Loop (REPL)

The heart of the application, a Read-Eval-Print-Loop cycle.

1.  **READ:** Displays a dynamic prompt (e.g., `[ProblemRefiner_Agent] > `) and waits for the Conductor's input.
2.  **EVAL:** Processes the input:
    *   **Internal Commands (Conductor):** Checks if the input starts with `/`.
        *   `/exit`: Ends the session (with confirmation to save state).
        *   `/save`: Forces persistence of the current `state.json`.
        *   `/help`: Shows Conductor's internal commands.
        *   `/agent_help`: Shows the embodied agent's specific commands (see Section 4.1).
        *   `/new_agent`: Shortcut for `src/cli/admin.py --agent AgentCreator_Agent` (see Section 7).
    *   **Agent Commands:** Checks if the input starts with `*`. If so, attempts to execute the agent's specific command (see Section 4.1).
    *   **AI Call (Chat):** If not a command, the input is treated as a chat message.
        a. The message is added to the conversation history in `state.json`.
        b. The complete history is sent to the LLM along with the system prompt.
    *   **AI Response Analysis:** The LLM's response is analyzed for a tool call (`[TOOL_CALL: ...]`).
        a. **If a tool is found:** The Conductor executes the tool, adds the result to the history, and makes a new call to the LLM with the result for interpretation.
        b. **If not found:** The response is treated as plain text.
3.  **PRINT:** Displays the final LLM response to the Conductor.
4.  **LOOP:** Returns to step 1.

### 4. Tools and Commands ("Special Powers")

**4.1. System Tools (Invoked by AI):**
*   **Definition:** Python functions in Conductor (e.g., `_tool_read_file`), registered in a `TOOL_REGISTRY`.
*   **Availability:** The `agent.yaml` defines which tools an agent can request via `available_tools`.
*   **Execution:** The AI requests execution via `[TOOL_CALL: ...]`. Conductor validates and executes.

**4.2. Agent Commands (Invoked by User):**
*   **Definition:** An agent's `persona.md` can contain a `## Commands` section that lists specific actions (starting with `*`). E.g., `*create-prd: Initiates the PRD creation process.`.
*   **Parse and Discovery:** When embodying an agent, Conductor must parse the `## Commands` section of the persona to know which commands the agent offers.
*   **Execution:** When the Conductor types a command like `*create-prd`, Conductor adds an instruction to the conversation history before calling the AI: `[USER_COMMAND: The user invoked the command '*create-prd'. Proceed with the logic defined for this command.]`. This instructs the AI to execute the task associated with the command.
*   **Help:** The `/agent_help` command of Conductor should list the commands (`*`) found in the currently embodied agent's persona.

### 5. State Management and Persistence

The `state.json` is the session memory, loaded at startup and saved via `/save` or upon exit.

### 6. Suggested Code Structure

A clear class structure to guide implementation:

*   `ConductorAgent`: The main class.
*   `Toolbelt`: Module with tool functions.
*   `CommandParser`: Module to extract commands from `persona.md`.
*   `LLMClient`: Wrapper for the LLM API.

---

### 7. Metaprogramming Capabilities: Agent Creation

**7.1. Philosophy:** Agent creation is a specialized task, delegated to a specific agent, the `AgentCreator_Agent` ("Agent Zero").

**7.2. Creation Workflow:**
1.  **Invocation:** The Conductor executes `poetry run python src/cli/admin.py --agent AgentCreator_Agent` (or the `/new_agent` shortcut).
2.  **Design Dialogue:** The `AgentCreator_Agent` (embodied) guides the Conductor in defining the `id`, `description`, `persona`, `tools`, and `execution_task` of the new agent.
3.  **Artifact Generation:** At the end, the `AgentCreator_Agent` uses its tools (`write_file`, `mkdir`) to generate the folder structure and files for the new agent.
