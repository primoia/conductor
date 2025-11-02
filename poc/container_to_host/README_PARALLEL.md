# Claude Mongo Watcher - Versão Paralelizada 🚀

## 📋 Visão Geral

O `claude-mongo-watcher.py` agora suporta **execução paralela de múltiplas tasks simultaneamente**, aumentando significativamente o throughput do sistema.

### Melhorias Implementadas

✅ **ThreadPoolExecutor**: Processamento paralelo com threads
✅ **Controle FIFO Configurável**: 3 modos diferentes de ordenação
✅ **Graceful Shutdown**: Finalização segura com SIGTERM/SIGINT
✅ **Métricas Detalhadas**: Acompanhamento de performance em tempo real
✅ **Logging Thread-Safe**: Identificação clara de cada thread nos logs
✅ **Proteção Atômica MongoDB**: Garante que apenas um worker processe cada task

---

## 🚀 Como Usar

### Modo Simples (Padrões Recomendados)

```bash
# 5 workers, FIFO por agente (recomendado)
python3 claude-mongo-watcher.py
```

### Configuração Customizada

```bash
python3 claude-mongo-watcher.py \
  --max-workers 10 \
  --fifo-mode per_agent \
  --poll-interval 1.0 \
  --metrics-interval 60
```

### Parâmetros Disponíveis

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--max-workers` | `5` | Número máximo de tasks simultâneas |
| `--fifo-mode` | `per_agent` | Modo de ordenação (strict/per_agent/relaxed) |
| `--poll-interval` | `1.0` | Intervalo entre verificações (segundos) |
| `--metrics-interval` | `60` | Intervalo para imprimir métricas (segundos) |
| `--mongo-uri` | `mongodb://localhost:27017` | URI do MongoDB |
| `--database` | `conductor_state` | Nome do database |
| `--collection` | `tasks` | Nome da collection |
| `--gateway-url` | `http://localhost:5006` | URL do conductor-gateway |

---

## 🎯 Modos FIFO

### `per_agent` (⭐ RECOMENDADO)

**Comportamento**: Mantém FIFO **apenas para tasks do mesmo agente**. Agentes diferentes podem processar em paralelo.

**Vantagens**:
- ✅ Preserva ordem de execução por agente
- ✅ Maximiza paralelização entre agentes
- ✅ Ideal para múltiplos agentes independentes

**Exemplo**:
```
Agent A: Task1 → Task2 → Task3 (sequencial)
Agent B: Task1 → Task2 (sequencial)
Agent C: Task1 (paralelo com A e B)

Resultado: Até 3 tasks simultâneas (uma de cada agente)
```

### `relaxed`

**Comportamento**: Sem restrição FIFO. Processa qualquer task pendente.

**Vantagens**:
- ✅ Máxima paralelização
- ✅ Melhor aproveitamento de workers

**Desvantagens**:
- ⚠️ Ordem de execução não garantida

**Exemplo**:
```
5 tasks pendentes de qualquer agente → Processa 5 simultaneamente
```

### `strict`

**Comportamento**: Apenas **uma task por vez** em todo o sistema (modo legado).

**Vantagens**:
- ✅ Ordem FIFO estrita
- ✅ Comportamento idêntico à versão anterior

**Desvantagens**:
- ❌ Sem paralelização
- ❌ Throughput baixo

**Exemplo**:
```
Task1 → Task2 → Task3 (sempre sequencial, independente do agente)
```

---

## 📊 Métricas de Paralelização

O watcher imprime métricas automaticamente a cada `--metrics-interval` segundos:

```
================================================================================
📊 MÉTRICAS DE PARALELIZAÇÃO
================================================================================
   Total de tasks processadas: 42
   Total de tasks com erro: 2
   Taxa de sucesso: 95.2%
   Tempo total de execução: 1234.56s
   Tempo médio por task: 29.39s
   Tasks concorrentes agora: 3
   Pico de tasks simultâneas: 5
   Tasks por agente: {'agent-1': 20, 'agent-2': 15, 'agent-3': 7}
   Erros por agente: {'agent-2': 2}
================================================================================
```

**Métricas Disponíveis**:
- **total_tasks_processed**: Total de tasks processadas desde o início
- **total_tasks_failed**: Total de tasks que falharam
- **success_rate**: Taxa de sucesso em porcentagem
- **total_execution_time**: Tempo total acumulado (soma de todas as durações)
- **average_execution_time**: Tempo médio por task
- **concurrent_tasks_count**: Número de tasks sendo processadas agora
- **max_concurrent_tasks**: Pico de tasks simultâneas atingido
- **tasks_by_agent**: Distribuição de tasks por agente
- **errors_by_agent**: Distribuição de erros por agente

---

## 🛡️ Graceful Shutdown

