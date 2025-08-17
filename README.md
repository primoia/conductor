# 🎼 Conductor & Maestro Framework

> **Um ecossistema de IA que transforma o diálogo em código de produção, de forma interativa e orquestrada.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🚀 Visão Geral

Este repositório contém uma arquitetura de múltiplos executores que trabalham em harmonia para fornecer uma plataforma robusta de automação e desenvolvimento assistido por IA.

1.  **`genesis_agent.py` (Executor de Projeto):** Uma interface de linha de comando para executar **agentes de projeto**. Estes agentes são projetados para operar sobre bases de código externas, realizando tarefas de análise, modificação e geração de código dentro de um escopo seguro e definido.

2.  **`admin.py` (Executor Administrativo):** Uma interface de linha de comando para executar **meta-agentes**. Estes agentes realizam tarefas de gerenciamento no próprio framework, como a criação de novos agentes (`AgentCreator_Agent`).

3.  **`run_conductor.py` (Motor de Orquestração):** Um motor de execução **não-interativo e automatizado**. Ele interpreta arquivos de workflow (`.yaml`) para orquestrar sequências complexas de tarefas envolvendo múltiplos agentes, ideal para automação e CI/CD.

### ✨ Funcionalidades Chave

- 💬 **Sessões Interativas com Agentes:** Dialogue com IAs especialistas para refinar ideias.
- 🤖 **Multi-Provedor de IA:** Suporte para Claude e Gemini, configurável por agente.
- 📂 **Suporte Multi-Projeto e Multi-Ambiente:** Gerencie e opere em múltiplos projetos de forma segura e contextualizada.
- 🛠️ **Sistema de Ferramentas (Poderes Especiais):** Agentes podem ler arquivos, executar comandos e interagir com o sistema de forma segura.
- 🆕 **Framework de Agentes v2.1:** Sistema padronizado com comandos help, preview e versionamento incremental.
- 📋 **Saída Parametrizada:** Configuração flexível de arquivos gerados por cada agente.
- 🔄 **Versionamento Incremental:** Mesclagem automática de conversas com preservação de contexto.
- 🧬 **Metaprogramação:** Capacidade de criar novos agentes usando o `AgentCreator_Agent`.
- 📋 **Execução Baseada em Planos:** Orquestração automatizada de tarefas de codificação a partir de um plano YAML.
- 🧠 **Aprendizado Contínuo e Conhecimento Negativo:** Agentes aprendem com o sucesso e o fracasso, evitando repetir erros passados.
- 🔒 **Segurança e Confiabilidade de Nível Empresarial:** Validação robusta de templates, rollback automático e gerenciamento seguro de comandos shell.
- ⚙️ **Flexibilidade Avançada com Deep Merge:** Personalização de configurações de agentes através de fusão profunda de templates.

## 📁 Estrutura de Diretórios (v2.0)

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

## 📁 Arquitetura de Execução (v2.0)

A versão 2.0 introduz uma separação clara de responsabilidades entre os executores para aumentar a segurança e a clareza.

### 1. Executando Agentes de Projeto (`genesis_agent.py`)

Use este executor para interagir com agentes que leem ou modificam uma base de código externa.

**Sintaxe:**
```bash
python scripts/genesis_agent.py --environment <env> --project <proj> --agent <agent_id> [opções]
```
- `--environment`: **(Obrigatório)** O ambiente de destino (ex: `develop`, `main`), conforme definido em `config/workspaces.yaml`.
- `--project`: **(Obrigatório)** O nome do projeto alvo (ex: `your-project-name`).
- `--agent`: **(Obrigatório)** O ID do agente a ser executado.

**Modos de Execução:**

| Modo | Comando Adicional | Descrição | Caso de Uso |
| :--- | :--- | :--- | :--- |
| **Conversacional** | `--repl` | Inicia uma sessão de chat interativa com o agente. | Design, análise, depuração. |
| **Comando Único** | `--input "<prompt>"` | Executa um único turno com o agente de forma não-interativa. | Scripting, consultas rápidas. |

### 2. Executando Agentes Administrativos (`admin.py`)

Use este executor para tarefas de gerenciamento do próprio framework, como criar novos agentes.

**Sintaxe:**
```bash
python scripts/admin.py --agent <meta_agent_id> [opções]
```
- `--agent`: **(Obrigatório)** O ID do meta-agente a ser executado (ex: `AgentCreator_Agent`).

**Exemplo (Criando um novo agente):**
```bash
# Inicia o criador de agentes em modo interativo para configurar um novo agente
python scripts/admin.py --agent AgentCreator_Agent --repl
```

### 3. Workflows Automatizados (`run_conductor.py`)

Use este motor para execuções não-interativas de múltiplos agentes a partir de um plano.

**Sintaxe:**
```bash
python scripts/run_conductor.py --plan <caminho_para_o_plano.yaml>
```

##  migrating-v1-agents-to-v2 Migração de Agentes (v1 -> v2)

Para atualizar agentes legados para a nova estrutura, utilize o script de migração. Ele irá guiá-lo no processo de adicionar as configurações de `environment`, `project_key` e `output_scope`.

```bash
python scripts/migrate_agents_v2.py
```

## 📚 Documentação Arquitetural

Nossa arquitetura é projetada para ser robusta, escalável e segura. Para entender completamente o design e as melhores práticas, consulte nossos documentos principais:

- **[📖 Especificação Arquitetural "Maestro"](docs/GEMINI_ARCH_SPEC.md)**: O blueprint da nossa arquitetura de agentes.
- **[🚀 Design Técnico do Genesis](docs/GENESIS_TECHNICAL_DESIGN.md)**: Arquitetura detalhada do motor interativo.
- **[Guia de Onboarding de Projetos](docs/ONBOARDING_NEW_PROJECT.md)**: Guia para integrar um novo projeto.
- **[Guia de Design de Agentes](docs/AGENT_DESIGN_PATTERNS.md)**: Melhores práticas para criar novos agentes.
- **[Framework de Agentes v2.1](project-management/agent-framework-patterns/)**: Documentação do sistema padronizado de agentes.



## 📊 Métricas e Performance

- ⚡ **Execução Otimizada**: Tempo de execução e sucesso otimizados pela seleção dinâmica de IA.
- 🔒 **Robustez Comprovada**: Sistema resiliente a falhas e seguro contra entradas maliciosas.
- 🔄 **Paralelização**: Suporte para execução paralela de tarefas.

## 🙏 Agradecimentos

- **Comunidade de IA** pelas ferramentas e modelos incríveis.
- **Inspiração:** O projeto `.bmad-core` serviu como inspiração inicial para a definição de agentes baseada em arquivos, que evoluiu para o Framework Maestro.

---

**🎼 Conductor & Maestro** - Orquestrando o diálogo e transformando ideias em código.