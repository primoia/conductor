# 🤖 Agent Framework v2.1 - Documentation

> **Standardized system for creating and managing agents with interactive commands and incremental versioning**

## 📋 Overview

This framework provides a complete and standardized system for Conductor agents, including:

- ✅ **Output Parameterization**: Flexible configuration of generated files
- ✅ **Interactive Help System**: Self-documenting commands in each agent
- ✅ **Preview without commit**: Visualization before saving
- ✅ **Incremental versioning**: Automatic merging v1.0 → v1.1 → v1.2...
- ✅ **Standardized interface**: Same commands across all agents

## 📁 Documentation Structure

| File | Description |
|---------|-----------|
| `output-configuration-examples.md` | Examples of parameterized configuration by agent type |
| `persona-commands-template.md` | Reusable template for adding commands to personas |
| `README.md` | This file - main documentation guide |

## 🚀 Implementation Guide

### 1. Agent.yaml Configuration

```yaml
# Mandatory configuration for all agents
execution_task: |
  Generate a document (${output_artifact}) with...

# Output parameterization
output_artifact: "filename.ext"
output_directory: "path/to/output"

# Modern standardized tools
available_tools:
  - read_file
  - write_file
  - search_file_content
  - glob
```

### 2. Help System in Personas

Each persona should include the commands section:

```markdown
## Available Commands

### Help Command
**Commands accepted:** help, ajuda, comandos, ?

### Preview Command
**Commands accepted:** preview, preview document, show document

### Generation/Merge Command
**Commands accepted:** generate document, create artifact, save document, execute task, consolidate
```

## 🔧 Supported Agent Types

### Code Agents
- **KotlinEntityCreator_Agent**: Generates `Entity.kt`
- **KotlinRepositoryCreator_Agent**: Generates `Repository.kt`
- **KotlinServiceCreator_Agent**: Generates `Service.kt`
- **KotlinTestCreator_Agent**: Generates `IntegrationTest.kt`

### Documentation Agents
- **ProblemRefiner_Agent**: Generates `polished_problem.md`
- **PlanCreator_Agent**: Generates `implementation_plan.yaml`
- **PythonDocumenter_Agent**: Generates `python_documentation.md`

### System Agents
- **AgentCreator_Agent**: Generates `agent_creation_report.md`
- **OnboardingGuide_Agent**: Generates `onboarding_report.md`

## 🎯 Universal Commands

All agents support:

### 📋 Preview (View without Saving)
```
preview
preview document
show document
```
**Result**: Displays content in chat, does not save file

### 💾 Generation/Merge (Save with Versioning)
```
generate document
create artifact
save document
execute task
consolidate
```
**Result**: 
- **First time**: Creates v1.0
- **Already exists**: Merges → v1.1, v1.2...

### ❓ Help
```
help
ajuda
comandos
?
```
**Result**: Shows available commands and agent configuration

## 🔄 Recommended Workflow

```bash
# 1. Chat with agent
poetry run python src/cli/agent.py --agent AgentName --repl

# 2. In the agent chat:
help                    # See available commands
# ... discuss problem/requirements ...
preview                 # See how the document would look
generate document         # Save v1.0

# 3. More conversations and refinements:
# ... more discussions ...
preview                 # See merge with new information
consolidate              # Save v1.1

# 4. Subsequent iterations:
# ... continuous refinements ...
generate document         # Save v1.2, v1.3...
```

## 📊 System Benefits

### For Developers
- **Consistency**: Uniform interface across all agents
- **Productivity**: Preview avoids unnecessary commits
- **Iteration**: Versioning facilitates incremental refinements

### For the Framework
- **Scalability**: Easy creation of new agents
- **Maintainability**: Patterns reduce complexity
- **Quality**: Automatic validation and consistent structure

### For Users
- **Self-documentation**: Embedded help explains each agent
- **Transparency**: Preview shows result before saving
- **Control**: Versioning preserves change history

## 🔧 Migrating Legacy Agents

To update existing agents:

1. **Agent.yaml**: Add `output_artifact` and `output_directory`
2. **Persona.md**: Include "Available Commands" section
3. **Tools**: Update to `read_file`/`write_file`/`search_file_content`/`glob`
4. **Test**: Validate help, preview, and generation

Consult `persona-commands-template.md` for complete template.

## 📈 Next Steps

- [ ] Implement domain-specific agent templates
- [ ] Add command usage metrics
- [ ] Create automatic configuration validation
- [ ] Expand versioning types (semantic)

---

**🎼 Agent Framework v2.1** - Standardization, scalability, and excellence in every interaction.
