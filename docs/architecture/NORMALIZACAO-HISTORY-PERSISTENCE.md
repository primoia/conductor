# Normalização da Persistência de History

## 📋 Resumo

Normalização dos dois fluxos de execução (REPL CLI e API MongoDB Queue) para que **ambos salvem no history global do agente**, garantindo consistência e reuso de código.

## 🎯 Problema Identificado

### Antes da Normalização

Existiam dois fluxos distintos com comportamentos diferentes:

| Fluxo | Salva no History Global? | Onde salva? |
|-------|-------------------------|-------------|
| **REPL CLI** (`./conductor.py --repl`) | ✅ Sim, sempre | `history.json` ou `agent_history` collection |
| **API MongoDB Queue** (sem `instance_id`) | ❌ **NÃO** | Lugar nenhum |
| **API MongoDB Queue** (com `instance_id`) | ❌ Não no global | Apenas `agent_conversations` collection |

### Impacto

- **Inconsistência**: Execuções via API não apareciam no histórico global do agente
- **Perda de contexto**: Próximas execuções não tinham acesso ao histórico de execuções anteriores via API
- **Duplicação de código**: Lógica de persistência duplicada em múltiplos lugares

## ✅ Solução Implementada

### Mudanças no `src/api/routes/conductor_cli.py`

Adicionada persistência no history global após execução via MongoDB queue (linhas 286-321):

```python
# 🔥 NORMALIZAÇÃO: Salvar no history GLOBAL do agente (mesmo fluxo que REPL)
if assistant_response:
    logger.info(f"Saving to global agent history for agent: {agent_id}")
    try:
        # Criar HistoryEntry (mesma estrutura que TaskExecutionService usa)
        history_entry = HistoryEntry(
            _id=str(uuid.uuid4()),
            agent_id=agent_id,
            task_id=result_document.get("task_id", str(uuid.uuid4())),
            status="completed" if result_document.get("status") == "success" else "error",
            summary=assistant_response[:200] + '...' if len(assistant_response) > 200 else assistant_response,
            git_commit_hash=""
        )

        # Obter storage service do container
        storage_service = container.get_storage_service()
        storage = storage_service.get_storage()

        # Salvar no history global (MESMA função que TaskExecutionService usa)
        storage.append_to_history(
            agent_id=agent_id,
            entry=history_entry,
            user_input=user_input,
            ai_response=assistant_response,
            instance_id=request.instance_id
        )
    except Exception as e:
        logger.error(f"❌ Error saving to global history: {e}", exc_info=True)
```

### Comportamento Após Normalização

| Fluxo | Salva no History Global? | Onde salva? |
|-------|-------------------------|-------------|
| **REPL CLI** | ✅ Sim | `history.json` ou `agent_history` collection |
| **API MongoDB Queue** (sem `instance_id`) | ✅ **SIM** | `history.json` ou `agent_history` collection |
| **API MongoDB Queue** (com `instance_id`) | ✅ **SIM** | **AMBOS**: history global + `agent_conversations` |

### Reuso de Código

- ✅ **Mesma interface**: `storage.append_to_history()`
- ✅ **Mesma estrutura de dados**: `HistoryEntry`
- ✅ **Mesmo comportamento**: Salvamento completo (user_input + ai_response)
- ✅ **Zero duplicação**: Infraestrutura compartilhada

## 📊 Fluxo Normalizado

### Fluxo REPL (CLI)
```
User → conductor.py --repl
     → ConductorCLI.chat()
     → ConductorService.execute_task()
     → TaskExecutionService.execute_task()
     → AgentExecutor.run()
     → Claude API
     → TaskExecutionService._persist_task_result()
     → storage.append_to_history() ✅
```

### Fluxo API (MongoDB Queue)
```
User → API /conductor/execute
     → _execute_agent_container_mongodb()
     → MongoTaskClient.submit_task()
     → MongoDB Queue → poc/watch process → Claude API
     → Obter resultado
     → storage.append_to_history() ✅ (NOVO!)
     → [Se instance_id] ConversationService.append_to_conversation() (adicional)
```

## 🧪 Testes

### Teste de Normalização

Criado `tests/api/test_history_persistence.py` que valida:

1. ✅ REPL salva no history global
2. ✅ API sem instance_id salva no history global
3. ✅ API com instance_id salva em AMBOS os locais

### Resultado dos Testes

```bash
$ pytest tests/api/test_history_persistence.py -v
# ✅ 1 passed

$ pytest tests/core/services/test_task_execution_service.py -v
# ✅ 8 passed (nenhum teste quebrado)
```

## 🎁 Benefícios

1. **Consistência**: Ambos os fluxos se comportam da mesma forma
2. **Contexto preservado**: Próximas execuções têm acesso ao histórico completo
3. **Manutenibilidade**: Uma única função de persistência para manter
4. **Rastreabilidade**: Todas as execuções ficam registradas no history global
5. **Compatibilidade**: Mantém comportamento adicional de `agent_conversations` quando necessário

## 🔍 Arquivos Modificados

1. `src/api/routes/conductor_cli.py` - Adicionada persistência no history global
2. `tests/api/test_history_persistence.py` - Novo teste de normalização

## 📝 Notas de Implementação

- A persistência no history global é **não-bloqueante**: Se falhar, não quebra a request
- Quando `instance_id` é fornecido, salva em **dois lugares** (compatibilidade com SAGA-003)
- Usa a **mesma infraestrutura** que TaskExecutionService (`storage.append_to_history()`)
- Formato do `HistoryEntry` é **idêntico** ao usado pelo REPL

## 🚀 Próximos Passos (Sugestões)

1. Considerar unificar completamente os dois fluxos usando `ConductorService.execute_task()`
2. Avaliar se `agent_conversations` ainda é necessário ou pode ser substituído por filtros no history global
3. Adicionar testes de integração end-to-end verificando o history após execução via API

---

**Data**: 2025-10-10
**Autor**: Claude Code Assistant
**Categoria**: Architecture Improvement
