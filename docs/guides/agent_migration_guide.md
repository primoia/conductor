# Guide: Migrating Legacy Agents

With the introduction of the new unified architecture in SAGA-017, the way agents are defined and stored has changed. This guide explains how to migrate agents from the old format (based on multiple files in a directory) to the new format (a single JSON artifact).

## 1. The Architectural Change

-   **Old Format:** An agent was defined by a collection of files within a directory (e.g., `agent.yaml`, `persona.md`, `playbook.yaml`).
-   **New Format:** An agent's complete definition now resides in a single `.json` artifact, which is stored in a persistence backend (like the `.conductor_workspace/agents/` directory for the `filesystem` backend).

## 2. The Migration Tool

To ease the transition, Conductor provides a script to automate the process.

-   **Script:** `scripts/migrate_legacy_agents.py`

This script reads a directory containing agents in the old format and generates the corresponding new `.json` artifacts.

## 3. How to Use

### Step 1: Run the Script
Open your terminal at the project root and run the script, providing the source directory (where your old agents are) and a target directory.

**Example:**
```bash
poetry run python scripts/migrate_legacy_agents.py \
    --source-dir path/to/your/legacy_agents \
    --target-dir .conductor_workspace/agents
```
-   `--source-dir`: The directory containing the folders for each agent to be migrated.
-   `--target-dir`: The directory where the new `.json` files will be saved. For the `filesystem` backend, this should be the agents directory within your workspace.

### Step 2: Check the Results
The script will process each subdirectory in the source directory and create a corresponding `.json` file in the target directory.

**"Before" Structure:**
```
legacy_agents/
└── MyAwesome_Agent/
    ├── agent.yaml
    └── persona.md
```

**"After" Structure:**
```
.conductor_workspace/
└── agents/
    └── MyAwesome_Agent.json
```

The `ConductorService` will automatically discover and load agents from this new location.
