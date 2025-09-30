# 🔍 Debug do Fluxo XML → MongoDB

## 🎯 Problema Reportado
O XML não está sendo salvo corretamente no MongoDB - aparece texto simples.

## 📊 Rastreamento Completo do Fluxo

### Passo 1: API recebe request
```
POST /conductor/{agent_id}/execute
Body: {
  "user_input": "mensagem do usuário",
  "cwd": "/path",
  "timeout": 300,
  "provider": "claude"
}
```

**Arquivo:** `src/api/routes/agents.py:117-158`

### Passo 2: API chama discovery_service.get_full_prompt()
```python
# Linha 134-141
xml_prompt = discovery_service.get_full_prompt(
    agent_id=agent_id,
    current_message=request.user_input,
    meta=False,
    new_agent_id=None,
    include_history=True,
    save_to_file=False
)
```

**Arquivo:** `src/core/services/agent_discovery_service.py:288-429`

**🔥 PONTO CRÍTICO 1:** Aqui o método pode retornar:
- ✅ XML estruturado (se tudo OK)
- ❌ Texto de fallback (se houver erro)

```python
# Linha 309-380: Caminho feliz
try:
    # Carrega PromptEngine
    prompt_engine = PromptEngine(agent_home_path, prompt_format)
    prompt_engine.load_context()

    # Carrega histórico
    conversation_history = self.get_conversation_history(agent_id)

    # GERA XML
    complete_prompt = prompt_engine.build_prompt_with_format(
        conversation_history,
        enhanced_message,
        include_history
    )

    return complete_prompt  # ✅ XML estruturado

# Linha 382-429: Caminho de erro
except Exception as e:
    # ❌ FALLBACK: Retorna texto simples
    fallback_parts = []
    fallback_parts.append(f"❌ Erro ao gerar prompt completo: {e}")
    fallback_parts.append("")
    fallback_parts.append("=== ENHANCED USER INPUT (disponível) ===")
    fallback_parts.append(enhanced_message)
    ...
    return "\n".join(fallback_parts)  # ❌ TEXTO SIMPLES
```

**⚠️ POSSÍVEL CAUSA:** Se houver qualquer exceção aqui, retorna texto simples!

### Passo 3: PromptEngine.build_prompt_with_format()

**Arquivo:** `src/core/prompt_engine.py:130-138`

```python
def build_prompt_with_format(self, conversation_history, message, include_history):
    if self.prompt_format == "xml":
        return self.build_xml_prompt(...)  # ✅ Retorna XML
    else:
        return self.build_prompt(...)      # ❌ Retorna texto simples
```

**🔥 PONTO CRÍTICO 2:** O formato depende de `self.prompt_format`

**Verificar:**
```python
from src.core.services.configuration_service import ConfigurationService
config = ConfigurationService()
print(config.get_prompt_format())  # Deve ser 'xml'
```

### Passo 4: API passa para submit_task()

**Arquivo:** `src/api/routes/agents.py:144-150`

```python
task_id = task_client.submit_task(
    agent_id=agent_id,
    cwd=request.cwd,
    timeout=request.timeout,
    provider=request.provider,
    prompt=xml_prompt  # ← O que vier aqui será salvo
)
```

**⚠️ IMPORTANTE:** O `submit_task` **NÃO modifica** o prompt!

### Passo 5: MongoTaskClient.submit_task() salva no MongoDB

**Arquivo:** `src/core/services/mongo_task_client.py:29-62`

```python
def submit_task(self, agent_id, cwd, timeout, provider, prompt):
    task_document = {
        "agent_id": agent_id,
        "provider": provider,
        "prompt": prompt,  # ← Salvo EXATAMENTE como recebido
        "cwd": cwd,
        "timeout": timeout,
        "status": "pending",
        ...
    }
    result = self.collection.insert_one(task_document)
```

**✅ CONFIRMADO:** Não há transformação aqui!

### Passo 6: MongoDB armazena

MongoDB armazena strings **exatamente como recebidas**. Não há limitação ou conversão.

## 🔍 Checklist de Debug

### 1. Verificar se agente existe
```python
from src.container import container

storage = container.get_agent_storage_service().get_storage()
agents = storage.list_agents()
print("AgentCreator_Agent" in agents)  # Deve ser True
```

### 2. Verificar configuração do prompt_format
```python
from src.core.services.configuration_service import ConfigurationService

config = ConfigurationService()
print(f"Formato configurado: {config.get_prompt_format()}")  # Deve ser 'xml'
```

