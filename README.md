# 🎼 Conductor: The AI-Powered Orchestration Framework

> **Conductor is an AI ecosystem that turns dialogue into production-ready code through interactive and orchestrated agents.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Overview

Conductor is a multi-agent framework that provides a robust platform for AI-assisted development and automation. It allows you to create, manage, and orchestrate specialized AI agents that can reason, plan, and execute complex coding tasks by interacting with your codebase.

- **Orchestrate Complex Workflows:** Define multi-step plans in simple YAML files and let Conductor execute them automatically.
- **Interact with Specialist Agents:** Dialogue with AI agents that have access to your code, enabling a conversational approach to development.
- **Multi-Provider Support:** Flexibly switch between different AI providers like Gemini and Claude for each agent.
- **Safe & Secure:** Agents operate in a secure environment with scoped file system access and human-in-the-loop confirmations for critical operations.

## ✨ Key Features

- 💬 **Interactive Sessions:** Engage in conversations with AI agents to refine ideas and co-create solutions.
- 🤖 **Multi-Provider AI:** Configure different AI models for different agents to leverage the best tool for the job.
- 📂 **Environment-Oriented Architecture:** Safely manage and operate on multiple projects and environments.
- 🛠️ **Scoped Tool System:** Grant agents secure and controlled access to the file system.
- 🧬 **Metaprogramming:** Use agents to create and manage other agents, enabling a self-improving system.
- 📋 **Plan-Based Execution:** Automate complex coding tasks by defining a sequence of steps in a YAML workflow.

### 💡 A Practical Example

**The traditional way:** To add a field to a database entity, you need to:
1. Write the database migration.
2. Change the entity class in the code.
3. Update the DTO (Data Transfer Object).
4. Expose the new field in the API.
5. Update the tests.

**With Conductor:** You simply instruct the agent:
> *"Add a 'last_login' date field to the User entity, including the database migration, DTO, and API endpoint."*

Conductor then orchestrates the specialist agents needed to execute all steps automatically.

### 👥 Who is Conductor for?

- **Developers & Agile Teams** who want to accelerate development and automate repetitive coding tasks.
- **DevOps Engineers** looking to automate the configuration and maintenance of infrastructure as code.
- **AI Enthusiasts** who want a robust platform to build and experiment with multi-agent systems.

## 🚀 Getting Started

### 1. Configuration

Create your configuration file from the template:

```bash
# Copy the example configuration
cp config.yaml.example config.yaml

# Edit with your preferences
nano config.yaml
```

Configure your environment in the `config.yaml` file:

```yaml
# config.yaml
storage:
  type: filesystem  # or 'mongodb' for team environments
  path: .conductor_workspace

# AI Providers Configuration
ai_providers:
  default_providers:
    chat: cursor-agent        # Options: claude, gemini, cursor-agent
    generation: cursor-agent
  fallback_provider: cursor-agent

# Add directories for your custom tools
tool_plugins:
  - custom_tools/
```

### 2. Quick Start

```bash
# List available agents
conductor --list

# Execute a simple task (stateless, fast)
conductor --agent SystemGuide_Meta_Agent --input "Explain how Conductor works"

# Contextual conversation (with history)
conductor --agent AgentCreator_Agent --chat --input "Create a new agent"

# Interactive session (REPL)
conductor --agent AgentCreator_Agent --chat --interactive

# Install agent templates
conductor --install list
conductor --install web_development
```

## 🎯 How to Use Conductor

### Basic Commands

#### **List Available Agents**
```bash
conductor --list
```

#### **Stateless Execution (Fast, No History)**
```bash
# Basic syntax - perfect for automation and quick tasks
conductor --agent <agent_id> --input "<your_message>"

# Practical examples
conductor --agent SystemGuide_Meta_Agent --input "Explain the system architecture"
conductor --agent CommitMessage_Agent --input "Generate commit message for current changes"
conductor --agent CodeReviewer_Agent --input "Review this function: def hello(): pass"
```

#### **Contextual Chat (With History)**
```bash
# Chat with conversation history - perfect for iterative work
conductor --agent <agent_id> --chat --input "Your message"

# Continue conversation (preserves context)
conductor --agent <agent_id> --chat --input "Continue explaining"
```

#### **Interactive Sessions (REPL)**
```bash
# Interactive session after initial message
conductor --agent <agent_id> --chat --input "Start analysis" --interactive

# Direct REPL (no initial message)
conductor --agent <agent_id> --chat --interactive
```

#### **Agent Information & System Operations**
```bash
# Show agent details
conductor --info <agent_id>

# Validate system configuration
conductor --validate

# Backup and restore agents
conductor --backup
conductor --restore
```

### Typical Workflow

