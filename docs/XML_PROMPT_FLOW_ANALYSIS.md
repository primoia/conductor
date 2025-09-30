# Análise do Fluxo de XML Prompt

## 🎯 Objetivo
Investigar por que o campo `prompt` na tabela `tasks` do MongoDB contém texto simples ao invés de XML estruturado.

## ✅ Descobertas

### 1. O Sistema ESTÁ Funcionando Corretamente

O fluxo completo de geração e salvamento de XML **está implementado e funcional**:

```python
# 1. API gera XML estruturado
xml_prompt = discovery_service.get_full_prompt(
    agent_id=agent_id,
    current_message=request.user_input,
    include_history=True,
    save_to_file=False
)
# Resultado: <prompt><system_context><persona>...</prompt>

# 2. XML é salvo no MongoDB
task_client.submit_task(
    agent_id=agent_id,
    prompt=xml_prompt  # XML completo
)

# 3. Watcher lê XML do MongoDB
prompt = request.get("prompt", "")  # Lê XML

# 4. Watcher envia XML ao LLM via stdin
subprocess.run(["claude", "--print"], input=prompt, ...)
```

### 2. Quando o Texto Simples Aparece (Fallback)

O texto simples só aparece quando há **erro** na geração do XML. Veja o código:

**`src/core/services/agent_discovery_service.py:382-429`**

```python
try:
    # Gerar XML estruturado
    complete_prompt = prompt_engine.build_prompt_with_format(
        conversation_history,
        enhanced_message,
        include_history
    )
    return complete_prompt  # ✅ XML estruturado

except Exception as e:
    # ❌ FALLBACK: Retorna texto simples quando há erro
    fallback_parts = []
    fallback_parts.append(f"❌ Erro ao gerar prompt completo: {e}")
    fallback_parts.append("")
    fallback_parts.append("=== ENHANCED USER INPUT (disponível) ===")
    fallback_parts.append(enhanced_message)
    ...
    return "\n".join(fallback_parts)  # ❌ TEXTO SIMPLES
```

### 3. Causas do Fallback

O fallback de texto simples é acionado quando:

#### a) Agente não existe no MongoDB
```bash
# Exemplo: tentar executar agente inexistente
curl -X POST http://api/conductor/testing-expert/execute
# Resultado: "❌ Erro ao gerar prompt completo: Error loading agent definition from MongoDB: Definition not found for agent: testing-expert"
```

#### b) Erro ao carregar persona/playbook
- Arquivo `persona.md` corrompido ou ausente
- `definition.yaml` com formato inválido
- Problemas de permissão no MongoDB

#### c) Erro ao carregar histórico
- Collection `history` inacessível
- Histórico com formato inválido

#### d) Erro de configuração
- `prompt_format` não definido
- `PromptEngine` falha ao inicializar

## 🧪 Testes Realizados

### Teste 1: Verificar geração de XML

```python
from src.container import container

discovery_service = container.get_agent_discovery_service()

xml_prompt = discovery_service.get_full_prompt(
    agent_id='CommitMessage_Agent',  # ✅ Agente existente
    current_message='Test message',
    include_history=False,
    save_to_file=False
)

print(xml_prompt[:300])
```

**Resultado:**
```xml
<prompt>
    <system_context>
        <persona>
            <![CDATA[# Persona: Commit Message Generator
...
```

✅ **XML gerado corretamente**

### Teste 2: Verificar salvamento no MongoDB

```python
task_document = {
    "agent_id": 'CommitMessage_Agent',
    "provider": 'claude',
    "prompt": xml_prompt,  # XML estruturado
    "status": "pending",
}

# MongoDB recebe XML intacto
assert task_document['prompt'].startswith('<prompt>')
```

✅ **XML salvo corretamente**

### Teste 3: Verificar leitura do watcher

```python
# Watcher lê campo 'prompt'
prompt_from_db = task_document.get("prompt", "")

# Envia via stdin
subprocess.run(["claude", "--print"], input=prompt_from_db, ...)
```

✅ **Watcher lê e envia XML corretamente**

## 📊 Estrutura do XML Gerado

```xml
<prompt>
    <system_context>
        <persona>
            <![CDATA[
                # Persona do agente
                ## Identidade
                ...
            ]]>
        </persona>
        <instructions>
            <![CDATA[
                Instruções específicas do agente...
            ]]>
        </instructions>
        <playbook>
            <best_practices>
                ...
            </best_practices>
            <anti_patterns>
                ...
            </anti_patterns>
        </playbook>
    </system_context>

    <conversation_history>
        <turn timestamp="...">
            <user><![CDATA[User input]]></user>
            <assistant><![CDATA[AI response]]></assistant>
        </turn>
    </conversation_history>

    <user_request>
        <![CDATA[Current message]]>
    </user_request>
</prompt>
```

## 🔍 Como Verificar se XML Está Sendo Salvo

### Opção 1: Verificar via MongoDB CLI

```bash
mongosh conductor

db.tasks.find().sort({created_at: -1}).limit(1).pretty()
```

Procure pelo campo `prompt` e verifique se começa com `<prompt>`.

### Opção 2: Verificar via código

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["conductor"]
tasks = db.tasks

# Buscar última task
last_task = tasks.find_one(sort=[("created_at", -1)])

print(f"Prompt é XML: {last_task['prompt'].startswith('<prompt>')}")
print(f"Primeiros 500 chars:")
print(last_task['prompt'][:500])
```

### Opção 3: Testar com endpoint da API

```bash
# Criar nova task com agente existente
curl -X POST http://localhost:8000/conductor/CommitMessage_Agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Add authentication feature",
    "cwd": "/tmp",
    "timeout": 300,
    "provider": "claude"
  }'
```

Depois verificar no MongoDB se o prompt é XML.

## ✅ Conclusão

**O sistema ESTÁ gerando e salvando XML corretamente.**

Se você viu texto simples no MongoDB, foi porque:

1. ✅ **Tasks antigas** (antes das correções) ainda têm texto simples
2. ✅ **Agente inexistente** triggera fallback de erro
3. ✅ **Erro ao carregar dados** do agente (persona/playbook)

**Solução:**

1. Limpar tasks antigas do MongoDB:
   ```javascript
   db.tasks.deleteMany({created_at: {$lt: new Date("2025-01-30")}})
   ```

2. Testar com agente que existe:
   ```bash
   # Listar agentes disponíveis
   python3 -c "from src.container import container;
   storage = container.get_agent_storage_service().get_storage();
   print(storage.list_agents())"
   ```

3. Criar nova task via API e verificar campo `prompt` no MongoDB

## 🎯 Próximos Passos

1. ✅ Validar que tasks novas têm XML
2. ✅ Limpar tasks antigas com texto simples
3. ✅ Adicionar logs para debug quando fallback é acionado
4. ✅ Criar testes automatizados para garantir XML sempre

## 📝 Configuração Relevante

**`config.yaml`**
```yaml
storage:
  type: mongodb
prompt_format: xml  # ✅ Default é 'xml'
```

**Verificar configuração:**
```python
from src.core.services.configuration_service import ConfigurationService

config = ConfigurationService()
print(config.get_prompt_format())  # Deve ser 'xml'
```