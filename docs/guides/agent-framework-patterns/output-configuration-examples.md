# Agent Output Configuration Patterns

## Overview

The framework allows each agent to configure its output artifacts through the `output_artifact` and `output_directory` parameters in `agent.yaml`. This makes the framework scalable and reusable.

## Configuration Examples

### 1. ProblemRefiner_Agent
```yaml
output_artifact: "polished_problem.md"
output_directory: "workspace/outbox"
execution_task: |
  Generate a Markdown document (`${output_artifact}`) that clearly describes...
```

### 2. CodeGenerator_Agent (Hypothetical)
```yaml
output_artifact: "generated_service.java"
output_directory: "src/main/java/com/example/service"
execution_task: |
  Based on the specification, generate a Java class (`${output_artifact}`) that implements...
```

### 3. TestCreator_Agent (Hypothetical)
```yaml
output_artifact: "IntegrationTest.java"
output_directory: "src/test/java/com/example"
execution_task: |
  Create automated tests (`${output_artifact}`) that validate...
```

### 4. DocumentationAgent (Hypothetical)
```yaml
output_artifact: "API_Documentation.md"
output_directory: "docs/api"
execution_task: |
  Consolidate the API documentation (`${output_artifact}`) including...
```

### 5. RequirementsAnalyzer_Agent (Hypothetical)
```yaml
output_artifact: "requirements_specification.doc"
output_directory: "project-docs/requirements"
execution_task: |
  Analyze and document the requirements (`${output_artifact}`) covering...
```

## Universal Commands

With this parameterization, all agents support:

### 0. Help (Help System)
```bash
help
ajuda
comandos
?
```
**Result**: 
- Displays full list of available commands
- Agent usage instructions
- Recommended workflow

### 1. Preview (View without Saving)
```bash
preview
preview document
show document
```
**Result**: 
- Displays full content in chat
- DOES NOT save file
- Allows review before saving

### 2. Generation/Merge (Save with Versioning)
```bash
generate document
create artifact
save document
execute task
consolidate
```
**Result**: 
- **New file**: Creates v1.0 based on full history
- **Existing file**: Merges with new conversations → v1.1, v1.2...
- Saves to the configured directory
- Preserves previous context + adds new insights

### 3. Recommended Workflow
```bash
# 1. First iteration
"preview"                    # See how it would look
"generate document"           # Save v1.0

# 2. More conversations...
"preview"                    # See how it would look with merge
"generate document"           # Save v1.1 (merged)

# 3. Subsequent iterations...
"consolidate"                # Save v1.2, v1.3...
```

## Benefits

1. **Scalability**: Easy creation of new agents
2. **Consistency**: Same command pattern for all
3. **Flexibility**: Each agent can have specific output
4. **Versioning**: Automatic incremental merging
5. **Preview**: Test before saving

## Implementation in Persona

```markdown
### 4.4 Dynamic Configuration
**The output file name and directory are configurable:**
- **File**: Defined in `output_artifact` in agent.yaml
- **Directory**: Defined in `output_directory` in agent.yaml
- **For this agent**: `{output_artifact}` in `{output_directory}/`
```

## Substitution Pattern

The `execution_task` uses `${output_artifact}` which is replaced by the configured value:

```yaml
execution_task: |
  Generate a document (`${output_artifact}`) that...
```

This allows reuse of persona templates across different agent types.
