# SAGA-016: Agent Artifact Evolution & Autonomous Orchestration

**Status:** Planning

## 1. Objective

This SAGA formalizes the next-generation architecture for Conductor's agents. The goal is to evolve from a static execution framework to a dynamic, autonomous system capable of intelligent decision-making.

This evolution is based on a clearer separation of concerns for agent artifacts, robust state management, and the introduction of intelligent agent routing.

## 2. The New Agent Artifact Convention

To achieve the required clarity and capability, the current `state.json` will be deprecated in favor of a set of specialized artifacts. Each artifact has a single, clear purpose, analogous to the documents used by a human specialist.

| Artifact          | Analogy                            | Purpose                                                                 | Lifecycle & Who Uses It                                                                 |
|-------------------|------------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **`agent.yaml`**      | The Résumé / CV                    | Defines the agent's identity, static capabilities, and permissions.     | **Orchestrator:** Reads for agent selection and permission validation.                  |
| **`persona.md`**      | The Onboarding Manual              | Defines the agent's behavior, style, and operational guidelines.         | **Specialist Agent (LLM):** Injected into the system prompt to guide reasoning.         |
| **`memory.json`**     | The Long-Term Memory / Diary       | Persists the agent's cumulative experience and conversation history.     | **Orchestrator:** Manages this for long-term context. Ideal for a MongoDB document.     |
| **`session.json`**    | The Short-Term Memory / Whiteboard | Holds the ephemeral context for a single task or `--repl` session.      | **Orchestrator & Specialist:** Used for collaboration on the current task. Discarded after completion. Ideal for a MongoDB document with TTL. |
| **`playbook.md`**     | The Best Practices Playbook        | Stores curated heuristics and solutions for common problems.            | **Specialist Agent (LLM):** Injected into the prompt to provide proven strategies.      |

## 3. Vision for Autonomous Orchestration

The core of this evolution is to empower the Orchestrator Agent with decision-making capabilities.

### 3.1. Intelligent Agent Routing

The Orchestrator will be responsible for selecting the best Specialist Agent for a given task described in a `plan.yaml`. This process involves:

1.  **Task Analysis:** The Orchestrator parses a task description from the plan (e.g., `task: "Refactor the auth module"`).
2.  **Candidate Evaluation:** It compares the task requirements against the `capabilities` and `tags` defined in the `agent.yaml` of all available agents.
3.  **LLM-Powered Selection:** The Orchestrator will use an LLM call to make the final selection, asking which agent is best suited for the task based on their metadata.

This removes the need for the user or the plan to explicitly specify which agent to use, making the system more dynamic.

### 3.2. Dynamic Agent Creation

If the selection mechanism fails to find a suitable agent with a high confidence score, the Orchestrator will trigger a fallback:

1.  It will invoke the `AgentCreator_Agent`.
2.  It will pass the original task description as the input for the new agent's persona and capabilities.

This creates a self-expanding system that can learn to handle new types of tasks by creating new specialists on demand.

## 4. State Management & Persistence Strategy

To support this architecture, we will formally distinguish between two types of state:

-   **Long-Term State (`memory.json`):** Captures an agent's entire history. This is best suited for a scalable database like **MongoDB**, allowing for rich queries on past executions.
-   **Short-Term State (`session.json`):** Contains the live context of a single plan execution. This can also be managed in MongoDB, potentially in a separate collection with a Time-To-Live (TTL) index to automatically clean up abandoned sessions.

This separation ensures that the long-term memory remains clean while providing a dedicated, ephemeral workspace for each task.
