# Agent Design Guide: Patterns and Best Practices

**Version:** 1.0

**Audience:** Developers, Architects, Agent Designers

## 1. Introduction

This document establishes the standards and best practices for designing and creating Specialist Agents within the Conductor Framework. Adhering to these patterns is crucial to ensure the ecosystem is maintainable, secure, and scalable.

## 2. The Specialist Agent Philosophy

A Specialist Agent is not a general-purpose AI. It is a **precision tool**. Each agent should be designed with a **single, clear responsibility**. Avoid creating "jack-of-all-trades" agents.

*   **Good:** `KotlinEntityCreator_Agent` (creates entities), `TerraformPlanValidator_Agent` (validates Terraform plans).
*   **Bad:** `Development_Agent` (too generic), `CodeAndDocs_Agent` (two distinct responsibilities).

## 3. Anatomy of an Agent

Each agent is defined by three main files. Understanding the role of each is the first step towards good design.

*   `agent.yaml`: The **DNA**. Defines metadata, capabilities, and the AI provider. It's the agent's technical specification.
*   `persona.md`: The **Soul**. Defines the agent's personality, behavior, philosophy, and specific commands. It's how the agent "thinks."
*   `state.json`: The **Memory**. Stores session state, conversation history, and acquired knowledge. It's the agent's short-term and long-term memory.

## 4. Persona Design Patterns

The `persona.md` is the most critical component for an agent's success.

*   **Be Specific and Give a Clear Role:** Instead of "You are an AI assistant," use "You are a Senior QA Engineer specializing in regression testing."
*   **Give a Name:** Helps the AI maintain character. E.g., "Your name is 'Context'", "Your name is 'Strategist'".
*   **Define a Philosophy:** Give the agent 2-3 principles that will guide its decisions. E.g., "Principle 1: Security first. Always question the impact of a change."
*   **Structure Behavior:** Use clear sections (`## Identity`, `## Philosophy`, `## Dialogue Behavior`) to organize instructions.

## 5. Tool Usage Patterns (Special Powers)

Tools are the agent's "hands." Use them wisely.

*   **Principle of Least Privilege:** In `agent.yaml`, under the `available_tools` section, list **only** the tools the agent absolutely needs for its function. An agent that only reads code does not need `write_file` or `run_shell_command`.
*   **Security with `run_shell_command`:** This is the most powerful and dangerous tool. Adhering to the `allowlist` of safe commands defined in the Conductor engine is mandatory. The persona of an agent using this tool should be instructed to be extremely cautious.
*   **Idempotence:** Whenever possible, design tasks to be idempotent. If a task is executed twice, the result should be the same. This makes the system more resilient.

## 6. Choosing the AI Provider (`ai_provider`)

The choice of AI in `agent.yaml` should be a conscious design decision, based on the agent's task.

*   **Use `claude` (Claude 3.5 Sonnet or higher) for:**
    *   Complex, multi-step reasoning tasks.
    *   High-quality and complex code generation.
    *   Security and architecture analysis.
    *   Agents that need to follow long and detailed instructions (like the `AgentCreator_Agent`).

*   **Use `gemini` (Gemini 1.5 Flash/Pro) for:**
    *   Data extraction and summarization tasks.
    *   Documentation generation from code.
    *   Content translation.
    *   Tasks requiring lower cost and faster response, with slightly less complex reasoning.

## 7. State Management (`state.json`)

The `state.json` is the agent's memory. Use it to provide continuity and context between sessions.

*   **Define a Schema:** Use the optional `state_schema` key in `agent.yaml` to document the expected structure of your `state.json`. This aids in maintenance.
*   **Do Not Store Secrets:** The state is saved to disk as plain text. Never store passwords, API keys, or other sensitive information in the state.
*   **Keep it Lean:** Avoid saving massive data (like the content of entire files) in the state. Save references (file paths) or summaries. Conductor's memory management (sliding window) helps with conversation history, but structured state is the agent designer's responsibility.