O watcher responde corretamente a sinais de shutdown:

```bash
# Shutdown manual (Ctrl+C)
^C

# Shutdown via SIGTERM (Docker, systemd, etc)
kill -TERM <pid>
```

**Comportamento**:
1. ✅ Interrompe o loop de busca de novas tasks
2. ✅ Aguarda tasks em execução finalizarem (timeout: 30s por task)
3. ✅ Finaliza ThreadPoolExecutor corretamente
4. ✅ Fecha conexão MongoDB
5. ✅ Imprime métricas finais

**Log de Exemplo**:
```
🛑 Sinal 15 recebido. Iniciando graceful shutdown...
================================================================================
🛑 INICIANDO GRACEFUL SHUTDOWN
================================================================================
⏳ Aguardando 3 tasks em execução...
🔄 Finalizando ThreadPoolExecutor...
🔌 Fechando conexão MongoDB...
📊 MÉTRICAS FINAIS:
[métricas aqui]
👋 Universal Task Watcher finalizado com sucesso
```

---

## 🔧 Configurações Recomendadas

### Cenário 1: Poucos Agentes (1-3)
```bash
--max-workers 3 --fifo-mode per_agent
```
**Razão**: Evita sobrecarga com poucos agentes.

### Cenário 2: Múltiplos Agentes (5-10)
```bash
--max-workers 5 --fifo-mode per_agent
```
**Razão**: Equilíbrio entre paralelização e consumo de recursos.

### Cenário 3: Alta Concorrência (10+)
```bash
--max-workers 10 --fifo-mode per_agent
```
**Razão**: Maximiza throughput para muitos agentes.

### Cenário 4: Desenvolvimento/Debug
```bash
--max-workers 1 --fifo-mode strict --metrics-interval 10
```
**Razão**: Comportamento sequencial com métricas frequentes.

### Cenário 5: Máxima Performance
```bash
--max-workers 20 --fifo-mode relaxed --poll-interval 0.5
```
**Razão**: Processamento agressivo sem restrições FIFO.

---

## ⚡ Ganhos de Performance Esperados

| Cenário | Modo Legado | Modo Paralelo (5 workers) | Ganho |
|---------|-------------|---------------------------|-------|
| 1 agente, 10 tasks | 300s | 300s | **1x** (sem ganho) |
| 3 agentes, 30 tasks | 900s | 180s | **5x** |
| 5 agentes, 50 tasks | 1500s | 300s | **5x** |
| 10 agentes, 100 tasks | 3000s | 600s | **5x** |

**Premissas**:
- Tempo médio por task: 30s
- `--fifo-mode per_agent`
- `--max-workers 5`

**Observações**:
- ✅ Ganho linear até `max_workers`
- ✅ Ganho maior quando há múltiplos agentes
- ⚠️ Sem ganho para agentes únicos (FIFO por agente)
- 💡 Use `--fifo-mode relaxed` para ganho com agente único

---

## 🔍 Logs Thread-Safe

Todos os logs agora incluem o nome da thread:

```
🚀 [TaskWorker-1] Iniciando processamento da task do agente agent-1
📨 [TaskWorker-1] PROCESSANDO NOVA TASK
   ID: 507f1f77bcf86cd799439011
   Agent ID: agent-1
...
✅ [TaskWorker-1] TASK COMPLETADA E SALVA NO MONGODB
🏁 [TaskWorker-1] Finalizou processamento do agente agent-1
```

**Benefícios**:
- ✅ Rastreamento fácil de tasks concorrentes
- ✅ Debug simplificado de problemas paralelos
- ✅ Identificação clara de qual worker executou cada ação

---

## 🚨 Proteção Contra Race Conditions

### MongoDB - Proteção Atômica

O método `mark_as_processing()` usa `update_one` com filtro atômico:

```python
result = self.collection.update_one(
    {"_id": request_id, "status": "pending"},  # ✅ Garante que só atualiza se pending
    {"$set": {"status": "processing", "started_at": datetime.now(timezone.utc)}}
)
return result.modified_count > 0  # ✅ Retorna False se já estava processing
```

**Garantias**:
- ✅ Apenas **um worker** conseguirá marcar cada task como `processing`
- ✅ Workers concorrentes receberão `False` e não processarão a task
- ✅ Não há necessidade de locks externos

### Controle de Agentes - Locks em Memória

O controle FIFO por agente usa `threading.Lock`:

```python
with self.processing_agents_lock:
    return agent_id not in self.processing_agents
```

**Garantias**:
- ✅ Thread-safe para verificações de agentes processando
- ✅ Evita race conditions no modo `per_agent`

---

## 🐛 Troubleshooting

### Problema: Tasks não estão sendo processadas em paralelo

