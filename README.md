# 🎼 Conductor & Maestro Framework

> **Um ecossistema de IA que transforma o diálogo em código de produção, de forma interativa e orquestrada.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🚀 Visão Geral

Este repositório contém uma arquitetura de múltiplos executores que trabalham em harmonia para fornecer uma plataforma robusta de automação e desenvolvimento assistido por IA.

1.  **`admin.py` (Executor Administrativo):** Uma interface de linha de comando para executar **meta-agentes**. É o ponto de partida do framework, usado para tarefas de gerenciamento como a criação de novos agentes (`AgentCreator_Agent`).

2.  **`genesis_agent.py` (Executor de Projeto):** Uma interface de linha de comando para executar os **agentes de projeto** que você criou. Estes agentes operam sobre bases de código externas, realizando as tarefas de análise e codificação.

3.  **`run_conductor.py` (Motor de Orquestração):** Um motor de execução **não-interativo e automatizado**. Ele interpreta arquivos de workflow (`.yaml`) para orquestrar sequências complexas de tarefas envolvendo múltiplos agentes, ideal para automação e CI/CD.

### ✨ Funcionalidades Chave

- 💬 **Sessões Interativas com Agentes:** Dialogue com IAs especialistas para refinar ideias.
- 🤖 **Multi-Provedor de IA:** Suporte para Claude e Gemini, configurável por agente.
- 📂 **Arquitetura Orientada a Ambientes:** Gerencie e opere de forma segura em múltiplos projetos e ambientes (`develop`, `main`, etc.), garantindo que um agente de desenvolvimento não acesse o ambiente de produção.
- 🛠️ **Sistema de Ferramentas com Escopo de Escrita:** Agentes podem interagir com o sistema de arquivos, mas as operações de escrita são estritamente controladas pela configuração `output_scope` do agente, prevenindo modificações acidentais.
- 🧬 **Metaprogramação:** Capacidade de criar e gerenciar agentes usando o `AgentCreator_Agent` através do executor `admin.py`.
- 📋 **Execução Baseada em Planos:** Orquestração automatizada de tarefas de codificação a partir de um plano YAML.
- 🔒 **Segurança e Confiabilidade:** Confirmação humana para operações de escrita em modo interativo e políticas de segurança estritas para execução automatizada.

## ⚙️ Configuração Inicial: Mapeando Seus Projetos

Antes de usar o framework, você precisa informar onde os seus projetos residem. Isso é feito no arquivo `config/workspaces.yaml`. Este arquivo mapeia um nome de ambiente (como `develop`) para um caminho absoluto no seu sistema de arquivos, permitindo que o Conductor encontre e interaja com suas bases de código.

**Exemplo de `config/workspaces.yaml`:**
```yaml
# config/workspaces.yaml
workspaces:
  # Mapeia o ambiente 'develop' para um diretório específico
  develop: /home/user/projetos/desenvolvimento
  
  # Mapeia o ambiente 'main' para outro diretório
  main: /home/user/projetos/producao
```

## Workflow Principal

O uso do framework segue um fluxo lógico de criar, e depois executar os agentes.

### Passo 1: Criar um Agente (`admin.py`)

Para qualquer nova tarefa, o primeiro passo é criar um agente especialista para ela. Isso é feito usando o `AgentCreator_Agent` através do executor administrativo.

**Sintaxe:**
```bash
# Inicia o criador de agentes em modo interativo para configurar um novo agente
python scripts/admin.py --agent AgentCreator_Agent --repl
```

### Passo 2: Executar o Agente (`genesis_agent.py`)

Uma vez que seu agente foi criado, você pode executá-lo para interagir com a base de código do seu projeto.

**Sintaxe:**
```bash
python scripts/genesis_agent.py --environment <env> --project <proj> --agent <agent_id> [opções]
```
- `--environment`: **(Obrigatório)** O ambiente de destino (ex: `develop`), conforme definido em `config/workspaces.yaml`.
- `--project`: **(Obrigatório)** O nome do projeto alvo (ex: `your-project-name`).
- `--agent`: **(Obrigatório)** O ID do agente a ser executado.

**Modos de Execução:**

| Modo | Comando Adicional | Descrição | Caso de Uso |
| :--- | :--- | :--- | :--- |
| **Conversacional** | `--repl` | Inicia uma sessão de chat interativa com o agente. | Design, análise, depuração. |
| **Comando Único** | `--input "<prompt>"` | Executa um único turno com o agente de forma não-interativa. | Scripting, consultas rápidas. |

### (Avançado) Passo 3: Orquestrar Agentes (`run_conductor.py`)

Para automação complexa, você pode usar o motor de orquestração para executar um plano (`.yaml`) que define uma sequência de tarefas para múltiplos agentes.

**Sintaxe:**
```bash
python scripts/run_conductor.py --plan <caminho_para_o_plano.yaml>
```

## 📁 Estrutura de Diretórios

```
conductor/
├── 📚 docs/
├── 🚀 scripts/
│   ├── genesis_agent.py       # Executor de AGENTES DE PROJETO
│   ├── admin.py               # Executor de AGENTES ADMIN
│   └── run_conductor.py       # Motor de ORQUESTRAÇÃO
├── 🔧 projects/
│   ├── _common/
│   │   └── agents/
│   │       └── AgentCreator_Agent/ # Meta-agentes residem aqui
│   └── <ambiente>/            # Ex: develop, main
│       └── <projeto>/         # Ex: your-project-name
│           └── agents/
│               └── <agent_id>/  # Agentes de projeto residem aqui
└── ...
```

## 📚 Documentação Arquitetural

Nossa arquitetura é projetada para ser robusta, escalável e segura. Para entender completamente o design e as melhores práticas, consulte nossos documentos principais:

- **[📖 Especificação Arquitetural "Maestro"](docs/GEMINI_ARCH_SPEC.md)**: O blueprint da nossa arquitetura de agentes.
- **[🚀 Design Técnico do Genesis](docs/GENESIS_TECHNICAL_DESIGN.md)**: Arquitetura detalhada do motor interativo.
- **[Guia de Onboarding de Projetos](docs/ONBOARDING_NEW_PROJECT.md)**: Guia para integrar um novo projeto.
- **[Guia de Design de Agentes](docs/AGENT_DESIGN_PATTERNS.md)**: Melhores práticas para criar novos agentes.

---

**🎼 Conductor & Maestro** - Orquestrando o diálogo e transformando ideias em código.