### 3. Testar geração de XML diretamente
```python
from src.container import container

discovery_service = container.get_agent_discovery_service()

xml = discovery_service.get_full_prompt(
    agent_id='CommitMessage_Agent',
    current_message='Test',
    include_history=False,
    save_to_file=False
)

print(f"Começa com <prompt>: {xml.strip().startswith('<prompt>')}")
print(f"Primeiros 200 chars:\n{xml[:200]}")
```

### 4. Verificar task no MongoDB
```bash
mongosh conductor

# Buscar última task
db.tasks.find().sort({created_at: -1}).limit(1).pretty()

# Verificar campo 'prompt'
# Deve começar com: "<prompt>"
# NÃO deve começar com: "❌ Erro"
```

### 5. Adicionar logs para debug

**Adicionar em `src/api/routes/agents.py` linha 141:**
```python
xml_prompt = discovery_service.get_full_prompt(...)

# 🔍 DEBUG: Verificar o que foi gerado
import logging
logger = logging.getLogger(__name__)
logger.info(f"🔍 XML gerado - Tipo: {'XML' if xml_prompt.startswith('<prompt>') else 'TEXTO'}")
logger.info(f"🔍 Primeiros 200 chars: {xml_prompt[:200]}")
```

**Adicionar em `src/core/services/mongo_task_client.py` linha 58:**
```python
task_document = {..., "prompt": prompt, ...}

# 🔍 DEBUG: Verificar o que será salvo
import logging
logger = logging.getLogger(__name__)
logger.info(f"🔍 Salvando no MongoDB - Tipo: {'XML' if prompt.startswith('<prompt>') else 'TEXTO'}")
logger.info(f"🔍 Tamanho: {len(prompt)} chars")
```

## 🎯 Possíveis Causas

### Causa 1: Agente não existe (99% provável)
```
Sintoma: Campo 'prompt' começa com "❌ Erro ao gerar prompt completo"
Solução: Usar agente que existe no MongoDB
```

### Causa 2: Erro ao carregar persona/playbook
```
Sintoma: Campo 'prompt' começa com "❌ Erro ao gerar prompt completo"
Causa: Arquivo corrompido ou ausente
Solução: Verificar integridade dos dados do agente
```

### Causa 3: prompt_format configurado como 'text'
```
Sintoma: Campo 'prompt' contém texto mas SEM tags XML
Solução: Verificar config.yaml tem prompt_format: xml
```

### Causa 4: Exceção silenciosa no PromptEngine
```
Sintoma: Fallback é acionado mas erro não é óbvio
Solução: Adicionar logs de debug conforme acima
```

## 🧪 Teste Definitivo

Execute este script para testar o fluxo completo:

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor')

from src.container import container

print("1. Listar agentes disponíveis...")
storage = container.get_agent_storage_service().get_storage()
agents = storage.list_agents()
print(f"   Total: {len(agents)} agentes")
print(f"   Exemplo: {agents[0] if agents else 'NENHUM!'}")

if not agents:
    print("❌ PROBLEMA: Nenhum agente no MongoDB!")
    sys.exit(1)

agent_to_test = agents[0]
print(f"\n2. Testando com agente: {agent_to_test}")

discovery_service = container.get_agent_discovery_service()

try:
    xml = discovery_service.get_full_prompt(
        agent_id=agent_to_test,
        current_message='Teste de geração de XML',
        include_history=False,
        save_to_file=False
    )

    print(f"\n3. XML gerado:")
    print(f"   Tipo: {'✅ XML' if xml.startswith('<prompt>') else '❌ TEXTO SIMPLES'}")
    print(f"   Tamanho: {len(xml)} chars")
    print(f"\n   Primeiros 300 chars:")
    print(f"   {xml[:300]}")

    if not xml.startswith('<prompt>'):
        print(f"\n❌ PROBLEMA ENCONTRADO: XML não foi gerado!")
        print(f"\nConteúdo completo:")
        print(xml)

except Exception as e:
    print(f"\n❌ ERRO ao gerar XML: {e}")
    import traceback
    traceback.print_exc()
```

## 📝 Próximos Passos

1. **Execute o teste definitivo acima**
2. **Verifique os logs** da API quando criar uma task
3. **Mostre-me o conteúdo** de uma task no MongoDB que você diz ter texto simples
4. **Confirme** qual agente está sendo usado

Com essas informações, posso identificar EXATAMENTE onde o XML está sendo perdido.