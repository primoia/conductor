# Onboarding a New Project

**Version:** 2.0

**Audience:** Developers, Architects

## 1. Introduction

This guide describes the step-by-step process for configuring a new software project to be managed by the Conductor agent ecosystem. The goal is to enable Conductor agents to operate safely and with full context within your project's codebase.

## 2. Prerequisites

-   Conductor should be cloned and configured on your local machine.
-   The project you want to integrate must have a Git repository and be accessible on your file system.

## 3. Step-by-Step Guide

### Step 1: Verify Configuration

Conductor uses a centralized configuration in `config.yaml` at the project root. All agents are stored in `.conductor_workspace/agents/` regardless of type.

**Example:**
```yaml
# config.yaml
storage:
  type: filesystem
  path: .conductor_workspace
  default: /home/user/projects/my-workspace
```

In this example, any project located inside `/home/user/projects/my-workspace` can be accessed by Conductor using the `default` environment.

### Step 2: Create the Project's Agent Directory

Conductor organizes agents by environment and project. To create agents for your project, you first need to create a dedicated directory for them.

Suppose your project is named **`my-new-app`** and it is located inside the `default` workspace path you defined above (`/home/user/projects/my-workspace/my-new-app`).

1.  Navigate to the Conductor `projects` directory.
2.  Create the following directory structure:

    ```bash
    # Command executed from the Conductor root directory
    mkdir -p projects/default/my-new-app/agents
    ```

-   **Explanation:**
    -   `projects/default/`: Represents the `default` environment.
    -   `my-new-app/`: Is the specific directory for your project's agent configurations.
    -   `agents/`: This folder will contain all the custom Specialist Agents for this project.

### Step 3: Create Your First Specialist Agent

The best way to validate the setup is to create an agent. You can do this by running the `AgentCreator_Agent`.

```bash
# Run the agent creation process
poetry run python src/cli/admin.py --agent AgentCreator_Agent
```

During the conversation, specify the environment and project:
-   **Environment:** `default`
-   **Project:** `my-new-app`
-   **Agent ID:** (e.g., `MyFirstAgent`)

Conductor will create the agent's files inside `projects/default/my-new-app/agents/MyFirstAgent/`.

### Step 4: Run the Agent in Your Project's Context

With your new agent created, you can now interact with it in the context of your project.

```bash
# Syntax: poetry run python src/cli/agent.py --environment <env> --project <project_name> --agent <agent_id>

# Example:
poetry run python src/cli/agent.py --environment default --project my-new-app --agent MyFirstAgent
```

In this session, `MyFirstAgent` will have the ability to read and write files safely within your project's directory (`/home/user/projects/my-workspace/my-new-app`).

## 4. Conclusion

Your project is now onboarded! You can create as many specialist agents as you need for your project within its corresponding `agents` folder. Conductor will know how to load and run them in the correct context, ensuring that each agent's operations are contained within the specified project.