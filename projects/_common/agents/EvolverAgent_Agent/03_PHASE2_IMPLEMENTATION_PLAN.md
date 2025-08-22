# 📜 EvolverAgent: Plano de Implementação da Fase 2

## 1. Objetivo

Expandir o EvolverAgent MVP para incluir a geração do artefato `TASK_SUGGESTIONS.json`, criando uma interface estruturada para que outros agentes de IA possam consumir as análises e automatizar tarefas de melhoria.

## 2. Escopo da Fase 2

1. **Geração de Tarefas**: Criar `TASK_SUGGESTIONS.json` com tarefas acionáveis
2. **Análises Expandidas**: Adicionar análise de segurança básica e dependências
3. **Classificação Inteligente**: Categorizar problemas por tipo e prioridade
4. **Interface para IA**: Estruturar dados para consumo por outros agentes

## 3. Instruções para o Agente Executor (Claude)

Siga os passos abaixo para implementar a Fase 2.

### Passo 1: Expandir Dependências

Atualize o arquivo `requirements.txt` adicionando:

```
radon
GitPython
bandit
safety
pipdeptree
```

### Passo 2: Implementar Análise de Segurança

Crie o arquivo `src/security_analysis.py`:

```python
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict

def analyze_security_issues(repo_path: str) -> List[Dict]:
    """
    Analisa problemas de segurança usando bandit
    """
    # Implementar análise com bandit
    pass

def analyze_dependency_vulnerabilities(repo_path: str) -> List[Dict]:
    """
    Analisa vulnerabilidades em dependências usando safety
    """
    # Implementar análise com safety
    pass
```

### Passo 3: Implementar Gerador de Tarefas

Crie o arquivo `src/task_generator.py`:

```python
from typing import List, Dict
import uuid
from datetime import datetime

def generate_task_suggestions(
    complexity_issues: List[Dict],
    security_issues: List[Dict],
    dependency_issues: List[Dict]
) -> List[Dict]:
    """
    Gera sugestões de tarefas baseadas nos problemas encontrados
    """
    tasks = []
    
    # Gerar tarefas de refatoração para complexidade
    for issue in complexity_issues:
        task = {
            "id": f"REFACTOR-{str(uuid.uuid4())[:8].upper()}",
            "project": extract_project_name(issue['file']),
            "type": "REFACTORING",
            "priority": get_complexity_priority(issue['complexity']),
            "description": f"Refactor function '{issue['function']}' with complexity {issue['complexity']}",
            "location": {
                "file": issue['file'],
                "line": issue['line']
            },
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_effort": estimate_refactoring_effort(issue['complexity'])
        }
        tasks.append(task)
    
    # Gerar tarefas de segurança
    for issue in security_issues:
        task = {
            "id": f"SECURITY-{str(uuid.uuid4())[:8].upper()}",
            "project": extract_project_name(issue['file']),
            "type": "SECURITY",
            "priority": get_security_priority(issue['severity']),
            "description": f"Fix security issue: {issue['test_name']}",
            "location": {
                "file": issue['file'],
                "line": issue.get('line_number', 1)
            },
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "security_details": {
                "severity": issue['severity'],
                "confidence": issue['confidence'],
                "cwe_id": issue.get('test_id', '')
            }
        }
        tasks.append(task)
    
    # Gerar tarefas de dependências
    for issue in dependency_issues:
        task = {
            "id": f"DEPENDENCY-{str(uuid.uuid4())[:8].upper()}",
            "project": extract_project_name(issue['file']),
            "type": "DEPENDENCY",
            "priority": get_dependency_priority(issue['severity']),
            "description": f"Update vulnerable dependency: {issue['package']} {issue['version']}",
            "location": {
                "file": issue['file']
            },
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "dependency_details": {
                "package": issue['package'],
                "current_version": issue['version'],
                "vulnerability_id": issue['id'],
                "advisory": issue['advisory']
            }
        }
        tasks.append(task)
    
    return tasks

def extract_project_name(file_path: str) -> str:
    """Extrai o nome do projeto do caminho do arquivo"""
    # Implementar lógica para extrair projeto
    pass

def get_complexity_priority(complexity: int) -> str:
    """Determina prioridade baseada na complexidade"""
    # Implementar lógica de prioridade
    pass

def get_security_priority(severity: str) -> str:
    """Determina prioridade baseada na severidade de segurança"""
    # Implementar lógica de prioridade
    pass

def get_dependency_priority(severity: str) -> str:
    """Determina prioridade baseada na vulnerabilidade de dependência"""
    # Implementar lógica de prioridade
    pass

def estimate_refactoring_effort(complexity: int) -> str:
    """Estima esforço de refatoração baseado na complexidade"""
    # Implementar estimativa
    pass
```

