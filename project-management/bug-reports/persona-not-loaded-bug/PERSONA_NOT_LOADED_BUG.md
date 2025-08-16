# 🎭💔 Persona Not Loaded Bug - Genesis Agent

## 📋 **Resumo**
O Genesis Agent não carrega nem incorpora a persona definida no arquivo `persona.md` do agente. O agente responde como "Claude Code" genérico em vez de assumir a personalidade específica definida na persona.

## 🔍 **Comportamento Observado**
```
> ola. qual sua especialidade?
Olá! Sou Claude Code, especializado em tarefas de engenharia de software. Posso ajudar com:

- Análise e modificação de código
- Depuração e correção de bugs
- Implementação de novas funcionalidades
- Refatoração de código
- Execução de comandos e scripts
- Análise de repositórios Git

Como posso ajudá-lo hoje?
```

## ✅ **Comportamento Esperado**
O agente deveria responder como "Contexto", o Analisador de Sistemas, conforme definido na persona.md:

```
> ola. qual sua especialidade?
Olá! Sou "Contexto", seu Analisador de Sistemas. Sou um Arquiteto de Software Sênior e Analista de Sistemas especialista em diagnóstico de problemas e levantamento de requisitos.

Meu único objetivo é colaborar com você (o "Maestro") para transformar uma ideia ou problema inicial em uma especificação clara, detalhada e profundamente contextualizada com o código-fonte existente.

Como posso ajudá-lo hoje?
```

## 🎯 **Impacto**
- **Severidade**: Alta
- **Área**: Sistema de embodiment de agentes
- **Componente**: `scripts/genesis_agent.py`
- **Agente Afetado**: Todos os agentes (testado com ProblemRefiner_Agent)
- **Funcionalidade**: Modo interativo (--repl) não funciona conforme especificado

## 📊 **Evidências**

### 1. **Persona Definida vs Resposta Real**
**Persona Definida (persona.md):**
```markdown
# Persona: Agente Analisador de Problemas

## 1. Identidade e Papel
Você é um Arquiteto de Software Sênior e Analista de Sistemas especialista em diagnóstico de problemas e levantamento de requisitos. Seu nome é **"Contexto"**.
```

**Resposta Real:**
```
Olá! Sou Claude Code, especializado em tarefas de engenharia de software...
```

### 2. **Estado Persistido vs Comportamento**
O arquivo `state.json` mostra que a conversa está sendo persistida corretamente, mas a persona não é aplicada:

```json
{
  "conversation_history": [
    {
      "prompt": "ola. qual sua especialidade?",
      "response": "Olá! Sou Claude Code, especializado em tarefas de engenharia de software...",
      "timestamp": 1755352341.4116113
    }
  ]
}
```

### 3. **Configuração vs Implementação**
O `agent.yaml` define corretamente:
```yaml
persona_prompt_path: "persona.md"
```

Mas o código não carrega este arquivo durante o embodiment.

## 📅 **Informações do Ambiente**
- **Data**: 2025-08-16
- **Versão**: Conductor Framework atual
- **Comando usado**: `python scripts/genesis_agent.py --embody ProblemRefiner_Agent --project-root /mnt/ramdisk/primoia-main/conductor --repl`
- **AI Provider**: Claude CLI
- **Agente Testado**: ProblemRefiner_Agent

## 🔧 **Root Cause**
O método `embody_agent()` em `genesis_agent.py` carrega o `agent.yaml` e o `state.json`, mas **não carrega o arquivo `persona.md`** especificado em `persona_prompt_path`. O LLM client não recebe a persona como parte do prompt do sistema.

## 🎯 **Solução Proposta**
1. Modificar `embody_agent()` para carregar o arquivo `persona.md`
2. Integrar a persona no prompt do sistema enviado ao LLM
3. Garantir que a persona seja aplicada em todas as interações
4. Adicionar testes para validar o embodiment correto
