# 🧠 Chat Memory Persistence System

**Status**: 🎯 Planned  
**Priority**: Critical  
**Estimate**: 1-2 days  
**Related**: [Bug Report](../bug-reports/memory-chat-issue/CHAT_MEMORY_AMNESIA_BUG.md)

## 📋 **Problem**
Chat memory does not persist between REPL sessions. Agents "forget" previous conversations, breaking the conversational experience.

## 🎯 **Proposal**

### **Architecture**
```python
# Proposed flow
Genesis Agent → Loads state.json → conversation_history is populated
User message → Sends context + new message → Claude CLI
Claude response → Saves to conversation_history → Updates state.json
```

### **Memory Structure**
```json
{
  "conversation_history": [
    {
      "timestamp": "2025-08-16T09:35:12Z",
      "role": "user", 
      "content": "hello",
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
- Maximum message limit (e.g., 50)
- Sliding window for long conversations
- Compression of old context
- Preservation of important messages

## 🔧 **Implementation**

### **Phase 1: State Loading**
1. Modify `embody_agent()` to load `state.json`
2. Populate `conversation_history` on initialization
3. Validate state structure

### **Phase 2: Context Injection**
1. Modify `_invoke_subprocess()` to include context
2. Format history for Claude CLI
3. Implement window management

### **Phase 3: State Persistence**
1. Save after each interaction
2. Implement backup/recovery
3. Optimize I/O performance

## 📊 **Benefits**
- ✅ Continuous conversational experience
- ✅ Agents with full context
- ✅ Effective debugging sessions
- ✅ Iterative problem analysis

## ⚠️ **Considerations**
- **Performance**: I/O after each message
- **Storage**: Growth of state.json
- **Privacy**: Sensitive data in history
- **Concurrency**: Multiple simultaneous sessions