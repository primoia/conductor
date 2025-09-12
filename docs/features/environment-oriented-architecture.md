# Environment-Oriented Architecture

To ensure security and organization, the framework operates with a concept of **environments** and **workspaces**. This prevents an agent intended for a `development` environment from accidentally modifying a `production` environment.

**Key Configuration:**
- **`config.yaml`**: Centralized configuration for storage, agent discovery, and tool plugins.

**Execution:**
- The `src/cli/agent.py` command requires the `--environment` parameter to ensure that the agent is loaded and executed within the correct and secure context.

This architecture provides a clear separation of concerns, allowing developers to work on different projects or different stages of the same project without interference. It enhances safety by restricting agent operations to their designated workspaces, preventing unintended modifications to critical systems.