# Configuration Guide

This guide explains the purpose and parameters of each configuration file within the `config/` directory and its subdirectories.

## `config/` Directory

### `agent-template.md`
**Purpose:** This file serves as a template for creating new agent personas. It defines the basic structure and common sections that should be present in every agent's `persona.md` file.

### `ai_providers.yaml`
**Purpose:** Configures the available AI providers and their respective API keys or credentials. This file allows you to define which LLMs Conductor can use and how to authenticate with them.
**Parameters:**
- `providers`: A list of AI provider configurations.
  - `id`: Unique identifier for the provider (e.g., `claude`, `gemini`).
  - `type`: The type of AI provider (e.g., `anthropic`, `google`).
  - `api_key`: Your API key for the provider.
  - `model`: The specific model to use (e.g., `claude-3-5-sonnet-20240620`, `gemini-1.5-flash`).

### `onboarding_rules.yaml`
**Purpose:** Defines rules and guidelines for the project onboarding process. It can specify required information, default settings, or automated steps during project setup.

### `orchestrator-template.md`
**Purpose:** This file serves as a template for creating new orchestrator plans. It defines the basic structure and common sections for `implementation_plan.yaml` files.

### `state-template.json`
**Purpose:** Provides a default structure for the `state.json` file of new agents. This ensures consistency in how agent memory and conversation history are initialized.

### `config.yaml` (Centralized Configuration)
**Purpose:** Centralized configuration for all Conductor operations, including storage backend, agent discovery, and tool plugins.
**Parameters:**
- `storage`: Configuration for data storage backend.
  - `type`: Storage type (`filesystem` or `mongodb`).
  - `path`: Path for filesystem storage (default: `.conductor_workspace`).
- `tool_plugins`: List of directories containing custom tool plugins.

## `config/teams/` Directory

These YAML files define pre-configured teams of agents, often tailored for specific development stacks or roles. They can be used to quickly set up a group of specialized agents for a project.

### `backend-kotlin-dev-team.yaml`
**Purpose:** Defines a team of agents specialized in backend development using Kotlin.

### `devops-basic-team.yaml`
**Purpose:** Defines a team of agents focused on basic DevOps tasks.

### `frontend-react-dev-team.yaml`
**Purpose:** Defines a team of agents specialized in frontend development using React.

## `config/workflows/` Directory

These YAML files define automated workflows or sequences of tasks that Conductor can execute. They orchestrate multiple agents to achieve a larger goal.

### `devops_add_monitoring.yaml`
**Purpose:** Defines a workflow for adding monitoring capabilities to a project.

### `devops_setup_basic_deployment.yaml`
**Purpose:** Defines a workflow for setting up a basic deployment pipeline.

### `kotlin_add_entity_field.yaml`
**Purpose:** Defines a workflow for adding a new field to a Kotlin entity.

### `kotlin_create_entity_complete.yaml`
**Purpose:** Defines a workflow for creating a complete Kotlin entity, including related files.

### `react_create_page_complete.yaml`
**Purpose:** Defines a workflow for creating a complete React page, including components and routing.

### `react_create_reusable_component.yaml`
**Purpose:** Defines a workflow for creating a reusable React component.
