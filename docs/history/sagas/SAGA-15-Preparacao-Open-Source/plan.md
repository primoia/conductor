# Plano de Execução para Claude: Preparação Open Source do Conductor

**Missão:** Executar as tarefas de preparação final para o lançamento do projeto Conductor como código aberto. Siga cada passo rigorosamente.

**Contexto:** Você está operando no diretório raiz do projeto `Conductor`. Todas as ferramentas necessárias estão disponíveis. Você não precisa de contexto adicional; todas as instruções e conteúdos estão neste plano.

---

### Passo 1: Criar o Workflow de Integração Contínua (CI)

**Objetivo:** Adicionar um workflow de GitHub Actions para garantir que todos os commits e pull requests sejam testados automaticamente.

**Ação:** Crie um novo arquivo no caminho `.github/workflows/ci.yaml` com o conteúdo exato abaixo.

**Conteúdo para `.github/workflows/ci.yaml`:**
```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python 3.10
        uses: actions/setup-python@v3
        with:
          python-version: "3.10"

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install dependencies
        run: poetry install

      - name: Run linter (Ruff)
        run: poetry run ruff check .

      - name: Check formatting (Black)
        run: poetry run black --check .

      - name: Run tests (Pytest)
        run: poetry run pytest
```

**Verificação:**
1.  Use o comando `ls -R .github` para confirmar que o arquivo `.github/workflows/ci.yaml` foi criado.
2.  Use o comando `cat .github/workflows/ci.yaml` para garantir que o conteúdo é idêntico ao fornecido.

---

### Passo 2: Arquivar Documentação de Gestão Interna

**Objetivo:** Mover a pasta `project-management`, que contém documentos internos, para um local de arquivo morto e garantir que ela não seja rastreada pelo Git.

**Ação 1:** Renomeie a pasta `project-management` para `project-management-archive` usando o comando `git mv`. Isso preserva o histórico do Git, o que é preferível a um `mv` simples.

**Comando:**
```bash
git mv project-management/ project-management-archive/
```

**Ação 2:** Adicione o novo diretório de arquivo morto ao `.gitignore` para evitar que ele seja incluído em futuros commits.

**Comando:**
```bash
echo "project-management-archive/" >> .gitignore
```

**Verificação:**
1.  Execute `ls` e confirme que a pasta `project-management/` não existe mais.
2.  Confirme que a pasta `project-management-archive/` existe.
3.  Execute `tail -n 1 .gitignore` e verifique se a última linha é `project-management-archive/`.

---

### Passo 3: Reescrever o README.md Principal

**Objetivo:** Simplificar e focar o `README.md` para fornecer a melhor experiência possível para um novo usuário que acaba de encontrar o projeto.

**Ação:** Substitua todo o conteúdo do arquivo `README.md` pela versão aprimorada abaixo.

**Novo Conteúdo para `README.md`:**
```markdown
# 🎼 Conductor: The AI-Powered Orchestration Framework

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/cezarfuhr/conductor/actions/workflows/ci.yaml/badge.svg)](https://github.com/cezarfuhr/conductor/actions/workflows/ci.yaml)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)]()

**Conductor is an AI ecosystem that turns dialogue into production-ready code through interactive and orchestrated agents.**

---

## 🚀 What is this?

Conductor is a multi-agent framework for AI-assisted development. It allows you to create, manage, and orchestrate specialized AI agents that can reason, plan, and execute complex coding tasks by interacting with your codebase. It's designed to be a robust platform for building automated development workflows.

## 🏁 Getting Started

### Using Docker (Recommended)

The easiest way to get started is with Docker.

```bash
# This will build the image, install dependencies, and start the services.
docker-compose up --build
```

### Local Python Environment

1.  **Prerequisites:** Python 3.8+ and [Poetry](https://python-poetry.org/docs/#installation).
2.  **Setup:**
    ```bash
    git clone https://github.com/cezarfuhr/conductor.git
    cd conductor
    poetry install
    cp .env.example .env
    # Add your API keys to the .env file
    ```

## ⚙️ How to Use

The primary way to use Conductor is through its CLI.

1.  **Configure a Workspace:** Edit `config/workspaces.yaml` to map a name to your project's directory.
    ```yaml
    workspaces:
      default: /path/to/your/projects
    ```

2.  **Run an Agent:** Start an interactive session with an agent.
    ```bash
    # Example:
    poetry run python src/cli/agent.py --environment default --project my-cool-project --agent CodeGenerator_Agent
    ```

## 📚 Learn More

-   **[Full Documentation](docs/README.md):** Dive deeper into Conductor's architecture and features.
-   **[Configuration Guide](docs/guides/configuration.md):** Learn how to configure workspaces, AI providers, and workflows.
-   **[Agent Design Patterns](docs/guides/AGENT_DESIGN_PATTERNS.md):** Best practices for creating effective agents.

## 🤝 Contributing

We welcome contributions! Please read our **[Contributing Guide](CONTRIBUTING.md)** to get started. Also, be sure to review our **[Code of Conduct](CODE_OF_CONDUCT.md)**.

---

**🎼 Conductor** - Orchestrating dialogue, transforming ideas into code.
```

**Verificação:**
1.  Use `cat README.md` e confirme que seu conteúdo é idêntico ao fornecido acima.

---

**Fim do Plano. Reporte a conclusão bem-sucedida de todos os passos.**
