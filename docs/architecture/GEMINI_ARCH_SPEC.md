# Architectural Specification: Conductor Agent Framework

> **📌 NOTA DE ARQUITETURA:** Esta documentação descreve especificações originais do framework. Para uma visão unificada e atualizada de toda a arquitetura do sistema pós-SAGA-017, consulte: [UNIFIED_ARCHITECTURE.md](./UNIFIED_ARCHITECTURE.md)

**Version:** 2.0

**Author:** Gemini (in collaboration with the project architect)

## 1. Overview and Philosophy

This document describes the architecture of a new generation AI agent framework, codenamed "Conductor". The goal is to overcome the limitations of linear and template-based models, creating a dynamic, interactive, and context-aware development ecosystem.

### Core Philosophy

The "Conductor" framework is designed to **augment the capacity of a single developer (the "Conductor")**, serving as an active and intelligent partner in the development lifecycle, rather than trying to simulate a complete development team rigidly.

### Architectural Principles

*   **Interaction as Priority:** Conversational interaction (chat) is a first-class functionality, essential for the analysis, planning, and debugging phases.
*   **Context Awareness:** Agents must have the ability to access and analyze the current state of the source code to inform their decisions and dialogues.
*   **Persistent and Evolving State:** Each agent has a persistent memory (`state.json`) that represents its current understanding of the system. This state evolves as development progresses.
*   **Unified Agent Model:** There is a single way to define an agent through a specification file (`agent.yaml`). This agent can, however, be executed in two distinct ways: interactive or automated.

---

## 2. The Conductor Development Lifecycle

The framework operates in a continuous and virtuous lifecycle, composed of four distinct phases.

> **Core Metaphor:** "State is part of the problem, state evolution is the plan, plan completion is state evolution within the agents."

### Phase 1: Immersion and Problem Definition
*   **Input:** An intention or objective from the Conductor (e.g., "Add Google authentication").
*   **Process:** The Conductor initiates an interactive session with a specialist agent (embodied by the Master Agent). The agent asks questions and, crucially, accesses the source code to analyze the impact, dependencies, and technical context. The problem is collaboratively refined.
*   **Output:** A "Polished Problem," a deep and shared understanding of what needs to be done.

### Phase 2: Collaboration and Plan Creation
*   **Input:** The "Polished Problem."
*   **Process:** The interactive session continues, now focusing on the solution. The agent collaborates with the Conductor to define the technical approach, necessary steps, and specific tasks. The agent can suggest creating multiple specialist agents for the execution phase.
*   **Output:** A "Polished Plan," typically in the form of an `implementation_plan.yaml`, ready for execution.

### Phase 3: Orchestrated Execution
*   **Input:** The "Polished Plan" (`implementation_plan.yaml`).
*   **Process:** The Conductor orchestrator takes control. It reads the plan and executes the tasks non-interactively, calling the necessary Specialist Agents in "Orchestrated Mode" to generate code, run tests, etc.
*   **Output:** New code, passing tests, and a Pull Request ready for review.

### Phase 4: Feedback and State Evolution
*   **Input:** The approved and integrated Pull Request.
*   **Process:** An automated or manual process analyzes the changes and updates the `state.json` of the relevant agents, informing them about the new reality of the source code.
*   **Output:** Agents with an updated state, ready for the next development cycle.

---

## 3. Component Architecture

1.  **The Conductor (Human):** The developer. The final decision-maker, who guides the process, validates AI suggestions, and maintains creative control.
2.  **The Master Agent:** The main user interface for interactive mode. It is a special agent whose sole function is to **embody** other specialist agents to allow dialogue, analysis, and debugging.
3.  **Specialist Agents:** The "doers." Each is a specialist in a task (e.g., `KotlinEntityCreator_Agent`, `TerraformPlanner_Agent`). They are defined by an `agent.yaml`.
4.  **The Orchestrator:** The execution engine for automatic mode. It reads a plan and executes specialist agents efficiently and non-interactively.
5.  **The Definition Artifact (`agent.yaml`):** The "DNA" of an agent. A specification file that makes an agent understandable to both the Master Agent (for embodiment) and the Orchestrator (for execution).

