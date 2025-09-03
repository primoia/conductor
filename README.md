# 🎼 Conductor: The AI-Powered Orchestration Framework

> **Conductor is an AI ecosystem that turns dialogue into production-ready code through interactive and orchestrated agents.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)]()

---

## 🚀 Overview

Conductor is a multi-agent framework designed to provide a robust platform for AI-assisted development and automation. It allows you to create, manage, and orchestrate specialized AI agents that can reason, plan, and execute complex coding tasks by interacting with your codebase.

-   **Orchestrate Complex Workflows:** Define multi-step plans in simple YAML files and let Conductor execute them automatically.
-   **Interact with Specialist Agents:** Dialogue with AI agents that have access to your code, enabling a conversational approach to development.
-   **Multi-Provider Support:** Flexibly switch between different AI providers like Gemini and Claude for each agent.
-   **Safe & Secure:** Agents operate in a secure environment with scoped file system access and human-in-the-loop confirmations for critical operations.

## ✨ Key Features

-   💬 **Interactive Sessions:** Engage in conversations with AI agents to refine ideas and co-create solutions.
-   🤖 **Multi-Provider AI:** Configure different AI models for different agents to leverage the best tool for the job.
-   📂 **Environment-Oriented Architecture:** Safely manage and operate on multiple projects and environments.
-   🛠️ **Scoped Tool System:** Grant agents secure and controlled access to the file system.
-   🧬 **Metaprogramming:** Use agents to create and manage other agents, enabling a self-improving system.
-   📋 **Plan-Based Execution:** Automate complex coding tasks by defining a sequence of steps in a YAML workflow.

## 🏁 Getting Started

You can get Conductor up and running using either Docker (recommended for ease of use) or a local Python environment.

### 1. Using Docker (Recommended)

This is the easiest way to start. With Docker and Docker Compose installed, simply run:

```bash
docker-compose up --build
```

This command will build the Docker image, install all dependencies, and start the Conductor service.

### 2. Local Python Environment

If you prefer to run locally:

**Prerequisites:**
-   Python 3.8+
-   [Poetry](https://python-poetry.org/docs/#installation) for dependency management.

**Installation:**
```bash
# 1. Clone the repository
git clone https://github.com/your-username/conductor.git
cd conductor

# 2. Install dependencies using Poetry
poetry install

# 3. Set up your environment variables
cp .env.example .env
# Edit .env and add your API keys (e.g., ANTHROPIC_API_KEY)
```

## ⚙️ Quick Start: Running Your First Agent

Conductor uses a simple CLI to interact with agents. The main entry point is `src/cli/agent.py`.

1.  **Configure a Workspace:**
    First, tell Conductor where your projects are located by editing `config/workspaces.yaml`:
    ```yaml
    # config/workspaces.yaml
    workspaces:
      # Maps the 'default' environment to a specific directory
      default: /path/to/your/projects
    ```

2.  **Run an Agent:**
    Use the following command to start an interactive session with an agent.
    ```bash
    # Syntax: poetry run python src/cli/agent.py --environment <env> --project <proj> --agent <agent_id>
    
    # Example:
    poetry run python src/cli/agent.py --environment default --project my-cool-project --agent CodeGenerator_Agent
    ```
    This will start a chat session where you can give instructions to the `CodeGenerator_Agent` to work on `my-cool-project`.

## 📚 Documentation

-   **[Full Documentation](docs/README.md):** Dive deeper into Conductor's architecture, features, and guides.
-   **[Configuration Guide](docs/guides/configuration.md):** Learn how to configure workspaces, AI providers, and workflows.
-   **[Agent Design Patterns](docs/guides/AGENT_DESIGN_PATTERNS.md):** Best practices for creating effective agents.

## 🤝 Contributing

We welcome contributions from the community! Please read our **[Contributing Guide](CONTRIBUTING.md)** to learn how you can get involved.

Also, be sure to review our **[Code of Conduct](CODE_OF_CONDUCT.md)** to understand our community standards.

---

**🎼 Conductor** - Orchestrating dialogue, transforming ideas into code.
