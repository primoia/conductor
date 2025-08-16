# 🧠 Sistema de Persistência de Memória de Chat

**Status**: 🎯 Planejada  
**Prioridade**: Crítica  
**Estimativa**: 1-2 dias  
**Relacionado**: [Bug Report](../bug-reports/memory-chat-issue/CHAT_MEMORY_AMNESIA_BUG.md)

## 📋 **Problema**
Chat memory não persiste entre sessões REPL. Agentes "esquecem" conversas anteriores, quebrando a experiência conversacional.

## 🎯 **Proposta**

### **Arquitetura**
```python
# Fluxo proposto
Genesis Agent → Carrega state.json → conversation_history preenchido
User message → Envia contexto + nova mensagem → Claude CLI
Claude response → Salva no conversation_history → Atualiza state.json
```

### **Estrutura de Memória**
```json
{
  "conversation_history": [
    {
      "timestamp": "2025-08-16T09:35:12Z",
      "role": "user", 
      "content": "ola",
      "session_id": "session_123"
    },
    {
      "timestamp": "2025-08-16T09:35:15Z",
      "role": "assistant",
      "content": "Hello! How can I help...",
      "session_id": "session_123"
    }
  ]
}
```

### **Context Window Management**
- Limite máximo de mensagens (ex: 50)
- Sliding window para conversas longas
- Compressão de contexto antigo
- Preservação de mensagens importantes

## 🔧 **Implementação**

### **Fase 1: State Loading**
1. Modificar `embody_agent()` para carregar `state.json`
2. Popular `conversation_history` na inicialização
3. Validar estrutura do estado

### **Fase 2: Context Injection**
1. Modificar `_invoke_subprocess()` para incluir contexto
2. Formatar histórico para Claude CLI
3. Implementar window management

### **Fase 3: State Persistence**
1. Salvar após cada interação
2. Implementar backup/recovery
3. Otimizar performance de I/O

## 📊 **Benefícios**
- ✅ Experiência conversacional contínua
- ✅ Agentes com contexto completo
- ✅ Sessões de debugging eficazes
- ✅ Análise iterativa de problemas

## ⚠️ **Considerações**
- **Performance**: I/O após cada mensagem
- **Storage**: Crescimento do state.json
- **Privacy**: Dados sensíveis em histórico
- **Concurrency**: Multiple sessions simultâneas