1. **Discover Available Agents:** `conductor --list`
2. **Create a New Agent (if needed):** Use `AgentCreator_Agent` interactively
3. **Use the Created Agent:** `conductor --agent NewAgent --input "Execute your task"`
4. **Check Agent Information:** `conductor --info NewAgent`

### Practical Examples

#### **Create and Use a Code Review Agent**
```bash
# 1. Create the agent interactively
conductor --agent AgentCreator_Agent --chat --input "Create a CodeReviewer_Agent for Python code quality analysis" --interactive

# 2. Use the created agent (stateless - fast)
conductor --agent CodeReviewer_Agent --input "Review this code: def example(): pass"

# 3. Get agent information
conductor --info CodeReviewer_Agent
```

#### **Quick Automation Tasks**
```bash
# Generate commit messages (stateless - perfect for scripts)
conductor --agent CommitMessage_Agent --input "Generate commit message for: added input validation and fixed authentication bug"

# Code analysis in CI/CD
conductor --agent SecurityAuditor_Agent --input "Audit the authentication module" --timeout 300

# Documentation generation
conductor --agent DocWriter_Agent --input "Generate API documentation for the user service"
```

### 🔧 Troubleshooting

#### **Command not found: `conductor`**
```bash
# Use full path
python src/cli/conductor.py --list

# Or make script executable
chmod +x conductor
./conductor --list
```

#### **Agent not found**
```bash
# List available agents
conductor --list

# System automatically suggests similar agents
conductor --agent TestAgent --input "test"
# Output: ❌ Agent 'TestAgent' not found
#         💡 Similar agents: TestingSpecialist_Agent, SystemGuide_Meta_Agent
```

#### **Validate everything is working**
```bash
conductor --validate
```

### 🔨 Creating New Agents

**Using AgentCreator_Agent (Recommended)**
```bash
# Interactive agent creation
conductor --agent AgentCreator_Agent --chat --interactive
[AgentCreator_Agent]> Create an agent for database performance analysis
[AgentCreator_Agent]> exit
```

> **💡 Tip:** For advanced customization and manual configuration, see the [Full Documentation](docs/README.md) and [Agent Design Patterns](docs/guides/AGENT_DESIGN_PATTERNS.md).

### 📊 Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `--list` | List all agents | `conductor --list` |
| `--agent --input` | Stateless execution | `conductor --agent MyAgent --input "text"` |
| `--agent --chat --input` | Contextual chat | `conductor --agent MyAgent --chat --input "text"` |
| `--agent --chat --interactive` | Interactive REPL | `conductor --agent MyAgent --chat --interactive` |
| `--info` | Show agent details | `conductor --info MyAgent` |
| `--validate` | Validate configuration | `conductor --validate` |

### 🎯 When to Use Each Mode

| Mode | Use Case | Example |
|------|----------|---------|
| **Stateless** (`--input`) | Quick tasks, automation, CI/CD | `conductor --agent CodeReviewer --input "review code"` |
| **Contextual** (`--chat --input`) | Iterative work, related questions | `conductor --agent AgentCreator --chat --input "continue building"` |
| **Interactive** (`--chat --interactive`) | Development, experimentation | `conductor --agent AgentCreator --chat --interactive` |

## 📚 Documentation

- **[Full Documentation](docs/README.md):** Dive deeper into Conductor's architecture, features, and guides.
- **[Configuration Guide](docs/guides/configuration.md):** Learn how to configure workspaces, AI providers, and workflows.
- **[Agent Design Patterns](docs/guides/AGENT_DESIGN_PATTERNS.md):** Best practices for creating effective agents.

## ❤️ Support Conductor

Conductor is an open-source project driven by passion and innovation. Your support helps us maintain the project, develop new features, improve documentation, and grow our community.

### Ways to Support:

- **Become a GitHub Sponsor:** Support us with recurring contributions directly through GitHub.
  [![Sponsor](https://img.shields.io/github/sponsors/cezarfuhr?style=flat&label=Sponsor)](https://github.com/sponsors/cezarfuhr)
- **Buy Me a Coffee:** Make a one-time or recurring donation to support our work.
  [![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow.svg)](https://buymeacoffee.com/cezarfuhr)
- **Direct Contributions:** For larger contributions or corporate partnerships, please reach out via our [Consulting & Advisory Services](project-management/CONSULTING.md) page.
- **Spread the Word:** Star our repository, share it with your network, and use Conductor in your projects!

Thank you for being a part of our journey!

## 🤝 Contributing

We welcome contributions from the community! Please read our **[Contributing Guide](CONTRIBUTING.md)** to learn how you can get involved.

Also, be sure to review our **[Code of Conduct](CODE_OF_CONDUCT.md)** to understand our community standards.

---

**🎼 Conductor** - Orchestrating dialogue, transforming ideas into code.