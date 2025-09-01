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

### ✅ Testes Automáticos (CI/CD)
```bash
# Testes que rodam automaticamente
python -m pytest -m "not manual and not e2e and not slow"
```

**Incluem:**
- `tests/core/` - Componentes principais
- `tests/test_container.py` - Injeção de dependência  
- `tests/test_core.py` - Lógica de agentes
- `tests/test_state_management.py` - Gerenciamento de estado (file)

### 🔧 Testes Manuais (Sob Demanda)

#### E2E - End-to-End
```bash
# Executar teste E2E completo
python -m pytest tests/e2e/ -v

# Ou diretamente
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

#### MongoDB Tests  
```bash
# Instalar dependência primeiro
pip install pymongo

# Executar testes MongoDB
python -m pytest tests/ -k "mongo" -v
```

**O que testa:**
- Conexão MongoDB
- Save/Load de estado
- Integração com repositórios

**Requisitos:**
- `pymongo` instalado
- MongoDB running (para testes reais)

### 🔍 Testes de Integração
```bash  
# Scripts de integração (backup)
python scripts_backup_20250830_115420/test_integration.py
python scripts_backup_20250830_115420/demo_integration.py
```

## 🎯 Marcadores (Markers)

```bash
# Excluir testes específicos
python -m pytest -m "not e2e"          # Sem E2E
python -m pytest -m "not manual"       # Sem manuais  
python -m pytest -m "not slow"         # Sem lentos
python -m pytest -m "not mongo"        # Sem MongoDB

# Executar apenas testes específicos
python -m pytest -m "e2e"              # Apenas E2E
python -m pytest -m "integration"      # Apenas integração
```

## 📊 Configuração de CI/CD

### GitHub Actions / GitLab CI
```yaml
# .github/workflows/tests.yml
- name: Run Unit Tests
  run: python -m pytest -m "not manual and not e2e and not slow"
  
- name: Run E2E Tests (Manual Trigger Only)
  if: github.event_name == 'workflow_dispatch'
  run: python -m pytest tests/e2e/ -v
```

### Configuração Local
```bash
# Configurar para desenvolvimento
export PYTEST_ADDOPTS="-v --tb=short -m 'not manual'"

# Executar testes completos (manual)
unset PYTEST_ADDOPTS && python -m pytest tests/
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

1. **Desenvolvimento:** Execute apenas testes unitários
2. **Pre-commit:** Execute testes rápidos + lint
3. **Release:** Execute testes completos including E2E
4. **CI/CD:** Configure exclusão de testes manuais
5. **Local:** Use marcadores para controle fino