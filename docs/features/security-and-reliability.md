# Security and Reliability

Security is a fundamental pillar of the framework's design.

**Key Measures:**
- **Write Scope (`output_scope`):** Prevents agents from modifying files outside their designated working directory.
- **Human Confirmation:** In interactive mode (`--chat --interactive`), any file write operation can be guarded by human confirmation.
- **Unified Entry Point:** Prefer the unified `conductor` CLI. Legacy CLIs (`src/cli/admin.py`, `src/cli/agent.py`) remain for compatibility but operate on the same secure services.
- **Environment Architecture:** Provides secure agent execution through controlled tool access and scoped permissions.

These measures collectively ensure a robust and secure environment for AI-assisted development, minimizing risks and maximizing reliability. The framework is built with a strong emphasis on preventing unintended actions and maintaining the integrity of your codebase.