# Plano de Demo: Validação do Conceito Conductor

## 🎯 Objetivo do Demo

Validar os princípios fundamentais da arquitetura Conductor através de um cenário simples mas representativo, provando:

1. **Coordenação entre agentes** via eventos
2. **Persistência de estado** através de reinicializações
3. **Especialização de função** sem interferência mútua
4. **Orquestração humana** eficaz

## 📋 Cenário: Análise de Versões Gradle

### Contexto
- 2 microserviços com versões diferentes de Gradle
- Necessidade de identificar inconsistências
- Gerar relatório com recomendações

### Agentes Envolvidos
- **gradle-checker-x**: Especialista em microserviço X
- **gradle-checker-y**: Especialista em microserviço Y
- **documentation**: Analista e consolidador de dados

## 🚀 Execução Passo-a-Passo

### Preparação Inicial
```bash
cd /mnt/ramdisk/primoia-main/conductor/demo

# Verificar estrutura inicial
ls -la */
```

### Fase 1: Execução Primeira Onda

#### Passo 1.1: Trigger Agent X
```bash
echo "=== EXECUTANDO AGENT GRADLE CHECKER X ==="
echo "Comando:" && cat orchestrator/1-trigger.txt
echo "Input:" && cat agent-gradle-checker-x/1.txt
echo "Processing..."
echo "Output:" && cat agent-gradle-checker-x/2.txt
echo "Estado atualizado:" && cat agent-gradle-checker-x/state.json
```

#### Passo 1.2: Trigger Agent Y (Paralelo)
```bash
echo "=== EXECUTANDO AGENT GRADLE CHECKER Y ==="
echo "Comando:" && cat orchestrator/2-trigger.txt
echo "Input:" && cat agent-gradle-checker-y/1.txt
echo "Processing..."
echo "Output:" && cat agent-gradle-checker-y/2.txt
echo "Estado atualizado:" && cat agent-gradle-checker-y/state.json
```

#### Passo 1.3: Verificação de Estados
```bash
echo "=== VERIFICANDO ESTADOS PÓS-EXECUÇÃO ==="
echo "Agent X Status:" && jq '.current_status' agent-gradle-checker-x/state.json
echo "Agent Y Status:" && jq '.current_status' agent-gradle-checker-y/state.json
echo "Ambos devem estar 'idle' e com dados coletados"
```

### Fase 2: Teste de Persistência (CRÍTICO)

#### Passo 2.1: Simular "Desligamento"
```bash
echo "=== SIMULANDO DESLIGAMENTO DO SISTEMA ==="
echo "Sistema 'desligado' - estados salvos em arquivos"
echo "Aguardando 5 segundos para simular restart..."
sleep 5
```

#### Passo 2.2: Simular "Boot" e Verificação
```bash
echo "=== SISTEMA RELIGADO - VERIFICANDO RECUPERAÇÃO ==="
echo "Agent X lembra:" && jq '.state.last_version_found' agent-gradle-checker-x/state.json
echo "Agent Y lembra:" && jq '.state.last_version_found' agent-gradle-checker-y/state.json
echo "Timestamps preservados:"
echo "  Agent X:" && jq '.last_execution' agent-gradle-checker-x/state.json
echo "  Agent Y:" && jq '.last_execution' agent-gradle-checker-y/state.json
```

### Fase 3: Continuação da Orquestração

#### Passo 3.1: Trigger Documentation Agent
```bash
echo "=== EXECUTANDO AGENT DOCUMENTATION ==="
echo "Comando:" && cat orchestrator/3-trigger.txt
echo "Input:" && cat agent-documentation/1.txt
echo "Processing baseado nos dados coletados anteriormente..."
echo "Análise consolidada:" && cat agent-documentation/2.txt
```

#### Passo 3.2: Verificação Final
```bash
echo "=== VERIFICAÇÃO FINAL DO DEMO ==="
echo "Documentation Status:" && jq '.current_status' agent-documentation/state.json
echo "Inconsistências detectadas:" && jq '.state.inconsistencies_found' agent-documentation/state.json
echo "Serviços analisados:" && jq '.state.services_analyzed' agent-documentation/state.json
```

## ✅ Critérios de Sucesso

### 1. **Coordenação Efetiva**
- [ ] Agent X executou sua função específica
- [ ] Agent Y executou sua função específica  
- [ ] Documentation consolidou dados de ambos
- [ ] Nenhum agent interferiu com outro