---

## 4. The Agent Definition Artifact (`agent.yaml`)

This file is the heart of the architecture. It defines everything the system needs to know about an agent.

```yaml
# Example: agent.yaml for an entity creator

id: KotlinEntityCreator_Agent
version: 1.0
description: "Creates a Kotlin data entity with JPA annotations from a specification."

# (NEW) Defines which AI engine to use for this agent.
# Valid values: 'claude' or 'gemini'.
ai_provider: 'claude'

# Path to the prompt that defines the personality and behavior
persona_prompt_path: "persona.md"

# Path to the agent's state file (memory)
state_file_path: "state.json"

# Task to be executed in automatic mode (by the Conductor orchestrator)
# The instruction can be a direct prompt or a path to a task file
execution_task: |
  Based on the `input_file` provided in the plan, generate the Kotlin entity.
  The `input_file` contains the field specification.
  Save the result to the `output_file` specified in the plan.

# Available tools in interactive mode (by the Master Agent)
available_tools:
  - read_file
  - list_directory
  - run_shell_command

# Expected schema for state.json (optional, for validation)
state_schema:
  last_entity_created: string
  common_field_patterns: array
```

---

## 5. Execution Modes

An agent, defined by a single `agent.yaml`, can operate in two ways:

### Embodied Mode (Interactive)
*   **Invocation:** `poetry run python src/cli/agent.py --agent <agent_id> --project-root <path_to_project>`
*   **Process:** The Master Agent reads the `agent.yaml` of the target agent. It loads the persona, state, and tools (`available_tools`) into a chat session. The Conductor uses the `--project-root` to contextualize all tool calls (e.g., `read_file`), ensuring the agent operates only within the target project.
*   **Use Cases:** Problem analysis, plan creation, interactive debugging of an agent that failed in automatic mode, guided refactoring.

### Orchestrated Mode (Automatic)
*   **Invocation:** The Conductor orchestrator is run with a plan (e.g., `poetry run python src/cli/orchestrator.py --plan <plan.yaml>` if such a script exists, or through other means of triggering orchestrated execution).
*   **Process:** The Conductor orchestrator reads the plan, identifies the `agent_id` for a task, loads its `agent.yaml`, and uses the `execution_task` directive to execute the task non-interactively, passing the parameters defined in the plan (such as `input_file` and `output_file`).
*   **Use Cases:** Mass code generation, test execution, CI/CD tasks, refactoring automation.

---

## 6. Workflow Example

1.  **Agent Creation (if necessary):** The Conductor uses the `AgentCreator_Agent` to create a new specialist agent within the correct context path, e.g., `projects/develop/my-app/agents/MyNewTaskAgent`.
2.  **Intention:** The Conductor wants to add a `tags` field to the `Product` entity in the `my-app` project.
3.  **Phase 1 (Analysis):**
    *   The Conductor initiates: `poetry run python src/cli/agent.py --agent KotlinEntityCreator_Agent --project-root /path/to/my-app --repl`
    *   In the chat session, they say: "I need to add a `tags` field to the `Product` entity. Can you analyze the `src/Product.kt` file and tell me the impact?"
    *   The agent (embodied) uses its `read_file` tool (contextualized by Conductor for `/path/to/my-app/src/Product.kt`) and responds with the details.
4.  **Phase 2 (Planning):**
    *   They collaborate and define the approach. The result is an `implementation_plan.yaml`.
5.  **Phase 3 (Execution):**
    *   The Conductor executes the plan (e.g., by running the orchestrator with `a_plan.yaml`).
    *   The orchestrator executes the tasks, generating the code within the `my-app` project.
6.  **Phase 4 (Feedback):**
    *   After the PR is approved, the `state.json` of the `KotlinEntityCreator_Agent` is updated.
