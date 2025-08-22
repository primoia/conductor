# =' EvolverAgent: Plano de Teste e Correção

## Objetivo
Diagnosticar, testar, corrigir e validar o funcionamento do EvolverAgent Phase 2, identificando e resolvendo bugs de execução.

## Fase 1: Diagnóstico Inicial

### Passo 1.1: Teste de Execução Básica
```bash
# Navegar para o diretório raiz do monorepo
cd /mnt/ramdisk/primoia-main/primoia-monorepo

# Executar o EvolverAgent via Docker
docker run --rm -v $(pwd):/monorepo evolver-agent
```

### Passo 1.2: Verificar Estrutura de Arquivos
```bash
# Verificar se todos os arquivos necessários estão presentes
find ./projects/conductor/projects/_common/agents/EvolverAgent_Agent -type f -name "*.py" | sort
```

### Passo 1.3: Teste de Importações
```bash
# Testar importações Python diretamente
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys
sys.path.append('/monorepo')
try:
    from src.agent import EvolverAgent
    print(' EvolverAgent importado com sucesso')
except Exception as e:
    print(f'L Erro na importação: {e}')
"
```

## Fase 2: Teste de Componentes Individuais

### Passo 2.1: Teste do KnowledgeBase
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.knowledge_base import KnowledgeBase
kb = KnowledgeBase('/monorepo')
print(' KnowledgeBase funcionando')
print(f'Diretório: {kb.knowledge_base_dir}')
"
```

### Passo 2.2: Teste da Análise de Complexidade
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.analysis import analyze_repo
results = analyze_repo('/monorepo')
print(f' Análise concluída: {len(results)} problemas encontrados')
"
```

### Passo 2.3: Teste da Análise de Segurança
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.security_analysis import analyze_security_issues
results = analyze_security_issues('/monorepo')
print(f' Análise de segurança: {len(results)} problemas encontrados')
"
```

### Passo 2.4: Teste da Análise de Dependências
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.security_analysis import analyze_dependency_vulnerabilities
results = analyze_dependency_vulnerabilities('/monorepo')
print(f' Análise de dependências: {len(results)} vulnerabilidades encontradas')
"
```

## Fase 3: Teste de Integração Git

### Passo 3.1: Verificar Repositório Git
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from git import Repo
repo = Repo('/monorepo')
print(f' Git funcionando: {repo.head.commit.hexsha[:8]}')
"
```

### Passo 3.2: Teste do Agente Completo
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.agent import EvolverAgent
agent = EvolverAgent()
info = agent.get_repo_info()
print(f' Agente inicializado: {info}')
"
```

## Fase 4: Execução Completa e Validação

### Passo 4.1: Execução Completa
```bash
# Executar o agente completo
docker run --rm -v $(pwd):/monorepo evolver-agent
```

### Passo 4.2: Verificar Artefatos Gerados
```bash
# Verificar se os relatórios foram gerados
ls -la .evolver/reports/
cat .evolver/reports/HEALTH_REPORT.md | head -20
```

### Passo 4.3: Verificar Base de Conhecimento
```bash
# Verificar se a base de conhecimento foi criada
ls -la .evolver/knowledge_base/
```

## Fase 5: Correções Identificadas

### Correção 1: Problema de Caminho de Importação
**Problema**: Importações relativas podem falhar quando executado via Docker
**Solução**: Ajustar PYTHONPATH e caminhos de importação

### Correção 2: Problema de Permissões de Arquivo
**Problema**: Container pode não ter permissões para criar diretórios
**Solução**: Ajustar permissões ou usar usuário correto

### Correção 3: Problema de Caminho do Repositório
**Problema**: Caminho do repositório pode estar incorreto no container
**Solução**: Ajustar lógica de detecção do caminho do repositório

## Fase 6: Validação Final

### Passo 6.1: Teste Completo Após Correções
```bash
# Rebuild da imagem Docker se necessário
docker build -t evolver-agent ./projects/conductor/projects/_common/agents/EvolverAgent_Agent

# Execução final
docker run --rm -v $(pwd):/monorepo evolver-agent
```

### Passo 6.2: Verificar Integridade dos Relatórios
```bash
# Verificar conteúdo dos relatórios
test -f .evolver/reports/HEALTH_REPORT.md && echo " Health Report criado"
test -f .evolver/reports/TASK_SUGGESTIONS.json && echo " Task Suggestions criado"
```

### Passo 6.3: Validar JSON
```bash
# Validar estrutura do JSON
python -c "
import json
with open('.evolver/reports/TASK_SUGGESTIONS.json', 'r') as f:
    data = json.load(f)
    print(f' JSON válido com {len(data.get(\"tasks\", []))} tarefas')
"
```

## Critérios de Sucesso

- [ ] EvolverAgent executa sem erros
- [ ] Relatórios são gerados corretamente
- [ ] Base de conhecimento é criada
- [ ] Análises de complexidade, segurança e dependências funcionam
- [ ] Git integration funciona corretamente
- [ ] JSON de tarefas é válido e estruturado

## Logs de Execução

Documentar aqui os resultados de cada fase e as correções aplicadas.