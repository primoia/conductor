# Suporte a Múltiplos Provedores de IA

O framework é projetado para ser agnóstico em relação ao provedor de LLM, permitindo que você escolha o modelo mais adequado para cada agente ou tarefa.

**Provedores Suportados:**
- Anthropic Claude
- Google Gemini

**Configuração:**
A escolha do provedor é feita no arquivo `agent.yaml` de cada agente, através da chave `ai_provider`.

```yaml
ai_provider: 'claude' # ou 'gemini'
```

Isso permite, por exemplo, usar o Claude para tarefas de diálogo e o Gemini para geração de código, otimizando custos e performance.
