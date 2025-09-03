# Agent Evaluation Process Guide

**Status:** Active
**Version:** 2.0

## 1. Objective

This document describes the standard and reusable process for conducting a 360-degree evaluation of the Conductor framework. The cycle consists of dynamically creating an agent, using that agent to perform a task (such as creating a project), formally evaluating the agent's performance, and recording the result for continuous improvement analysis.

---

## 2. Execution Phases

The cycle is divided into 4 main phases, orchestrated by an Orchestrator agent and executed by an Executor agent.

### Phase 0: Study and Preparation (Orchestrator)

Before starting a new cycle, the orchestrator must study the scripts (`src/cli/admin.py`, `src/cli/agent.py`, `run_agent_evaluation.sh`) to ensure that the commands and parameters to be used are correct and up-to-date.

### Phase 1: Agent Creation

- **Tool:** `src/cli/admin.py`
- **Standard Command:**
  ```bash
  poetry run python src/cli/admin.py --agent AgentCreator_Agent --input "<PROMPT_FOR_AGENT_CREATION>" --destination-path "<PATH_TO_NEW_AGENT>" --ai-provider claude
  ```

### Phase 2: Execution of the Created Agent

- **Tool:** `src/cli/agent.py`
- **Standard Command:**
  ```bash
  poetry run python src/cli/agent.py --agent <CREATED_AGENT_NAME> --environment <TARGET_ENVIRONMENT> --project <TARGET_PROJECT> --input "<PROMPT_FOR_TASK_EXECUTION>" --ai-provider claude
  ```

### Phase 3: Formal Evaluation

- **Tool:** `run_agent_evaluation.sh`
- **Prerequisite:** A test case (`.yaml`) must be created in `projects/conductor/evaluation_cases/` for the agent in question.
- **Standard Command:**
  ```bash
  bash projects/conductor/scripts/run_agent_evaluation.sh --agent <CREATED_AGENT_NAME>
  ```

---

## 3. Post-Cycle Procedure

At the end of each execution cycle, the following verification and logging steps are mandatory.

1.  **Artifact Review:** The orchestrator must review all artifacts generated during the process. This includes the new agent's configuration files, the project or files created by the task, and the execution logs to ensure quality and consistency.

2.  **Result Collection:** The orchestrator must locate the evaluation report generated in `projects/conductor/.evaluation_output/` and extract the consolidated final score.

3.  **Log Recording:** **The final and mandatory step is to record the results.** The date, cycle ID, tested agent, final score, and relevant observations must be added as a new line in the table of the `360_EVALUATION_LOG.md` file.

---

## 4. Parameter Reference

This section documents the parameters of the main scripts used in this evaluation cycle.

### `src/cli/admin.py`

- **Objective:** Execute meta-agents that manage the framework itself (e.g., `AgentCreator_Agent`).
- **Relevant Parameters:**
  - `--agent <AGENT_ID>`: (Required) Specifies the meta-agent to be executed.
  - `--input "<INSTRUCTION>"`: (Optional) Allows passing an instruction to the agent non-interactively for automation.
  - `--destination-path <PATH>`: (Optional) Specifies the destination path for agent creation in non-interactive mode.
  - `--ai-provider <claude|gemini>`: (Optional) Forces the use of a specific AI provider.
  - `--repl`: (Optional) Starts an interactive console session with the agent.
  - `--debug`: (Optional) Activates detailed logs in the console.
- **⚠️ Known Issue:** State management (`state.json`) may not work reliably when using non-interactive mode.

### `src/cli/agent.py`

- **Objective:** Execute project agents that operate on external codebases.
- **Relevant Parameters:**
  - `--environment <ENVIRONMENT_NAME>`: (Required) Working environment (e.g., `develop`).
  - `--project <PROJECT_NAME>`: (Required) Target project where the agent will operate.
  - `--agent <AGENT_ID>`: (Required) Agent to be executed.
  - `--input "<INSTRUCTION>"`: (Optional) Allows passing an instruction to the agent non-interactively.
  - `--repl`: (Optional) Starts interactive mode.
  - `--ai-provider <claude|gemini>`: (Optional) Forces the use of an AI provider.
  - `--timeout <SECONDS>`: (Optional) Sets the maximum time for AI operation.

### `run_agent_evaluation.sh`

- **Objective:** Execute the evaluation framework for a specific agent.
- **Relevant Parameters:**
  - `--agent <AGENT_NAME>`: (Required) The name of the agent to be evaluated, which must correspond to a test case in `evaluation_cases/`.