**Possíveis causas**:
1. `--fifo-mode strict` está ativo
2. Todas as tasks são do mesmo agente e `--fifo-mode per_agent` está ativo
3. `--max-workers 1`

**Solução**:
```bash
# Verificar modo FIFO
grep "Modo FIFO:" /tmp/claude-mongo-watcher.log

# Usar modo relaxed se necessário
python3 claude-mongo-watcher.py --fifo-mode relaxed --max-workers 5
```

### Problema: "Máximo de X workers atingido, aguardando..."

**Causa**: Mais tasks pendentes do que workers disponíveis.

**Solução**:
```bash
# Aumentar max-workers
python3 claude-mongo-watcher.py --max-workers 10
```

### Problema: Métricas mostram taxa de sucesso baixa

**Causa**: Muitos erros nas tasks.

**Ação**:
```bash
# Ver logs detalhados
tail -f /tmp/claude-mongo-watcher.log | grep "❌"

# Verificar erros por agente nas métricas
```

### Problema: Shutdown demorado

**Causa**: Tasks longas ainda em execução.

**Solução**:
```bash
# Aguardar graceful shutdown (até 30s por task)
# OU forçar kill (não recomendado):
kill -9 <pid>
```

---

## 🔄 Migração da Versão Anterior

A versão paralelizada é **100% retrocompatível**:

```bash
# Comportamento idêntico à versão anterior
python3 claude-mongo-watcher.py --max-workers 1 --fifo-mode strict
```

**Mudanças**:
- ✅ Todos os argumentos anteriores ainda funcionam
- ✅ Novos argumentos são opcionais (padrões inteligentes)
- ✅ Logs compatíveis (apenas adiciona nome da thread)
- ✅ API do MongoDB inalterada

---

## 📈 Roadmap Futuro

### Fase 3 (Opcional): Asyncio
- Substituir ThreadPoolExecutor por asyncio
- Melhor para I/O-bound workloads
- Menor overhead de memória

### Fase 4 (Opcional): Multiprocessing
- Usar multiprocessing.Pool para CPU-bound tasks
- Bypass do GIL do Python
- Maior throughput para tarefas intensivas

---

## 📝 Exemplos de Uso

### 1. Desenvolvimento Local (Debug)
```bash
python3 claude-mongo-watcher.py \
  --max-workers 1 \
  --fifo-mode strict \
  --poll-interval 2.0 \
  --metrics-interval 10
```

### 2. Produção Padrão
```bash
python3 claude-mongo-watcher.py \
  --max-workers 5 \
  --fifo-mode per_agent \
  --gateway-url http://conductor-gateway:8080
```

### 3. Alta Performance
```bash
python3 claude-mongo-watcher.py \
  --max-workers 10 \
  --fifo-mode relaxed \
  --poll-interval 0.5 \
  --metrics-interval 30
```

### 4. Background com nohup
```bash
nohup python3 claude-mongo-watcher.py \
  --max-workers 5 \
  --fifo-mode per_agent \
  > /tmp/watcher.log 2>&1 &

echo $! > /tmp/watcher.pid  # Salvar PID
```

### 5. Via run-watcher.sh (atualizar script)
```bash
# Editar run-watcher.sh para incluir novos parâmetros
./run-watcher.sh --max-workers 5 --fifo-mode per_agent
```

---

## 🎓 Conceitos Técnicos

### Threading vs Asyncio vs Multiprocessing

| Aspecto | Threading (ATUAL) | Asyncio | Multiprocessing |
|---------|-------------------|---------|-----------------|
| **Paralelismo Real** | ❌ (GIL) | ❌ (GIL) | ✅ (bypass GIL) |
| **I/O-bound** | ✅ Bom | ✅ Ótimo | ⚠️ Overhead |
| **CPU-bound** | ❌ Ruim | ❌ Ruim | ✅ Ótimo |
| **Complexidade** | 🟢 Simples | 🟡 Média | 🔴 Alta |
| **Overhead** | 🟢 Baixo | 🟢 Muito Baixo | 🟡 Médio |

**Por que Threading?**
- ✅ CLIs são **I/O-bound** (aguardam subprocess)
- ✅ Simples de implementar e debugar
- ✅ Compatível com bibliotecas síncronas (pymongo, requests)
- ✅ Overhead baixo (threads compartilham memória)

---

## 📞 Suporte

Em caso de dúvidas ou problemas:

1. **Verificar logs**: `/tmp/claude-mongo-watcher.log`
2. **Ver métricas**: Aguardar próximo intervalo ou enviar SIGUSR1 (se implementado)
3. **Reportar issue**: Incluir logs, configuração e métricas

---

**Versão**: 2.0.0 (Paralelizada)
**Autor**: Primoia Community
**Data**: 2025-01-01
