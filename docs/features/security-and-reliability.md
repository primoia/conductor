# Security and Reliability

Security is a fundamental pillar of the framework's design.

**Key Measures:**
- **Write Scope (`output_scope`):** Prevents agents from modifying files outside their designated working directory.
- **Human Confirmation:** In interactive mode (`--repl`), any file write operation requires explicit user confirmation.
- **Separated Executors:** The separation between `src/cli/admin.py` (framework tasks) and `src/cli/agent.py` (project tasks) prevents a project agent from modifying the framework's own configuration.
- **Environment Architecture:** Logically isolates `development` and `production` environments through `workspaces.yaml`.

These measures collectively ensure a robust and secure environment for AI-assisted development, minimizing risks and maximizing reliability. The framework is built with a strong emphasis on preventing unintended actions and maintaining the integrity of your codebase.