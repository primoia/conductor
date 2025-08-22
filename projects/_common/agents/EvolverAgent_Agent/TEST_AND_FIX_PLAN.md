# =' EvolverAgent: Plano de Teste e Corre��o

## Objetivo
Diagnosticar, testar, corrigir e validar o funcionamento do EvolverAgent Phase 2, identificando e resolvendo bugs de execu��o.

## Fase 1: Diagn�stico Inicial

### Passo 1.1: Teste de Execu��o B�sica
```bash
# Navegar para o diret�rio raiz do monorepo
cd /mnt/ramdisk/primoia-main/primoia-monorepo

# Executar o EvolverAgent via Docker
docker run --rm -v $(pwd):/monorepo evolver-agent
```

### Passo 1.2: Verificar Estrutura de Arquivos
```bash
# Verificar se todos os arquivos necess�rios est�o presentes
find ./projects/conductor/projects/_common/agents/EvolverAgent_Agent -type f -name "*.py" | sort
```

### Passo 1.3: Teste de Importa��es
```bash
# Testar importa��es Python diretamente
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys
sys.path.append('/monorepo')
try:
    from src.agent import EvolverAgent
    print(' EvolverAgent importado com sucesso')
except Exception as e:
    print(f'L Erro na importa��o: {e}')
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
print(f'Diret�rio: {kb.knowledge_base_dir}')
"
```

### Passo 2.2: Teste da An�lise de Complexidade
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.analysis import analyze_repo
results = analyze_repo('/monorepo')
print(f' An�lise conclu�da: {len(results)} problemas encontrados')
"
```

### Passo 2.3: Teste da An�lise de Seguran�a
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.security_analysis import analyze_security_issues
results = analyze_security_issues('/monorepo')
print(f' An�lise de seguran�a: {len(results)} problemas encontrados')
"
```

### Passo 2.4: Teste da An�lise de Depend�ncias
```bash
docker run --rm -v $(pwd):/monorepo evolver-agent python -c "
import sys, os
sys.path.append('/monorepo')
os.chdir('/monorepo')
from src.security_analysis import analyze_dependency_vulnerabilities
results = analyze_dependency_vulnerabilities('/monorepo')
print(f' An�lise de depend�ncias: {len(results)} vulnerabilidades encontradas')
"
```

## Fase 3: Teste de Integra��o Git

### Passo 3.1: Verificar Reposit�rio Git
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

## Fase 4: Execu��o Completa e Valida��o

### Passo 4.1: Execu��o Completa
```bash
# Executar o agente completo
docker run --rm -v $(pwd):/monorepo evolver-agent
```

### Passo 4.2: Verificar Artefatos Gerados
```bash
# Verificar se os relat�rios foram gerados
ls -la .evolver/reports/
cat .evolver/reports/HEALTH_REPORT.md | head -20
```

### Passo 4.3: Verificar Base de Conhecimento
```bash
# Verificar se a base de conhecimento foi criada
ls -la .evolver/knowledge_base/
```

## Fase 5: Corre��es Identificadas

### Corre��o 1: Problema de Caminho de Importa��o
**Problema**: Importa��es relativas podem falhar quando executado via Docker
**Solu��o**: Ajustar PYTHONPATH e caminhos de importa��o

### Corre��o 2: Problema de Permiss�es de Arquivo
**Problema**: Container pode n�o ter permiss�es para criar diret�rios
**Solu��o**: Ajustar permiss�es ou usar usu�rio correto

### Corre��o 3: Problema de Caminho do Reposit�rio
**Problema**: Caminho do reposit�rio pode estar incorreto no container
**Solu��o**: Ajustar l�gica de detec��o do caminho do reposit�rio

## Fase 6: Valida��o Final

### Passo 6.1: Teste Completo Ap�s Corre��es
```bash
# Rebuild da imagem Docker se necess�rio
docker build -t evolver-agent ./projects/conductor/projects/_common/agents/EvolverAgent_Agent

# Execu��o final
docker run --rm -v $(pwd):/monorepo evolver-agent
```

### Passo 6.2: Verificar Integridade dos Relat�rios
```bash
# Verificar conte�do dos relat�rios
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
    print(f' JSON v�lido com {len(data.get(\"tasks\", []))} tarefas')
"
```

## Crit�rios de Sucesso

- [ ] EvolverAgent executa sem erros
- [ ] Relat�rios s�o gerados corretamente
- [ ] Base de conhecimento � criada
- [ ] An�lises de complexidade, seguran�a e depend�ncias funcionam
- [ ] Git integration funciona corretamente
- [ ] JSON de tarefas � v�lido e estruturado

## Logs de Execu��o

Documentar aqui os resultados de cada fase e as corre��es aplicadas.