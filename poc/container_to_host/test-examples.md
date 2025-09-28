# Claude MongoDB Integration - Exemplos de Teste

## 🚀 Como Usar

### 1. Setup Inicial
```bash
# Instalar dependências e configurar
./setup-mongo-claude.sh
```

### 2. Iniciar o Watcher (na sua sessão autenticada)
```bash
# Terminal 1: Inicie o watcher onde o Claude funciona
./claude-mongo-watcher.py

# Com parâmetros customizados:
./claude-mongo-watcher.py --mongo-uri mongodb://localhost:27017 --database conductor --collection claude_requests
```

### 3. Testar com o Cliente Python
```bash
# Terminal 2: Teste com demo
./claude-mongo-client.py --demo

# Ou teste interativo
./claude-mongo-client.py
```

## 🔧 Como o Conductor Usaria

### Exemplo 1: Inserir Request via Python
```python
from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017")
db = client.conductor
collection = db.claude_requests

# Criar request
request = {
    "command": ["claude", "-p", "Resuma o README.md em 3 frases"],
    "cwd": "/mnt/ramdisk/develop/nex-web-backend",
    "timeout": 180,
    "status": "pending",
    "created_at": datetime.now(timezone.utc)
}

result = collection.insert_one(request)
print(f"Request criado: {result.inserted_id}")

# Aguardar resultado (polling)
import time
while True:
    doc = collection.find_one({"_id": result.inserted_id})
    if doc["status"] in ["completed", "error"]:
        print(f"Status: {doc['status']}")
        print(f"Resultado: {doc.get('result', 'N/A')}")
        break
    time.sleep(0.5)
```

### Exemplo 2: Via MongoDB Shell (mongosh)
```javascript
// Conectar ao MongoDB
use conductor

// Inserir request
db.claude_requests.insertOne({
    command: ["claude", "-p", "Hello world"],
    cwd: "/tmp",
    timeout: 60,
    status: "pending",
    created_at: new Date()
})

// Verificar resultado
db.claude_requests.find({status: "completed"}).sort({created_at: -1}).limit(1)
```

### Exemplo 3: Via HTTP/REST (se tiver API)
```bash
# Se você criar uma API REST sobre o MongoDB
curl -X POST http://localhost:8080/claude/execute \
  -H "Content-Type: application/json" \
  -d '{
    "command": ["claude", "-p", "Conte até 5"],
    "cwd": "/tmp",
    "timeout": 60
  }'
```

## 📊 Estrutura do Documento

### Request (quando criado)
```json
{
  "_id": ObjectId("..."),
  "command": ["claude", "-p", "seu prompt aqui"],
  "cwd": "/path/to/working/directory",
  "timeout": 180,
  "status": "pending",
  "created_at": ISODate("...")
}
```

### Response (quando processado)
```json
{
  "_id": ObjectId("..."),
  "command": ["claude", "-p", "seu prompt aqui"],
  "cwd": "/path/to/working/directory",
  "timeout": 180,
  "status": "completed", // ou "error"
  "result": "Resposta do Claude aqui...",
  "exit_code": 0,
  "duration": 2.5,
  "created_at": ISODate("..."),
  "started_at": ISODate("..."),
  "completed_at": ISODate("...")
}
```

## 🎯 Casos de Uso no Conductor

### 1. Análise de Código
```python
request = {
    "command": ["claude", "-p", "Analise este arquivo Python e sugira melhorias"],
    "cwd": "/path/to/project",
    "status": "pending"
}
```

### 2. Geração de Documentação
```python
request = {
    "command": ["claude", "-p", "Gere documentação para esta API baseada no código"],
    "cwd": "/path/to/api/project",
    "status": "pending"
}
```

### 3. Code Review
```python
request = {
    "command": ["claude", "-p", "Revise as mudanças no último commit"],
    "cwd": "/path/to/git/repo",
    "status": "pending"
}
```

## 🔍 Monitoramento

### Ver requests pendentes
```bash
mongosh conductor --eval "db.claude_requests.find({status: 'pending'})"
```

### Ver últimos resultados
```bash
mongosh conductor --eval "db.claude_requests.find({status: 'completed'}).sort({completed_at: -1}).limit(5)"
```

### Limpar requests antigos
```bash
mongosh conductor --eval "db.claude_requests.deleteMany({created_at: {\$lt: new Date(Date.now() - 24*60*60*1000)}})"
```

## ⚡ Vantagens desta Abordagem

1. **Desacoplamento**: Conductor e Claude executam em processos separados
2. **Persistência**: Requests são salvos, resistem a crashes
3. **Escalabilidade**: Múltiplos workers podem processar requests
4. **Auditoria**: Histórico completo de todas as interações
5. **Retry**: Fácil reprocessar requests que falharam
6. **Monitoring**: Queries SQL-like para análise
7. **Change Streams**: Notificações em tempo real (opcional)

## 🚨 Importante

- O watcher deve rodar na sua sessão onde o Claude está autenticado
- O Conductor pode rodar em qualquer lugar que tenha acesso ao MongoDB
- TTL index remove requests automaticamente após 24h
- Use índices apropriados para performance em produção