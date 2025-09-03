# Scoped Tool System

Agents can be granted "tools" that give them the ability to interact with the file system and execute commands.

**Security First:**
To prevent destructive or unwanted operations, the writing tool (`write_file`) is restricted by a **write scope**.

**Configuration:**
- In the `agent.yaml` file, the `output_scope` key defines a `glob` pattern that restricts where the agent can write files. For example: `src/main/kotlin/**/*.kt`.

Any attempt to write outside this pattern will be blocked, ensuring the integrity of the codebase. This granular control over file system access is a critical security feature, allowing developers to safely integrate AI agents into their development workflows without risking unintended modifications to sensitive areas of the project.