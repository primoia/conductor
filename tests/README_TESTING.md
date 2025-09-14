# 📋 Guia de Testes - Conductor Framework

## 🚀 Execução Rápida (Padrão)

```bash
# LOCAL: Executar TODOS os testes (PADRÃO - incluindo integration)
poetry run pytest

# CI: Executar apenas testes CI-safe (sem dependencies externas)
poetry run pytest -m "not manual and not e2e and not integration and not mongo"

# Script helper para CI-safe tests
python run_ci_tests.py

# Executar com cobertura
poetry run pytest --cov=src --cov-report=html
```

## 🏷️ Categorias de Testes

### ✅ Testes CI-Safe (GitHub Actions) - 93 testes
```bash
# CI: Testes que rodam automaticamente no GitHub Actions
poetry run pytest -m "not manual and not e2e and not integration and not mongo"

# LOCAL: Todos os testes (padrão para desenvolvimento)
poetry run pytest
```

**Incluem:**
- `tests/core/services/test_task_execution_service.py` - TaskExecutionService (8 testes) ✅
- `tests/core/services/test_agent_storage_service.py` - AgentStorageService (6 testes) ✅
- `tests/core/test_prompt_engine.py` - PromptEngine (14 testes) ✅
- `tests/core/services/test_configuration_service.py` - ConfigurationService (4 testes) ✅
- `tests/core/services/test_tool_management_service.py` - ToolManagementService (8 testes) ✅
- `tests/test_container.py` - Dependency Injection (10 testes) ✅
- `tests/test_argument_parser.py` - CLI Parsing (6 testes) ✅
- E mais 47+ testes de serviços core

**Performance:** ~21 segundos ⚡ **Dependências:** Zero (apenas mocks)

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

### GitHub Actions - `.github/workflows/test.yml` ✅
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
    - name: Install Poetry
      uses: snok/install-poetry@v1
    - name: Install dependencies
      run: poetry install --no-interaction
    - name: Run CI-safe tests
      run: |
        poetry run pytest \
          -v --tb=short \
          -m "not e2e and not integration and not manual and not mongo" \
          --maxfail=10 tests/
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

1. **Desenvolvimento:** `poetry run pytest` (103 testes CI-safe, ~21s) ⚡
2. **CI/CD Local:** `python run_ci_tests.py` (helper script)
3. **Pre-commit:** `poetry run pytest` + lint
4. **Release:** `poetry run pytest tests/e2e/ -v` (validação completa)
5. **GitHub Actions:** Automático (pytest.ini + workflow configurados)
6. **Debug:** Use `-v -s --tb=long` para logs detalhados

## 📊 Resumo dos Comandos

| Situação | Comando | Testes | Tempo |
|----------|---------|--------|-------|
| **Desenvolvimento (padrão local)** | `poetry run pytest` | 104 todos | ~21s ⚡ |
| **CI Safe (GitHub Actions)** | `poetry run pytest -m "not e2e and not integration and not manual and not mongo"` | 93 CI-safe | ~3s ⚡ |
| **CI Helper Script** | `python run_ci_tests.py` | 93 CI-safe | ~3s ⚡ |
| **Com MongoDB** | `poetry run pytest -m "not manual and not e2e"` | ~111 (unit+mongo) | ~25s |
| **E2E Manual** | `poetry run pytest tests/e2e/ -v` | E2E completos | ~60s+ |
| **Tudo** | `poetry run pytest --override-ini addopts="-v"` | Todos completos | ~90s+ |

## 🚀 **GitHub Actions CI**
- **Trigger:** Push/PR para main/develop
- **Python:** 3.11 e 3.12
- **Testes:** 93 CI-safe (sem Claude/Gemini/MongoDB/config.yaml)
- **Tempo:** ~1 minuto total (setup + testes)
- **Dependências:** Zero externas ✅