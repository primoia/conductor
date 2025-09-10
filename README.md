# 🎼 Conductor: The AI-Powered Orchestration Framework

> **Conductor is an AI ecosystem that turns dialogue into production-ready code through interactive and orchestrated agents.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)]()

---

## 🚀 Overview

Conductor is a multi-agent framework designed to provide a robust platform for AI-assisted development and automation. It allows you to create, manage, and orchestrate specialized AI agents that can reason, plan, and execute complex coding tasks by interacting with your codebase.

```
+-----------+        +-------------------+        +----------------+
|           |        |                   |        |                |
|  Developer|--💬-->|     Conductor     |--⚙️-->|    Agents      |
|           | Dialogue   |  (Orchestrator)   | Orchestrates| (Database, Coder)|
+-----------+        |                   |        |                |
                     +---------+---------+        +-------+--------+
                               |                          |
                               | Analysis & Planning      | Execution
                               |                          |
                               ▼                          ▼
                     +------------------------------------------+
                     |                                          |
                     |               Codebase                   |
                     |                                          |
                     +------------------------------------------+
```

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

### 💡 A Practical Example

**The traditional way:** To add a field to a database entity, you need to:
1.  Write the database migration.
2.  Change the entity class in the code.
3.  Update the DTO (Data Transfer Object).
4.  Expose the new field in the API.
5.  Update the tests.

**With Conductor:** You simply instruct the agent:
> *"Add a 'last_login' date field to the User entity, including the database migration, DTO, and API endpoint."*

Conductor then orchestrates the specialist agents needed to execute all steps automatically.

### 👥 Who is Conductor for?
- **Developers & Agile Teams** who want to accelerate development and automate repetitive coding tasks.
- **DevOps Engineers** looking to automate the configuration and maintenance of infrastructure as code.
- **AI Enthusiasts** who want a robust platform to build and experiment with multi-agent systems.

## Getting Started

O Conductor agora opera sob uma arquitetura unificada e orientada a serviços. Toda a configuração é centralizada no arquivo `config.yaml` na raiz do projeto.

### 1. Configuração

Antes de rodar qualquer agente, configure seu ambiente no `config.yaml`:

```yaml
# config.yaml
storage:
  type: filesystem
  path: .conductor_workspace

# Adicione aqui diretórios para suas ferramentas customizadas
tool_plugins:
  - custom_tools/
```

-   **storage**: Define onde os dados dos agentes são armazenados.
    -   `filesystem`: (Padrão) Ideal para desenvolvimento local, não requer dependências.
    -   `mongodb`: Para ambientes de equipe ou produção.
-   **tool_plugins**: Lista de diretórios onde o Conductor irá procurar por ferramentas customizadas.

### 2. Executando Agentes

Embora estejamos caminhando para um CLI unificado, você ainda pode usar os CLIs `admin.py` e `agent.py`. Eles agora operam como interfaces para o novo serviço central e respeitam o `config.yaml`.

**Para Meta-Agentes:**
```bash
poetry run python src/cli/admin.py --agent AgentCreator_Agent --input "Crie um novo agente para analisar logs."
```

**Para Agentes de Projeto:**
```bash
poetry run python src/cli/agent.py --environment develop --project desafio-meli --agent ProductAnalyst_Agent --input "Analise os dados de produtos."
```

## 📚 Documentation

-   **[Full Documentation](docs/README.md):** Dive deeper into Conductor's architecture, features, and guides.
-   **[Configuration Guide](docs/guides/configuration.md):** Learn how to configure workspaces, AI providers, and workflows.
-   **[Agent Design Patterns](docs/guides/AGENT_DESIGN_PATTERNS.md):** Best practices for creating effective agents.

## ❤️ Support Conductor

Conductor is an open-source project driven by passion and innovation. Your support helps us maintain the project, develop new features, improve documentation, and grow our community.

### Ways to Support:

-   **Become a GitHub Sponsor:** Support us with recurring contributions directly through GitHub.
    [![Sponsor](https://img.shields.io/github/sponsors/cezarfuhr?style=flat&label=Sponsor)](https://github.com/sponsors/cezarfuhr)
    *(You'll need to set up GitHub Sponsors on your profile.)*
-   **Buy Me a Coffee:** Make a one-time or recurring donation to support our work.
    [![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow.svg)](https://buymeacoffee.com/cezarfuhr)
-   **Direct Contributions:** For larger contributions or corporate partnerships, please reach out via our [Consulting & Advisory Services](project-management/CONSULTING.md) page.
-   **Spread the Word:** Star our repository, share it with your network, and use Conductor in your projects!

Thank you for being a part of our journey!

## 🤝 Contributing

We welcome contributions from the community! Please read our **[Contributing Guide](CONTRIBUTING.md)** to learn how you can get involved.

Also, be sure to review our **[Code of Conduct](CODE_OF_CONDUCT.md)** to understand our community standards.

---

**🎼 Conductor** - Orchestrating dialogue, transforming ideas into code.