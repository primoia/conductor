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
conductor chat --agent <agent_id> --input "Your message"
```
Sends a message while preserving conversation context.

### Chat with History Management
```bash
# Show conversation history after response
conductor chat --agent <agent_id> --input "Continue" --show-history

# Clear history before new conversation
conductor chat --agent <agent_id> --input "New topic" --clear-history
```

## 🔧 Agent Management

### Install Agent Templates
```bash
# List available templates
conductor install --list

# Install specific category
conductor install --category web_development

# Install specific agent
conductor install --agent ReactExpert_Agent
```

### Backup and Restore
```bash
# Backup all agents
conductor backup

# Restore from backup
conductor restore
```

## 🎯 Advanced Usage

### Project Context
```bash
# Execute with project context
conductor execute --agent TestAgent --environment develop --project myapp --input "Run tests"

# REPL with project context
conductor repl --agent TestAgent --environment develop --project myapp
```

### Meta-Agent Operations
```bash
# Create new agents
conductor repl --agent AgentCreator_Agent --meta --mode dev

# Chat for agent creation
conductor chat --agent AgentCreator_Agent --meta --input "Create a new agent for X"
```

### Timeout Configuration
```bash
# Custom timeout for long operations
conductor execute --agent MyAgent --input "Complex task" --timeout 300
```

## 🛠️ Practical Examples

### Creating a New Agent
```bash
# Interactive agent creation
conductor repl --agent AgentCreator_Agent --mode dev
[AgentCreator_Agent]> Create a CodeReviewer_Agent for Python code analysis
[AgentCreator_Agent]> Add capabilities for PEP8 checking and security analysis
[AgentCreator_Agent]> exit

# Verify creation
conductor list-agents | grep CodeReviewer
conductor info --agent CodeReviewer_Agent
```

### Code Review Workflow
```bash
# Quick code review
conductor execute --agent CodeReviewer_Agent --input "Review this function: def process_data(data): return data.strip().lower()"

# Interactive review session
conductor repl --agent CodeReviewer_Agent --mode advanced
[CodeReviewer_Agent]> Review the authentication module
[CodeReviewer_Agent]> debug  # Check agent state
[CodeReviewer_Agent]> What security issues did you find?
[CodeReviewer_Agent]> exit
```

### Documentation Analysis
```bash
# Analyze project documentation
conductor execute --agent DocumentAnalyst_Agent --input "Analyze all README files and suggest improvements"

# Interactive documentation session
conductor chat --agent DocumentAnalyst_Agent --input "What's missing from our docs?"
conductor chat --agent DocumentAnalyst_Agent --input "How can we improve onboarding?" --show-history
```

## 🚨 Troubleshooting

### Common Issues

#### Agent Not Found
```bash
# List available agents
conductor list-agents

# System suggests similar agents automatically
conductor execute --agent TestAgent --input "test"
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