### 2. **Persistência Validada**
- [ ] Estados foram mantidos após "restart"
- [ ] Agentes "lembraram" de execuções anteriores
- [ ] Timestamps e dados preservados corretamente
- [ ] Possível continuar execução de onde parou

### 3. **Especialização Confirmada**
- [ ] Cada agent processou apenas seus inputs específicos
- [ ] Outputs são consistentes com função definida
- [ ] Nenhum agent tentou executar função de outro

### 4. **Orquestração Humana**
- [ ] Humano controlou timing de execução
- [ ] Possível intervir em qualquer ponto
- [ ] Visibilidade completa de estado do sistema
- [ ] Capacidade de rollback/restart se necessário

## 🔍 Validações Específicas

### Teste 1: Detecção de Inconsistência
```bash
# Verificar se Documentation detectou versões diferentes
grep -i "inconsistency\|mismatch" agent-documentation/2.txt
# Deve retornar linha sobre diferença 7.5.1 vs 8.0
```

### Teste 2: Estado Independente
```bash
# Verificar que agentes não compartilham estado
diff agent-gradle-checker-x/state.json agent-gradle-checker-y/state.json
# Devem ter diferenças (different microservices, versions, timestamps)
```

### Teste 3: Rastreabilidade
```bash
# Verificar timestamps sequenciais
echo "Sequência temporal:"
jq '.last_execution' agent-gradle-checker-x/state.json
jq '.last_execution' agent-gradle-checker-y/state.json
jq '.last_execution' agent-documentation/state.json
# Documentation deve ser posterior aos checkers
```

## 🔄 Cenários de Teste Adicicionais

### Cenário A: Interrupção no Meio
1. Execute Agent X
2. PARE antes de executar Agent Y
3. Restart sistema
4. Continue com Agent Y e Documentation
5. **Resultado esperado**: Funciona normalmente

### Cenário B: Rollback
1. Execute sequência completa
2. "Desfaça" mudanças (simule reset de states)
3. Re-execute com dados diferentes
4. **Resultado esperado**: Novos resultados refletem novos inputs

### Cenário C: Agent Failure
1. Execute Agent X (sucesso)
2. Simule falha em Agent Y (modifique state para "error")
3. Execute Documentation
4. **Resultado esperado**: Documentation detecta dados incompletos

## 📊 Métricas de Sucesso

### Quantitativas
- **Tempo de execução**: < 2 minutos para sequência completa
- **Estados persistidos**: 100% dos dados preservados após restart
- **Acurácia**: 100% das inconsistências detectadas
- **Recuperação**: 0 segundos para restart (load de estados)

### Qualitativas
- **Clareza**: Fácil entender o que cada agent está fazendo
- **Controle**: Humano mantém controle total do processo
- **Debugging**: Fácil identificar problemas e states
- **Extensibilidade**: Óbvio como adicionar novos agents

## 🎯 Próximos Passos Após Demo

### Se Demo for Bem-Sucedido
1. **Automatizar execução** com script bash
2. **Adicionar 3º microserviço** (test scaling)
3. **Implementar Redis** para eventos reais
4. **Containerizar agents** com Docker

### Se Demo Revelar Problemas
1. **Simplificar ainda mais** o cenário
2. **Refinar model de estados**
3. **Melhorar documentação** de agents
4. **Revisar coordenação** entre agents

## 📝 Template de Execução

```bash
#!/bin/bash
# demo-runner.sh

echo "🎯 CONDUCTOR DEMO - GRADLE VERSION ANALYSIS"
echo "==========================================="

# Fase 1: Coleta Paralela
echo "📍 FASE 1: Coleta de Dados"
./run-agent.sh gradle-checker-x "check gradle version microservice-x"
./run-agent.sh gradle-checker-y "check gradle version microservice-y"

# Teste de Persistência
echo "📍 TESTE DE PERSISTÊNCIA"
echo "Sistema desligando..."
sleep 2
echo "Sistema religando..."
./verify-states.sh

# Fase 2: Consolidação
echo "📍 FASE 2: Análise e Documentação"
./run-agent.sh documentation "document gradle status for microservice-x and microservice-y"

# Validação Final
echo "📍 VALIDAÇÃO FINAL"
./validate-demo.sh

echo "✅ Demo concluído!"
```

---

**Este demo é o foundation stone do projeto Conductor. Sucesso aqui valida toda a arquitetura conceitual.**