# Executor Architecture - Separation of Responsibilities

## Overview

The executor architecture has been refactored following the **Single Responsibility Principle** to clearly separate responsibilities between project agents and meta-agents.

## Executors

### 1. `src/cli/agent.py` - Project Executor

**Responsibility:** Execute agents that operate on specific target projects.

**Characteristics:**
- Requires environment and project context (`--environment`, `--project`)
- Agents reside in `projects/<environment>/<project>/agents/`
- Changes to the target project directory (Project Resident Mode)
- Applies `output_scope` restrictions when configured

**Usage:**
```bash
poetry run python src/cli/agent.py --environment develop --project your-project-name --agent KotlinEntityCreator_Agent --repl
```

**Examples of Agents:**
- `KotlinEntityCreator_Agent`
- `ProblemRefiner_Agent`
- `TestGenerator_Agent`

### 2. `src/cli/admin.py` - Administration Executor

**Responsibility:** Execute meta-agents that manage the framework itself.

**Characteristics:**
- Does not require project/environment context
- Agents reside in `projects/_common/agents/`
- Works in the framework's root directory
- No output restrictions (meta-agents)

**Usage:**
```bash
# Interactive mode
poetry run python src/cli/admin.py --agent AgentCreator_Agent --repl

# Non-interactive mode with destination path (v2.1)
poetry run python src/cli/admin.py --agent AgentCreator_Agent --destination-path "/absolute/path" --input "Agent description"
```

**Examples of Meta-Agents:**
- `AgentCreator_Agent` - Automated creation of new agents
- `migrate_agents_v2` - Agent migration to new architecture
- `update_agents_help_system` - Help system update

**Practical Example - QA Agent Creation:**
```bash
poetry run python src/cli/admin.py \
  --agent AgentCreator_Agent \
  --destination-path "/projects/conductor/projects/_common/agents/QAAgent_01" \
  --input "Create an agent to automate QA tests focusing on REST APIs" \
  --ai-provider claude
```

**Result:** Automatically creates:
- `agent.yaml` - Configuration with appropriate tools
- `persona.md` - QA specialized persona
- `state.json` - Clean initial state v2.0

## Shared Module

### Core Components

Contains common functions used by both executors, such as:

- Loading AI providers configuration
- Loading agent configuration
- Resolving agent paths
- Creating LLM clients with refactored LLM classes
- Starting REPL sessions
- Validating configuration

**LLM Classes (v2.1):**
- `LLMClient` - Base interface for AI providers
- `ClaudeCLIClient` - Claude CLI client implementation
- `GeminiCLIClient` - Gemini CLI client implementation

> **Note:** LLM classes were moved to avoid duplication and centralize AI provider communication logic.

## Benefits of Separation

### 1. High Cohesion
- Each executor has a clear and single responsibility
- More focused and easier to understand code

### 2. Cleaner Code
- Eliminates unnecessary conditional logic
- Reduces complexity of each executor

### 3. Clarity for the User
- Explicit separation between "using" and "administering" the framework
- More intuitive and specific commands

### 4. Maintainability
- Changes in one executor do not affect the other
- More focused and isolated tests

## Decision Flow

### When to use `src/cli/agent.py`:
- Agent works on a specific project
- Needs environment/project context
- Agent is in `projects/<env>/<project>/agents/`

### When to use `src/cli/admin.py`:
- Agent manages the framework
- Does not need project context
- Agent is in `projects/_common/agents/`

## Migration

### For Existing Users:
- **Project Agents:** Continue using `src/cli/agent.py` normally
- **Meta-Agents:** Migrate to `src/cli/admin.py`

### Migration Example:
```bash
# Before (worked, but not ideal)
poetry run python src/cli/agent.py --environment _common --project _common --agent AgentCreator_Agent

# After (recommended)
poetry run python src/cli/admin.py --agent AgentCreator_Agent --repl

# New (v2.1): Automated agent creation
poetry run python src/cli/admin.py --agent AgentCreator_Agent \
  --destination-path "/path/to/new/agent" \
  --input "Create agent for QA documentation" \
  --ai-provider claude
```

## Directory Structure

```
conductor/
├── src/cli/
│   ├── agent.py             # Project executor
│   └── admin.py             # Administration executor
└── projects/
    ├── _common/
    │   └── agents/          # Meta-agents
    │       └── AgentCreator_Agent/
    └── develop/
        └── your-project-name/
            └── agents/      # Project agents
                └── KotlinEntityCreator_Agent/
```

## v2.1 Improvements (Recent)

### Automated Agent Creation

The `src/cli/admin.py` has been enhanced with automated agent creation functionalities:

**`--destination-path` Parameter:**
- Allows specifying an absolute path where the agent should be created
- Eliminates ambiguity in creating meta-agents vs. project agents
- Supports automation and scripts

**Refactored AgentCreator_Agent:**
- New persona based on direct absolute paths
- Eliminates questions about environment/project
- Clean and standardized `state.json` v2.0 template
- Direct file creation at the specified path

**state.json v2.0 Template:**
```json
{
  "agent_id": "{{agent_id}}",
  "version": "2.0", 
  "created_at": "{{timestamp}}",
  "last_updated": "{{timestamp}}",
  "execution_stats": {
    "total_executions": 0,
    "last_execution": null
  },
  "conversation_history": []
}
```

### Code Cleanup

- **LLM Class Refactoring:** Removed duplications
- **Centralization:** All LLM classes now reside in core components
- **Consistency:** Better organization and maintainability of the code

### Benefits of v2.1 Improvements

1. **Full Automation:** Agent creation via command line without interaction
2. **Clean State:** Agents always start with an empty `state.json`
3. **No Ambiguity:** Explicit path eliminates confusion about location
4. **Maintainability:** Cleaner and more organized code
5. **Testability:** Deterministic and verifiable process

### Validation of Improvements

The automated creation process was validated with the following criteria:

✅ **Exit Code 0:** Command terminates successfully
✅ **Directory Created:** Specified path is created correctly
✅ **Essential Files:** `agent.yaml`, `persona.md`, `state.json` are generated
✅ **Clean State:** `conversation_history: []` in `state.json`

**Test Command:**
```bash
poetry run python src/cli/admin.py \
  --agent AgentCreator_Agent \
  --destination-path "/mnt/ramdisk/test-agent" \
  --input "Simple test agent" \
  --ai-provider claude
```

## Compatibility

- ✅ Fully compatible with existing agents
- ✅ Does not break current functionality
- ✅ Improves organization and clarity
- ✅ Facilitates future maintenance
- ✅ **New:** Support for automated agent creation
```