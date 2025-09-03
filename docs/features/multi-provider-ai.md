# Multi-Provider AI Support

The Conductor framework is designed to be LLM provider-agnostic, allowing you to choose the most suitable model for each agent or task.

**Supported Providers:**
- Anthropic Claude
- Google Gemini

**Configuration:**
The choice of provider is made in each agent's `agent.yaml` file, through the `ai_provider` key.

```yaml
ai_provider: 'claude' # or 'gemini'
```

This flexibility allows you to optimize costs and performance by, for example, using Claude for complex reasoning tasks and Gemini for faster code generation or summarization. The framework abstracts away the differences between providers, providing a unified interface for agent development.