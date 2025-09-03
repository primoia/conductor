# Interactive Sessions with Agents

The Conductor Framework allows direct and interactive communication with AI agents through a command-line interface (REPL - Read-Eval-Print Loop). This facilitates collaborative development, debugging, and refinement of complex tasks.

**How it works:**
- **Executors:** `src/cli/agent.py` (for project-specific agents) or `src/cli/admin.py` (for framework administration agents).
- **Command:** Use the `--repl` flag when invoking the agent.

During a session, you can have a continuous dialogue with the agent, ask it to analyze problems, suggest solutions, generate code, and use its available tools. This interactive mode provides a powerful way to guide the AI and iterate on solutions in real-time.