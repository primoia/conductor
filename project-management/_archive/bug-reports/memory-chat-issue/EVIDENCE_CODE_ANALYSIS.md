# 🔍 Evidências Técnicas - Chat Memory Amnesia Bug

## 🧩 **Problema 1: Memória nunca é persistida**

### Localização: `scripts/genesis_agent.py:2034`
```python
def __init__(self, working_directory: str = None):
    self.working_directory = working_directory or os.getcwd()
    self.conversation_history = []  # ❌ Apenas em memória RAM
```

### Evidência:
- `conversation_history` existe apenas na instância da classe
- **Nunca é salvo** no arquivo `state.json` do agente
- **Perdido** quando a aplicação termina

---

## 🧩 **Problema 2: Estado do agente não é carregado**

### Configuração esperada: `projects/develop/agents/ProblemRefiner_Agent/agent.yaml:13-14`
```yaml
# Caminho para o arquivo de estado (memória) do agente
state_file_path: "state.json"
```

### Estado atual: `projects/develop/agents/ProblemRefiner_Agent/state.json:6`
```json
{
  "conversation_history": [],  // ❌ Array vazio - nunca preenchido
  "files_analyzed": [],
  "last_updated": "2025-08-15T12:00:00Z"
}
```

### Evidência:
- Arquivo `state.json` **existe** mas **nunca é lido**
- `conversation_history` permanece vazio
- Não há código para carregar estado na inicialização

---

## 🧩 **Problema 3: Contexto não enviado ao Claude CLI**

### Localização: `scripts/genesis_agent.py:2278`
```python
def chat(self, message: str) -> str:
    try:
        response = self.llm_client._invoke_subprocess(message)  # ❌ Só a mensagem atual
        return response or "No response from agent."
```

### Localização: `scripts/genesis_agent.py:2084`
```python
def _invoke_subprocess(self, prompt: str) -> Optional[str]:
    cmd = [self.claude_command, "--print", prompt]  # ❌ Sem histórico
```

### Evidência:
- Cada mensagem é **independente**
- **Sem contexto** das mensagens anteriores
- Claude CLI recebe apenas a mensagem atual

---

## 🧩 **Problema 4: REPL ignora sistema de estado**

### Localização: `scripts/genesis_agent.py:2314-2320`
```python
while True:
    try:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break
        response = agent.chat(user_input)  # ❌ Não salva no estado
        print(response)
```

### Evidência:
- Loop REPL **não persiste** conversas
- **Não chama** funções de save/load do estado
- Memória existe apenas durante a execução

---

## 📊 **Fluxo Atual vs Esperado**

### ❌ **Fluxo Atual (Bugado)**
```
Início → Cria conversation_history=[] em RAM
Msg 1 → Claude CLI (sem contexto) → Resposta
Msg 2 → Claude CLI (sem contexto) → Resposta  
Fim → conversation_history perdido
```

### ✅ **Fluxo Esperado**
```
Início → Carrega state.json → conversation_history preenchido
Msg 1 → Claude CLI + histórico → Resposta → Salva state.json
Msg 2 → Claude CLI + histórico completo → Resposta → Atualiza state.json
Fim → Estado persistido
```