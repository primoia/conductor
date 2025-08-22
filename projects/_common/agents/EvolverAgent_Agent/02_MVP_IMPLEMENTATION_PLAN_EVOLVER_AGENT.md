# 📜 EvolverAgent: Plano de Implementação do MVP

## 1. Objetivo

Construir e integrar a primeira versão funcional (MVP) do `EvolverAgent`. O agente deverá ser capaz de rodar via CI/CD, analisar o repositório, evitar trabalho repetitivo e gerar um relatório de saúde básico.

## 2. Escopo do MVP

1.  **Linguagem:** Python.
2.  **Análise:** Análise de complexidade de código Python (`.py`) em todo o monorepo.
3.  **Persistência:** Lógica da Base de Conhecimento com hash de commit.
4.  **Artefato:** Geração do `HEALTH_REPORT.md`.
5.  **Containerização:** Um `Dockerfile` para rodar o agente.
6.  **Integração:** Um workflow de GitHub Actions para disparar o agente a cada push.

## 3. Instruções para o Agente Executor (Claude)

Siga os passos abaixo para implementar o MVP.

### Passo 1: Estrutura de Arquivos

Crie a seguinte estrutura de arquivos dentro de `projects/conductor/projects/_common/agents/EvolverAgent_Agent/`:

```
projects/conductor/projects/_common/agents/EvolverAgent_Agent/
|-- src/
|   |-- __main__.py       # Ponto de entrada
|   |-- agent.py          # Lógica principal do agente
|   |-- analysis.py       # Módulos de análise (ex: complexidade)
|   |-- knowledge_base.py # Gerenciamento da base de conhecimento
|   |-- artifacts.py      # Geração dos relatórios
|-- Dockerfile
|-- requirements.txt
```

### Passo 2: Dependências

Preencha o arquivo `requirements.txt` com as seguintes bibliotecas:

```
radon
GitPython
```

### Passo 3: Implementação da Lógica

**3.1 - `knowledge_base.py`:**
*   Crie uma classe `KnowledgeBase`.
*   Implemente um método `has_commit(commit_hash)` que verifica se o arquivo `/.evolver/knowledge_base/{commit_hash}.json` existe.
*   Implemente um método `store_results(commit_hash, results)` que salva um dicionário de resultados no arquivo correspondente.

**3.2 - `analysis.py`:**
*   Crie uma função `analyze_repo(repo_path)` que:
    *   Use o `glob` para encontrar todos os arquivos `.py` no `repo_path`.
    *   Use a biblioteca `radon` para calcular a complexidade ciclomática de cada função/método em cada arquivo.
    *   Retorne uma lista de dicionários com os problemas encontrados (ex: `{'file': path, 'function': name, 'complexity': value}`), focando apenas em funções com complexidade > 10.

**3.3 - `artifacts.py`:**
*   Crie uma função `generate_health_report(results)` que:
    *   Receba a lista de problemas da análise.
    *   Gere um arquivo `HEALTH_REPORT.md` no formato Markdown dentro de `/.evolver/reports/`.
    *   O relatório deve listar os arquivos e funções que excederam o limite de complexidade.

**3.4 - `agent.py`:**
*   Crie uma classe `EvolverAgent` com um método `run()`.
*   O método `run()` deve:
    1.  Obter o caminho raiz do monorepo (ir seis níveis acima do diretório do script, para chegar em `primoia-main/primoia-monorepo`).
    2.  Usar `git.Repo` (da biblioteca GitPython) para obter o hash do commit HEAD.
    3.  Instanciar `KnowledgeBase` e verificar se o commit já foi processado (`has_commit`). Se sim, imprima uma mensagem e saia.
    4.  Chamar `analyze_repo()` para obter os resultados.
    5.  Chamar `generate_health_report()` com os resultados.
    6.  Chamar `store_results()` para salvar os resultados na base de conhecimento.

**3.5 - `__main__.py`:**
*   Este arquivo deve apenas instanciar e executar o `EvolverAgent`: `EvolverAgent().run()`.

### Passo 4: Containerização

Preencha o `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# O diretório do monorepo será montado como um volume em /monorepo
VOLUME /monorepo

# O comando de entrada executará o agente
ENTRYPOINT ["python", "-m", "src"]
```

### Passo 5: CI/CD (GitHub Actions)

Crie o arquivo `.github/workflows/evolver_agent.yml` (na raiz do monorepo):

```yaml
name: EvolverAgent CI

on:
  push:
    branches: [ main, develop ]

jobs:
  evolve:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Monorepo
        uses: actions/checkout@v3
        with:
          fetch-depth: 0 # Necessário para o GitPython ler o histórico

      - name: Build EvolverAgent Docker image
        run: docker build -t evolver-agent ./primoia-main/primoia-monorepo/projects/conductor/projects/_common/agents/EvolverAgent_Agent

      - name: Run EvolverAgent
        run: docker run --rm -v $(pwd):/monorepo evolver-agent

      - name: Commit Reports
        run: |
          git config --global user.name 'EvolverAgent'
          git config --global user.email 'evolver.agent@primoia.ai'
          git add .evolver/
          # Apenas commita se houver mudanças nos relatórios
          git diff-index --quiet HEAD || git commit -m "chore(EvolverAgent): Update analysis reports"
          git push
```

---

**Conclusão:** Ao final destes passos, o MVP estará completo e funcional.
