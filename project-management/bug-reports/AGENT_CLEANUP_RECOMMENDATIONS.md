# 🧹 Recomendações de Limpeza dos Agentes

## 📊 **Resumo da Análise: 13 Agentes**

### ✅ **MANTER (Production Ready - 5 agentes)**
- `AgentCreator_Agent` - ✅ Completo
- `OnboardingGuide_Agent` - ✅ Completo
- `PlanCreator_Agent` - ✅ Completo  
- `ProblemRefiner_Agent` - ✅ Completo
- `KotlinServiceCreator_Agent` - ✅ Completo

### 🔧 **CORRIGIR (Inconsistent - 3 agentes)**
- `KotlinTestCreator_Agent` - ❌ Copy-paste error crítico
- `KotlinRepositoryCreator_Agent` - ❌ Copy-paste error crítico
- `KotlinEntityCreator_Agent` - ⚠️ Template original (ok, mas foi mal copiado)

### 🚧 **PADRONIZAR (Prototype - 4 agentes)**
- `unit-test-strategy-agent` - ⚠️ Naming inconsistente + arquivo temp
- `kotlin-test-creator-agent` - ⚠️ Naming inconsistente + arquivo temp
- `unit-test-executor-agent` - ⚠️ Naming inconsistente + arquivo temp
- `QuotationReceiptService_IntegrationTest_Agent` - ✅ Ok (específico)

### 🗑️ **REMOVER (Obsolete - 1 agente)**
- `PythonDocumenter_Agent` - ❌ Formato antigo incompatível

## 🔄 **Ações Recomendadas por Prioridade**

### **🚨 CRÍTICO (Copy-paste errors)**
1. **KotlinTestCreator_Agent**
   - Descrição fala sobre "Hibernate" em vez de testes
   - execution_task é sobre Entity Creator
   - persona.md completamente errado

2. **KotlinRepositoryCreator_Agent**  
   - Mesmo problema - cópia mal feita do EntityCreator

### **⚠️ ALTO (Naming padronization)**
3. Renomear agentes com hífen:
   - `unit-test-strategy-agent` → `UnitTestStrategy_Agent`
   - `kotlin-test-creator-agent` → `KotlinTestCreator_Agent` (já existe!)
   - `unit-test-executor-agent` → `UnitTestExecutor_Agent`

### **📁 MÉDIO (Limpeza de arquivos)**
4. Remover arquivos temporários:
   - `*/1.txt`, `*/2.txt`, `*/3.txt`
   - São comandos Claude de desenvolvimento

### **🗑️ BAIXO (Remoção)**
5. **PythonDocumenter_Agent**
   - Formato YAML antigo
   - Falta campos obrigatórios (ai_provider)
   - Incompatível com especificação atual

## 📋 **Lista Final para Confirmação**

### **DELETAR:**
- [ ] `PythonDocumenter_Agent` (obsoleto - formato antigo)

### **CORRIGIR URGENTE:**
- [ ] `KotlinTestCreator_Agent` (descriptions e tasks errados)
- [ ] `KotlinRepositoryCreator_Agent` (descriptions e tasks errados)

### **RENOMEAR:**
- [ ] `unit-test-strategy-agent` → `UnitTestStrategy_Agent`
- [ ] `kotlin-test-creator-agent` → `KotlinTestCreator_Agent` (mas já existe um broken!)
- [ ] `unit-test-executor-agent` → `UnitTestExecutor_Agent`

### **LIMPAR ARQUIVOS:**
- [ ] Remover `*/1.txt`, `*/2.txt`, `*/3.txt`
- [ ] Remover arquivos de desenvolvimento temporário

## 🎯 **Sistema de Versionamento**

### **Padrão Atual:**
- **version: "1.0"** - Padrão estabelecido
- **ai_provider: 'claude'** - Padrão obrigatório
- **Especificação: Maestro v2.1** - Versão atual

### **Proposta de Evolução:**
- **version mínima**: 1.0 (para compatibilidade)
- **Deprecação**: Agentes com version < 1.0 ou sem ai_provider
- **Validação**: Automática ao carregar agente

---
*Análise realizada em: 2025-08-16*