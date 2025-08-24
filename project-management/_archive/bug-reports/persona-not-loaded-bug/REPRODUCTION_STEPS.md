# 🔄 Reproduction Steps - Persona Not Loaded Bug

## 📋 **Passos Exatos para Reproduzir o Bug**

### **Pré-requisitos**
- Conductor Framework instalado
- Claude CLI configurado e funcionando
- Acesso ao diretório do projeto

### **Passo 1: Preparar o Ambiente**
```bash
# Navegar para o diretório do conductor
cd /mnt/ramdisk/primoia-main/conductor

# Verificar se o agente existe
ls -la projects/develop/agents/ProblemRefiner_Agent/
```

**Resultado Esperado:**
```
total 20
drwxr-xr-x 2 user user 4096 Aug 16 10:52 .
drwxr-xr-x 8 user user 4096 Aug 16 10:52 ..
-rw-r--r-- 1 user user 1340 Aug 16 10:52 agent.yaml
-rw-r--r-- 1 user user 2640 Aug 16 10:52 persona.md
-rw-r--r-- 1 user user  800 Aug 16 10:52 state.json
```

### **Passo 2: Verificar a Persona Definida**
```bash
# Verificar o conteúdo da persona
cat projects/develop/agents/ProblemRefiner_Agent/persona.md
```

**Resultado Esperado:**
```markdown
# Persona: Agente Analisador de Problemas

## 1. Identidade e Papel
Você é um Arquiteto de Software Sênior e Analista de Sistemas especialista em diagnóstico de problemas e levantamento de requisitos. Seu nome é **"Contexto"**.
```

### **Passo 3: Executar o Genesis Agent**
```bash
# Executar o agente em modo REPL
python scripts/genesis_agent.py --embody ProblemRefiner_Agent --project-root /mnt/ramdisk/primoia-main/conductor --repl
```

**Resultado Esperado:**
```
2025-08-16 10:52:03,254 - INFO - GenesisAgent initialized with provider: claude
2025-08-16 10:52:03,256 - INFO - Successfully embodied agent: ProblemRefiner_Agent
Successfully embodied ProblemRefiner_Agent
Genesis Agent REPL started. Type 'exit' to quit.
>
```

### **Passo 4: Testar a Persona**
```bash
# No REPL, digite:
> ola. qual sua especialidade?
```

**❌ Comportamento Atual (Bug):**
```
Olá! Sou Claude Code, especializado em tarefas de engenharia de software. Posso ajudar com:

- Análise e modificação de código
- Depuração e correção de bugs
- Implementação de novas funcionalidades
- Refatoração de código
- Execução de comandos e scripts
- Análise de repositórios Git

Como posso ajudá-lo hoje?
```

**✅ Comportamento Esperado (Correto):**
```
Olá! Sou "Contexto", seu Analisador de Sistemas. Sou um Arquiteto de Software Sênior e Analista de Sistemas especialista em diagnóstico de problemas e levantamento de requisitos.

Meu único objetivo é colaborar com você (o "Maestro") para transformar uma ideia ou problema inicial em uma especificação clara, detalhada e profundamente contextualizada com o código-fonte existente.

Como posso ajudá-lo hoje?
```

### **Passo 5: Verificar o Estado Persistido**
```bash
# Sair do REPL
> exit

# Verificar se o estado foi persistido
cat projects/develop/agents/ProblemRefiner_Agent/state.json
```

**Resultado Esperado:**
```json
{
  "version": "1.0",
  "agent_id": "ProblemRefiner_Agent",
  "status": "IDLE",
  "current_problem_id": null,
  "conversation_history": [
    {
      "prompt": "ola. qual sua especialidade?",
      "response": "Olá! Sou Claude Code, especializado em tarefas de engenharia de software...",
      "timestamp": 1755352341.4116113
    }
  ],
  "files_analyzed": [],
  "last_updated": "2025-08-16T10:53:04.518180"
}
```

### **Passo 6: Testar Memória (Opcional)**
```bash
# Reentrar no REPL
python scripts/genesis_agent.py --embody ProblemRefiner_Agent --project-root /mnt/ramdisk/primoia-main/conductor --repl

# Testar se lembra da conversa anterior
> qual é meu nome?
```

**❌ Comportamento Atual (Bug):**
```
Você não mencionou seu nome nesta conversa. Como posso ajudá-lo?
```

**✅ Comportamento Esperado (Correto):**
```
Você disse que seu nome é João na conversa anterior.
```

## 🎯 **Critérios de Reprodução**

### **Bug Confirmado Se:**
1. ✅ O agente responde como "Claude Code" em vez de "Contexto"
2. ✅ A persona definida em `persona.md` é ignorada
3. ✅ O agente não assume a personalidade específica
4. ✅ O comportamento é genérico, não especializado

### **Bug Não Reproduzido Se:**
1. ❌ O agente responde como "Contexto"
2. ❌ A persona é aplicada corretamente
3. ❌ O comportamento é especializado conforme definido

## 📊 **Dados de Reprodução**

### **Ambiente de Teste**
- **Sistema Operacional:** Linux 6.14.0-27-generic
- **Python Version:** 3.x
- **Conductor Framework:** Versão atual
- **Claude CLI:** Configurado e funcionando
- **Data do Teste:** 2025-08-16

### **Comandos Executados**
```bash
cd /mnt/ramdisk/primoia-main/conductor
python scripts/genesis_agent.py --embody ProblemRefiner_Agent --project-root /mnt/ramdisk/primoia-main/conductor --repl
```

### **Logs Gerados**
```
2025-08-16 10:52:03,254 - INFO - GenesisAgent initialized with provider: claude
2025-08-16 10:52:03,256 - INFO - Successfully embodied agent: ProblemRefiner_Agent
Successfully embodied ProblemRefiner_Agent
Genesis Agent REPL started. Type 'exit' to quit.
```

## 🔍 **Observações Importantes**

1. **Estado Persistido:** O sistema persiste corretamente a conversa no `state.json`
2. **Configuração Carregada:** O `agent.yaml` é carregado corretamente
3. **Persona Ignorada:** O arquivo `persona.md` existe mas não é usado
4. **LLM Funcionando:** O Claude CLI responde corretamente, mas sem contexto de persona

## 🎯 **Conclusão**

O bug é **100% reproduzível** seguindo estes passos. O problema está na **falta de integração** entre o arquivo `persona.md` e o sistema de embodiment do Genesis Agent.
