# 📋 Guia de Testes - Conductor Framework

## 🚀 Execução Rápida (Padrão)

```bash
# Executar todos os testes unitários (PADRÃO - 32 testes em 0.25s)
python -m pytest

# Comando equivalente (configuração automática em pytest.ini)
python -m pytest -m "not manual and not e2e and not mongo"

# Executar com cobertura
python -m pytest --cov=src --cov-report=html
```

## 🏷️ Categorias de Testes

### ✅ Testes Automáticos (CI/CD) - 32 testes
```bash
# Testes que rodam automaticamente (PADRÃO)
python -m pytest

# Configuração explícita (já aplicada em pytest.ini)
python -m pytest -m "not manual and not e2e and not mongo"
```

**Incluem:**
- `tests/core/test_prompt_engine.py` - PromptEngine (14 testes) ✅
- `tests/test_container.py` - Container/DI (6 testes) ✅
- `tests/test_core.py` - Agent Logic (7 testes) ✅  
- `tests/test_state_management.py` - File State Management (5 testes) ✅

**Performance:** 0.25 segundos ⚡

### 🔧 Testes Manuais (Sob Demanda)

#### E2E - End-to-End (1 teste)
```bash
# Executar teste E2E completo
python -m pytest tests/e2e/ -v

# Ou incluir na execução padrão
python -m pytest -m "e2e" -v

# Ou executar diretamente 
python tests/e2e/test_full_lifecycle.py
```

**O que testa:**
- `test_full_lifecycle_e2e` - Ciclo completo do agente
  - Criação via CLI (AgentCreator_Agent)
  - Validação de arquivos (agent.yaml, persona.md)
  - Execução de comandos
  - Verificação de estado
  - Cleanup automático

**Requisitos:**
- AgentCreator_Agent disponível
- Permissões de escrita no filesystem
- Timeout de 2+ minutos

#### MongoDB Tests (8 testes)  
```bash
# Instalar dependência primeiro
pip install pymongo

# Executar apenas testes MongoDB
python -m pytest -m "mongo" -v

# Ou filtro específico (comando antigo)
python -m pytest -k "mongo" -v
```

**O que testa:**
- Conexão MongoDB (MongoStateRepository)
- Save/Load de estado com MongoDB
- Integração file + mongo repositories
- Error handling para pymongo

**Requisitos:**
- `pymongo` instalado
- MongoDB running (para testes reais, mocks para unitários)

### 🔍 Testes de Integração
```bash  
# Scripts de integração (backup)
python scripts_backup_20250830_115420/test_integration.py
python scripts_backup_20250830_115420/demo_integration.py
```

## 🎯 Marcadores (Markers)

```bash
# Excluir testes específicos
python -m pytest -m "not e2e"          # Sem E2E (32 testes)
python -m pytest -m "not manual"       # Sem manuais (40 testes)  
python -m pytest -m "not mongo"        # Sem MongoDB (33 testes)

# Executar apenas testes específicos
python -m pytest -m "e2e"              # Apenas E2E (1 teste)
python -m pytest -m "mongo"            # Apenas MongoDB (8 testes)
python -m pytest -m "manual"           # Apenas manuais (1 teste)

# Combinações úteis
python -m pytest -m "not manual"       # Automáticos + MongoDB (40 testes)
python -m pytest -m "manual or e2e"    # Todos os manuais (1 teste)
```

## 📊 Configuração de CI/CD

### GitHub Actions / GitLab CI
```yaml
# .github/workflows/tests.yml
- name: Run Unit Tests (Fast)
  run: python -m pytest  # Usa configuração padrão do pytest.ini
  
- name: Run Unit + MongoDB Tests  
  run: python -m pytest -m "not manual and not e2e"
  
- name: Run E2E Tests (Manual Trigger Only)
  if: github.event_name == 'workflow_dispatch' 
  run: python -m pytest tests/e2e/ -v --timeout=300
```

### Configuração Local
```bash
# Testes padrão (usando pytest.ini automático)
python -m pytest

# Override configuração padrão para incluir tudo
python -m pytest --override-ini addopts="-v --tb=short"

# Ou temporariamente com variável de ambiente  
PYTEST_ADDOPTS="-v" python -m pytest tests/
```

## 🚫 Quando NÃO Executar E2E

❌ **Evitar em CI/CD automático:**
- Pull requests
- Commits automáticos  
- Builds de desenvolvimento

✅ **Executar manualmente quando:**
- Release candidates
- Validação pré-produção
- Debugging de problemas específicos
- Validação após refatorações grandes

## 🛠️ Troubleshooting

### E2E Falhando?
```bash
# Verificar se AgentCreator_Agent existe
ls projects/_common/agents/AgentCreator_Agent/

# Executar com logs detalhados
python -m pytest tests/e2e/ -v -s --tb=long

# Limpar cache de teste
rm -rf tests/e2e/__pycache__ .pytest_cache
```

### MongoDB Falhando?
```bash
# Instalar dependência
pip install pymongo

# Verificar se MongoDB está running
docker run -d -p 27017:27017 mongo:latest

# Ou pular testes MongoDB
python -m pytest -k "not mongo"
```

## 📈 Cobertura de Testes

```bash
# Gerar relatório HTML
python -m pytest --cov=src --cov-report=html

# Ver no browser
open htmlcov/index.html

# Relatório no terminal
python -m pytest --cov=src --cov-report=term-missing
```

## 🎯 Recomendações

1. **Desenvolvimento:** `python -m pytest` (32 testes, 0.25s) ⚡
2. **Pre-commit:** `python -m pytest` + lint
3. **Release:** `python -m pytest tests/e2e/ -v` (validação completa)
4. **CI/CD:** Padrão automático (pytest.ini cuida da configuração)
5. **Debug:** Use `-v -s --tb=long` para logs detalhados

## 📊 Resumo dos Comandos

| Situação | Comando | Testes | Tempo |
|----------|---------|--------|-------|
| **Desenvolvimento (padrão)** | `python -m pytest` | 32 unitários | 0.25s ⚡ |
| **Com MongoDB** | `python -m pytest -m "not manual and not e2e"` | 40 (unit+mongo) | ~1s |
| **E2E Manual** | `python -m pytest tests/e2e/ -v` | 1 end-to-end | ~30s+ |
| **Tudo** | `python -m pytest --override-ini addopts="-v"` | 41 completos | ~30s+ |