# Plano de Limpeza do Repositório Conductor

## 📊 Análise do Estado Atual

### ✅ **Arquivos Relevantes e Funcionais**
- `run_conductor.py` - **CORE** - Orquestrador principal funcional
- `focused_claude_orchestrator.py` - **CORE** - Referência para padrões
- `demo_integration.py` - **DEMO** - Demonstração completa
- `test_integration.py` - **TEST** - Teste da integração
- `INTEGRATION_PLAN.md` - **DOC** - Plano original
- `INTEGRATION_README.md` - **DOC** - Documentação de uso
- `INTEGRATION_SUMMARY.md` - **DOC** - Resumo da implementação
- `PLAN-A_CONDUCTOR_REFACTOR.md` - **DOC** - Plano de refatoração
- `PLAN-A_IMPLEMENTATION_SUMMARY.md` - **DOC** - Resumo da implementação

### 🗂️ **Estrutura .bmad-core (MANTIDA)**
- Agentes funcionais para metodologia
- Templates e workflows
- Configurações e checklists

### 🧪 **Scripts de Teste Antigos (CANDIDATOS À REMOÇÃO)**

#### **Scripts Obsoletos - REMOVER**
- `test_gemini_cli.py` - Testes antigos do Gemini CLI
- `test_gemini_working.py` - Testes antigos do Gemini
- `test_simple_claude.py` - Testes antigos do Claude
- `debug_executor.py` - Script de debug antigo
- `test_executor_only.py` - Teste antigo do executor

#### **Scripts de Orquestrador Antigos - AVALIAR**
- `orchestrator/gemini_mock_orchestrator.py` - Mock antigo
- `orchestrator/gemini_test_orchestrator.py` - Teste antigo
- `orchestrator/kotlin_test_orchestrator.py` - Orquestrador específico

### 📁 **Diretórios de Demo Antigos - AVALIAR**
- `demo/agent-documentation/` - Demos antigos
- `demo/agent-gradle-checker-x/` - Demos antigos
- `demo/agent-gradle-checker-y/` - Demos antigos
- `demo/agent-integration-user-auth/` - Demos antigos
- `demo/agent-test-payment-service/` - Demos antigos
- `demo/agent-test-user-service/` - Demos antigos

### 📁 **Agentes Antigos - AVALIAR**
- `projects/develop/agents/kotlin-test-creator-agent/` - Agente antigo
- `projects/develop/agents/unit-test-executor-agent/` - Agente antigo
- `projects/develop/agents/unit-test-strategy-agent/` - Agente antigo
- `projects/develop/agents/QuotationReceiptService_IntegrationTest_Agent/` - Agente específico

## 🎯 **Plano de Ação**

### **Fase 1: Remoção de Scripts Obsoletos**
```bash
# Scripts de teste antigos
rm test_gemini_cli.py
rm test_gemini_working.py
rm test_simple_claude.py
rm debug_executor.py
rm test_executor_only.py
```

### **Fase 2: Avaliação de Orquestradores Antigos**
```bash
# Verificar se são referenciados em algum lugar
# Se não, remover
rm -rf orchestrator/gemini_mock_orchestrator.py
rm -rf orchestrator/gemini_test_orchestrator.py
# Manter kotlin_test_orchestrator.py se for útil
```

### **Fase 3: Limpeza de Demos Antigos**
```bash
# Remover demos antigos não relacionados ao conductor
rm -rf demo/agent-documentation/
rm -rf demo/agent-gradle-checker-x/
rm -rf demo/agent-gradle-checker-y/
rm -rf demo/agent-integration-user-auth/
rm -rf demo/agent-test-payment-service/
rm -rf demo/agent-test-user-service/
# Manter demo/orchestrator/ se for relevante
```

### **Fase 4: Avaliação de Agentes Antigos**
```bash
# Verificar se são usados
# Se não, mover para archive/ ou remover
```

### **Fase 5: Limpeza de Documentação**
```bash
# Remover docs obsoletos
rm docs/cli-integration.md  # Se não for mais relevante
rm docs/demo-plan.md        # Se não for mais relevante
```

## 📋 **Estrutura Final Proposta**

```
conductor/
├── .bmad-core/                    # MANTIDO - Metodologia
├── config/                        # MANTIDO - Configurações
├── docs/                          # MANTIDO - Documentação relevante
├── examples/                      # MANTIDO - Exemplos úteis
├── projects/develop/
│   ├── agents/
│   │   ├── KotlinEntityCreator_Agent/      # MANTIDO - Funcional
│   │   ├── KotlinRepositoryCreator_Agent/  # MANTIDO - Funcional
│   │   └── [outros agentes relevantes]     # AVALIAR
│   └── workspace/
│       ├── example-implementation-plan.yaml # MANTIDO
│       └── implementation-plan-template.yaml # MANTIDO
├── src/                           # MANTIDO - Código gerado
├── stories/                       # MANTIDO - Histórias de exemplo
├── run_conductor.py               # MANTIDO - CORE
├── focused_claude_orchestrator.py # MANTIDO - Referência
├── demo_integration.py            # MANTIDO - Demo funcional
├── test_integration.py            # MANTIDO - Teste funcional
├── README.md                      # MANTIDO
├── INTEGRATION_PLAN.md            # MANTIDO
├── INTEGRATION_README.md          # MANTIDO
├── INTEGRATION_SUMMARY.md         # MANTIDO
└── CLEANUP_PLAN.md               # TEMPORÁRIO
```

## 🚀 **Benefícios da Limpeza**

1. **Foco**: Repositório mais limpo e focado no conductor
2. **Manutenção**: Menos arquivos para manter
3. **Clareza**: Estrutura mais clara para novos contribuidores
4. **Performance**: Menos arquivos para indexar e buscar
5. **Qualidade**: Código mais organizado e profissional

## ⚠️ **Precauções**

1. **Backup**: Fazer backup antes de remover arquivos
2. **Verificação**: Confirmar que arquivos não são referenciados
3. **Teste**: Testar funcionalidade após limpeza
4. **Documentação**: Atualizar README se necessário

## 📝 **Próximos Passos**

1. Executar Fase 1 (scripts obsoletos)
2. Testar funcionalidade
3. Executar Fase 2 (orquestradores antigos)
4. Testar funcionalidade
5. Continuar com fases subsequentes
6. Atualizar documentação
7. Commit das mudanças