### Passo 4: Atualizar artifacts.py

Adicione a função para gerar o arquivo JSON:

```python
def generate_task_suggestions_json(tasks: List[Dict], repo_path: str) -> None:
    """
    Gera o arquivo TASK_SUGGESTIONS.json com tarefas acionáveis
    """
    repo_path = Path(repo_path)
    reports_dir = repo_path / ".evolver" / "reports"
    
    # Ensure the reports directory exists
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    suggestions_path = reports_dir / "TASK_SUGGESTIONS.json"
    
    # Adicionar metadados
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "agent_version": "Phase2-1.0",
            "total_tasks": len(tasks),
            "task_types": get_task_type_summary(tasks)
        },
        "tasks": tasks
    }
    
    with open(suggestions_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Task suggestions generated: {suggestions_path}")

def get_task_type_summary(tasks: List[Dict]) -> Dict:
    """Gera resumo dos tipos de tarefas"""
    # Implementar contagem por tipo
    pass
```

### Passo 5: Atualizar agent.py

Modifique o método `run()` para incluir as novas análises:

```python
def run(self) -> None:
    """
    Main execution method for the EvolverAgent Phase 2.
    """
    print("🧠 EvolverAgent Phase 2 Starting...")
    print(f"📁 Repository path: {self.repo_path}")
    
    # Get current commit hash
    commit_hash = self._get_current_commit_hash()
    print(f"📋 Current commit: {commit_hash[:8]}")
    
    # Check if this commit has already been analyzed
    if self.knowledge_base.has_commit(commit_hash):
        print("✅ This commit has already been analyzed. Exiting.")
        return
    
    print("🔍 Running comprehensive analysis...")
    
    try:
        # Perform complexity analysis
        complexity_results = analyze_repo(self.repo_path)
        print(f"📊 Found {len(complexity_results)} complexity issues")
        
        # Perform security analysis
        security_results = analyze_security_issues(self.repo_path)
        print(f"🔒 Found {len(security_results)} security issues")
        
        # Perform dependency analysis
        dependency_results = analyze_dependency_vulnerabilities(self.repo_path)
        print(f"📦 Found {len(dependency_results)} dependency issues")
        
        # Generate task suggestions
        task_suggestions = generate_task_suggestions(
            complexity_results, security_results, dependency_results
        )
        print(f"📋 Generated {len(task_suggestions)} task suggestions")
        
        # Generate artifacts
        generate_health_report(complexity_results, self.repo_path)
        generate_task_suggestions_json(task_suggestions, self.repo_path)
        
        # Prepare results for storage
        results = {
            'commit_hash': commit_hash,
            'timestamp': datetime.now().isoformat(),
            'complexity_results': complexity_results,
            'security_results': security_results,
            'dependency_results': dependency_results,
            'task_suggestions': task_suggestions,
            'summary_stats': generate_summary_stats(complexity_results),
            'agent_version': 'Phase2-1.0'
        }
        
        # Store results in knowledge base
        self.knowledge_base.store_results(commit_hash, results)
        print("💾 Results stored in knowledge base")
        
        print("✅ EvolverAgent Phase 2 analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        sys.exit(1)
```

### Passo 6: Implementar Análises Detalhadas

Complete as implementações em `security_analysis.py` e `task_generator.py` com lógica real para:

1. **Análise de Segurança (bandit)**:
   - Executar bandit nos arquivos Python
   - Parsear resultados JSON
   - Filtrar por severidade

2. **Análise de Dependências (safety)**:
   - Encontrar arquivos requirements.txt
   - Executar safety check
   - Parsear vulnerabilidades

3. **Geração de Tarefas**:
   - Classificar por prioridade (critical, high, medium, low)
   - Estimar esforço de correção
   - Agrupar por projeto

### Passo 7: Atualizar Health Report

Expanda o `HEALTH_REPORT.md` para incluir:

```markdown
## 🔒 Security Issues
## 📦 Dependency Vulnerabilities  
## 📋 Recommended Actions
```

### Passo 8: Atualizar Dockerfile

Nenhuma mudança necessária no Dockerfile, as novas dependências serão instaladas automaticamente.

---

**Conclusão:** Ao final desta fase, o EvolverAgent será capaz de gerar análises abrangentes e tarefas estruturadas para outros agentes consumirem e automatizarem melhorias no código.