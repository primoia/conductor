# 🔄 Passos para Reproduzir - Chat Memory Amnesia Bug

## 📋 **Pré-requisitos**
- Conductor Framework instalado
- Claude CLI configurado
- Agente ProblemRefiner_Agent disponível

## 🎯 **Passos para Reprodução**

### **Passo 1: Iniciar o Genesis Agent**
```bash
cd /mnt/ramdisk/primoia-main/conductor
python scripts/genesis_agent.py --embody ProblemRefiner_Agent --project-root /mnt/ramdisk/primoia-main/conductor --repl
```

### **Passo 2: Primeira interação**
```
> ola
```
**Resultado esperado**: Agente responde cumprimentando

### **Passo 3: Segunda interação**
```
> qual sua funcao?
```
**Resultado esperado**: Agente explica sua função

### **Passo 4: Teste de memória**
```
> qual minha pergunta anterior?
```

## ❌ **Resultado Atual (Bug)**
```
Você não fez nenhuma pergunta anterior nesta conversa. Esta é sua primeira mensagem.
```

## ✅ **Resultado Esperado**
```
Sua pergunta anterior foi: "qual sua funcao?"
```

## 🔍 **Verificação Adicional**

### **Verificar estado do agente antes**
```bash
cat projects/develop/agents/ProblemRefiner_Agent/state.json
```
**Resultado**: `conversation_history: []`

### **Verificar estado do agente depois**
```bash
cat projects/develop/agents/ProblemRefiner_Agent/state.json
```
**Resultado**: `conversation_history: []` (inalterado)

## 📊 **Frequência do Bug**
- **Reproduzibilidade**: 100%
- **Plataforma**: Todas (testado em Linux)
- **Agentes afetados**: Todos (problema no framework base)

## ⚠️ **Impacto Observado**
- Impossibilidade de manter contexto conversacional
- Agentes "esquecem" informações mencionadas anteriormente
- Experiência de usuário degradada no modo interativo