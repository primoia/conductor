# Plano de Reorganização da Estrutura do Repositório

## 📊 **Análise da Estrutura Atual**

### 🗂️ **Arquivos na Raiz (MUITOS!)**
- **Scripts Python**: `run_conductor.py`, `focused_claude_orchestrator.py`, `demo_integration.py`, `test_integration.py`
- **Documentação**: `README.md`, `INTEGRATION_*.md`, `PLAN-A_*.md`, `CLEANUP_*.md`, `BREAKTHROUGH.md`, `CHANGELOG.md`, `CONTEXT.md`
- **Outros**: `.gitignore`

### 📁 **Diretórios Existentes**
- `.bmad-core/` - Metodologia (MANTIDO)
- `config/` - Configurações (MANTIDO)
- `docs/` - Documentação (EXPANDIDO)
- `examples/` - Exemplos (MANTIDO)
- `orchestrator/` - Orquestradores (REORGANIZADO)
- `projects/` - Projetos (MANTIDO)
- `scripts/` - Scripts (EXPANDIDO)
- `src/` - Código gerado (MANTIDO)
- `stories/` - Histórias (MANTIDO)
- `demo/` - Demos (MANTIDO)

## 🎯 **Estrutura Proposta**

```
conductor/
├── .bmad-core/                    # ✅ Metodologia (mantido)
├── config/                        # ✅ Configurações (mantido)
├── docs/                          # 📁 Documentação expandida
│   ├── README.md                  # 📄 README principal
│   ├── integration/               # 📁 Documentação de integração
│   │   ├── INTEGRATION_PLAN.md
│   │   ├── INTEGRATION_README.md
│   │   └── INTEGRATION_SUMMARY.md
│   ├── plans/                     # 📁 Planos de implementação
│   │   ├── PLAN-A_CONDUCTOR_REFACTOR.md
│   │   └── PLAN-A_IMPLEMENTATION_SUMMARY.md
│   ├── cleanup/                   # 📁 Documentação de limpeza
│   │   ├── CLEANUP_PLAN.md
│   │   └── CLEANUP_SUMMARY.md
│   ├── history/                   # 📁 Histórico do projeto
│   │   ├── BREAKTHROUGH.md
│   │   ├── CHANGELOG.md
│   │   └── CONTEXT.md
│   └── architecture/              # 📁 Documentação de arquitetura
│       └── coding-standards.md
├── scripts/                       # 📁 Scripts organizados
│   ├── run_conductor.py           # 🚀 Script principal
│   ├── focused_claude_orchestrator.py # 🔧 Referência
│   ├── demo_integration.py        # 🎭 Demo
│   └── test_integration.py        # 🧪 Teste
├── orchestrator/                  # 📁 Orquestradores
│   ├── kotlin_test_orchestrator.py # 🔧 Orquestrador específico
│   └── README.md                  # 📄 Documentação
├── examples/                      # ✅ Exemplos (mantido)
├── projects/                      # ✅ Projetos (mantido)
├── src/                           # ✅ Código gerado (mantido)
├── stories/                       # ✅ Histórias (mantido)
├── demo/                          # ✅ Demos (mantido)
└── .gitignore                     # ✅ Git ignore (mantido)
```

## 🚀 **Plano de Ação**

### **Fase 1: Criar Nova Estrutura de Diretórios**
```bash
# Criar diretórios de documentação
mkdir -p docs/integration
mkdir -p docs/plans
mkdir -p docs/cleanup
mkdir -p docs/history

# Mover scripts para diretório scripts/
mkdir -p scripts
```

### **Fase 2: Mover Documentação**
```bash
# Mover documentação de integração
mv INTEGRATION_PLAN.md docs/integration/
mv INTEGRATION_README.md docs/integration/
mv INTEGRATION_SUMMARY.md docs/integration/

# Mover planos
mv PLAN-A_CONDUCTOR_REFACTOR.md docs/plans/
mv PLAN-A_IMPLEMENTATION_SUMMARY.md docs/plans/

# Mover documentação de limpeza
mv CLEANUP_PLAN.md docs/cleanup/
mv CLEANUP_SUMMARY.md docs/cleanup/

# Mover histórico
mv BREAKTHROUGH.md docs/history/
mv CHANGELOG.md docs/history/
mv CONTEXT.md docs/history/

# Mover README principal
mv README.md docs/
```

### **Fase 3: Mover Scripts**
```bash
# Mover scripts Python
mv run_conductor.py scripts/
mv focused_claude_orchestrator.py scripts/
mv demo_integration.py scripts/
mv test_integration.py scripts/
```

### **Fase 4: Atualizar Referências**
```bash
# Atualizar imports e referências nos scripts
# Atualizar documentação com novos caminhos
# Criar links simbólicos se necessário
```

### **Fase 5: Criar README Principal**
```bash
# Criar novo README.md na raiz com navegação
# Incluir links para documentação organizada
# Manter informações essenciais na raiz
```

## 📋 **Benefícios da Reorganização**

### 1. **Clareza e Organização**
- Documentação organizada por categoria
- Scripts centralizados em um diretório
- Fácil navegação e localização de arquivos

### 2. **Manutenibilidade**
- Estrutura escalável para futuras adições
- Separação clara de responsabilidades
- Documentação bem categorizada

### 3. **Profissionalismo**
- Estrutura de projeto padrão
- Fácil onboarding para novos contribuidores
- Documentação bem organizada

### 4. **Escalabilidade**
- Fácil adição de novos scripts
- Categorização automática de novos documentos
- Estrutura preparada para crescimento

## ⚠️ **Precauções**

1. **Backup**: Fazer backup antes de reorganizar
2. **Referências**: Verificar e atualizar todas as referências
3. **Teste**: Testar funcionalidade após reorganização
4. **Documentação**: Atualizar documentação com novos caminhos

## 📝 **Próximos Passos**

1. Executar Fase 1 (criar diretórios)
2. Executar Fase 2 (mover documentação)
3. Executar Fase 3 (mover scripts)
4. Executar Fase 4 (atualizar referências)
5. Executar Fase 5 (criar README principal)
6. Testar funcionalidade
7. Commit das mudanças
