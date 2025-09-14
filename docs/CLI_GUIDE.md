# 🎮 Conductor CLI Guide

## 🚀 Overview

Conductor provides a unified command-line interface that makes it easy to interact with AI agents for development tasks. The CLI supports both quick one-off commands and interactive sessions for complex workflows.

## 📋 Basic Commands

### List Available Agents
```bash
conductor --list
```
Shows all available agents with their capabilities, tags, and descriptions.

### Stateless Execution (Fast, No History)
```bash
conductor --agent <agent_id> --input "<message>"
```
Executes a single task without loading or saving conversation history. Perfect for automation and quick tasks.

### Contextual Chat (With History)
```bash
conductor --agent <agent_id> --chat --input "<message>"
```
Executes a task while preserving conversation context. Ideal for iterative work and related questions.

### Interactive Session (REPL)
```bash
conductor --agent <agent_id> --chat --interactive
```
Starts an interactive session where you can have ongoing conversations with the agent.

### Get Agent Information
```bash
conductor --info <agent_id>
```
Shows detailed information about a specific agent including capabilities, tools, and file structure.

### Validate System Configuration
```bash
conductor --validate
```
Checks system configuration, agent validity, and storage setup.

## 🎮 Execution Modes

### Stateless Mode (Default)
```bash
conductor --agent <agent_id> --input "<message>"
```
- ⚡ **Fast execution** - no history loading/saving
- 🎯 **Perfect for**: automation, CI/CD, quick tasks
- 💰 **Cost effective** - fewer tokens used
- 🔄 **Isolated** - each execution is independent

### Contextual Mode
```bash
conductor --agent <agent_id> --chat --input "<message>"
```
- 📚 **Preserves context** - loads and saves conversation history
- 🎯 **Perfect for**: iterative work, related questions
- 🧠 **Intelligent** - agent remembers previous interactions
- 🔗 **Connected** - builds on previous conversations

### Interactive Mode (REPL)
```bash
conductor --agent <agent_id> --chat --interactive
```
Starts an interactive session with standard REPL commands:
- `state` - Show agent state
- `history` - Show conversation history
- `clear` - Clear conversation history
- `tools` - Show available tools
- `debug` - Show technical information (if available)
- `prompt` - Show full prompt sent to AI (if available)
- `simulate` - Toggle simulation mode (if available)
- `exit` - Exit REPL

### Combined Mode
```bash
conductor --agent <agent_id> --chat --input "<initial_message>" --interactive
```
Sends an initial message with context, then enters interactive mode.

## 💬 Context-Aware Chat

### Basic Chat
```bash
conductor --agent <agent_id> --chat --input "Your message"
```
Sends a message while preserving conversation context.

### Chat with History Management
```bash
# Show conversation history after response
conductor --agent <agent_id> --chat --input "Continue" --show-history

# Clear history before new conversation
conductor --agent <agent_id> --chat --clear --input "New topic"
```

## 🔧 Agent Management

### Install Agent Templates
```bash
# List available templates
conductor --install list

# Install specific category
conductor --install web_development

# Install specific agent
conductor --install ReactExpert_Agent
```

### Backup and Restore
```bash
# Backup all agents
conductor --backup

# Restore from backup
conductor --restore
```

## 🎯 Advanced Usage

### Project Context
```bash
# Execute with project context
conductor --agent TestAgent --environment develop --project myapp --input "Run tests"

# REPL with project context
conductor --agent TestAgent --environment develop --project myapp --chat --interactive
```

### Meta-Agent Operations
```bash
# Create new agents (development REPL)
conductor --agent AgentCreator_Agent --meta --chat --interactive

# Chat for agent creation
conductor --agent AgentCreator_Agent --meta --chat --input "Create a new agent for X"

# Specify new agent id explicitly
conductor --agent AgentCreator_Agent --meta --chat --input "Create" --new-agent-id MyNewAgent
```

### Timeout Configuration
```bash
# Custom timeout for long operations
conductor --agent MyAgent --input "Complex task" --timeout 300
```

## 🛠️ Practical Examples

### Creating a New Agent
```bash
# Interactive agent creation
conductor --agent AgentCreator_Agent --chat --interactive
[AgentCreator_Agent]> Create a CodeReviewer_Agent for Python code analysis
[AgentCreator_Agent]> Add capabilities for PEP8 checking and security analysis
[AgentCreator_Agent]> exit

# Verify creation
conductor --list | grep CodeReviewer
conductor --info CodeReviewer_Agent
```

### Code Review Workflow
```bash
# Quick code review
conductor --agent CodeReviewer_Agent --input "Review this function: def process_data(data): return data.strip().lower()"

# Interactive review session
conductor --agent CodeReviewer_Agent --chat --interactive
[CodeReviewer_Agent]> Review the authentication module
[CodeReviewer_Agent]> debug  # Check agent state
[CodeReviewer_Agent]> What security issues did you find?
[CodeReviewer_Agent]> exit
```

