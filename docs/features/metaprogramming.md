# Metaprogramming with AgentCreator

Metaprogramming is the ability of a program to write or manipulate other programs. In Conductor, this is manifested through the `AgentCreator_Agent`.

**What it is:**
- The `AgentCreator_Agent` is a **meta-agent** (an agent that manages other agents).
- It guides the user through a dialogue to create the directory structure and configuration files (`agent.yaml`, `persona.md`) for a new agent.

**How to use:**
- Execute `src/cli/admin.py` to invoke the `AgentCreator_Agent`:
  ```bash
  poetry run python src/cli/admin.py --agent AgentCreator_Agent --repl
  ```

This feature allows for the dynamic creation and customization of agents, enabling the Conductor framework to adapt and extend its capabilities without manual coding. It's a powerful way to bootstrap new agent functionalities and maintain a consistent agent ecosystem.