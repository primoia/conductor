# Architecture Security Analysis (SAGA-017)

> **📌 ARCHITECTURE NOTE:** This documentation analyzes specific security aspects. For a unified and updated view of the entire system architecture post-SAGA-017, please refer to: [UNIFIED_ARCHITECTURE.md](./UNIFIED_ARCHITECTURE.md)

## Threat Vector: Tool Plugin Loading

The `tool_plugins` functionality introduced in SAGA-016 allows loading Python code from directories specified in `config.yaml`. This represents the main threat vector of the new architecture.

### Identified Risks

1.  **Path Traversal:** A malicious user could configure a path like `../../../../etc/` to try to load or inspect system files.
2.  **Malicious Code Execution:** A user can, intentionally or not, point to a plugin directory that contains malicious code, which would be executed at the initialization of the `ConductorService`.

### Implemented Mitigations (Stage 24)

1.  **Path Validation:** The `ConductorService` now checks if the absolute path of the plugin directory is a subdirectory of the project directory. This effectively mitigates Path Traversal attacks, ensuring that only code within the project's scope can be loaded dynamically.
2.  **Explicit Logging:** A `WARNING` is explicitly logged whenever a plugin is loaded. This increases visibility and helps in auditing.

### Residual Risks and Recommendations

-   The risk of malicious code execution persists. The final responsibility lies with the operator who configures the `config.yaml`.
-   **Recommendation:** The documentation should clearly instruct users to **never** load plugins from untrusted sources.
-   **Future:** In a more restricted production environment, consider implementing an "allow-list" of permitted plugins or code signing for plugins.