### Documentation Analysis
```bash
# Analyze project documentation
conductor --agent DocumentAnalyst_Agent --input "Analyze all README files and suggest improvements"

# Interactive documentation session
conductor --agent DocumentAnalyst_Agent --chat --input "What's missing from our docs?"
conductor --agent DocumentAnalyst_Agent --chat --input "How can we improve onboarding?" --show-history
```

## 🚨 Troubleshooting

### Common Issues

#### Agent Not Found
```bash
# List available agents
conductor --list

# System suggests similar agents automatically
conductor --agent TestAgent --input "test"
# Output: ❌ Agent 'TestAgent' not found
#         💡 Similar agents: TestingSpecialist_Agent, SystemGuide_Meta_Agent
```

#### Configuration Problems
```bash
# Validate configuration
conductor --validate

# Check specific agent
conductor --info ProblematicAgent
```

#### Performance Issues
```bash
# Increase timeout for complex tasks
conductor --agent MyAgent --input "complex analysis" --timeout 600

# Use simulation mode for testing
conductor --agent MyAgent --chat --interactive --simulate
```

### Getting Help
```bash
# General help
conductor --help

# System operations help
conductor --list
conductor --validate
```

## 📊 Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `--list` | List all agents | `conductor --list` |
| `--agent --input` | Stateless execution | `conductor --agent X --input "task"` |
| `--agent --chat --input` | Contextual execution | `conductor --agent X --chat --input "task"` |
| `--agent --chat --interactive` | Interactive session | `conductor --agent X --chat --interactive` |
| `--info` | Agent information | `conductor --info X` |
| `--validate` | System validation | `conductor --validate` |
| `--install` | Template management | `conductor --install web_development` |
| `--backup` | Agent backup | `conductor --backup` |
| `--restore` | Agent restore | `conductor --restore` |

## 🎯 Best Practices

### For End Users
1. Start with `conductor --list` to discover available agents
2. Use `conductor --agent X --input Y` for quick tasks
3. Use `conductor --agent X --chat --interactive` for complex workflows
4. Always validate configuration with `conductor --validate`

### For Developers
1. Use `conductor --agent X --chat --interactive --meta` for agent development
2. Create agents interactively with AgentCreator_Agent
3. Test agents with `--simulate` flag before production use
4. Use `conductor --info X` to understand agent capabilities

### For Teams
1. Use `conductor --backup` regularly to preserve agents
2. Install template categories with `conductor --install <category>`
3. Document custom agents in your project README
4. Use `--project` and `--environment` flags for context

## 💾 Storage Migration & Backup

Conductor supports bidirectional migration between filesystem and MongoDB backends, perfect for RAMDisk workflows and team scaling.

### Quick Migration Commands

#### Backup to MongoDB (Preserves Current Config)
```bash
# Backup your agents to MongoDB without changing config.yaml
conductor --migrate-to mongodb --no-config-update
```

#### Restore from MongoDB (Preserves Current Config)  
```bash
# Restore agents from MongoDB without changing config.yaml
conductor --migrate-from mongodb --migrate-to filesystem --no-config-update
```

#### Permanent Migration to MongoDB
```bash
# Migrate permanently to MongoDB (updates config.yaml)
conductor --migrate-to mongodb
```

#### External Backup (Private Git Repository)
```bash
# Backup to external path (useful for private Git repos)
conductor --migrate-to filesystem --path /path/to/private-repo/.conductor_workspace
```

### MongoDB Configuration

Add to your `.env` file:
```bash
MONGO_URI=mongodb://username:password@localhost:27017/conductor_state?authSource=admin
MONGO_DATABASE=conductor_state
MONGO_COLLECTION=agent_states
```

### Use Cases

**RAMDisk Users**: Use `--no-config-update` to backup safely without changing your filesystem setup
**Team Scaling**: Migrate permanently to MongoDB when multiple developers need shared state
**Private Backups**: Use `--path` to backup to private Git repositories
**Hybrid Workflows**: Keep filesystem as default, use MongoDB for critical backups

### Migration Features

✅ **Bidirectional**: filesystem ↔ mongodb  
✅ **Safe**: Automatic config.yaml backup before changes  
✅ **Fast**: Optimized for bulk operations (19 agents in ~0.1s)  
✅ **Compatible**: Works alongside existing SSD backup (`conductor --backup`)  
✅ **Flexible**: Preserve or update configuration as needed  

### Troubleshooting

**MongoDB not configured**: Add MONGO_URI to your .env file  
**Connection failed**: Check if MongoDB is running and credentials are correct  
**Permission denied**: Ensure write permissions for target directories