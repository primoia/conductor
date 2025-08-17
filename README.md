# 🎼 Conductor & Maestro Framework

> **Um ecossistema de IA que transforma o diálogo em código de produção, de forma interativa e orquestrada.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🚀 Visão Geral

Este repositório contém uma arquitetura de múltiplos executores que trabalham em harmonia para fornecer uma plataforma robusta de automação e desenvolvimento assistido por IA.

1.  **`admin.py` (Executor Administrativo):** Uma interface de linha de comando para executar **meta-agentes**. É o ponto de partida do framework, usado para tarefas de gerenciamento como o onboarding de novos projetos ou a criação de agentes.

2.  **`genesis_agent.py` (Executor de Projeto):** Uma interface de linha de comando para executar os **agentes de projeto** que você criou. Estes agentes operam sobre bases de código externas, realizando as tarefas de análise e codificação.

3.  **`run_conductor.py` (Motor de Orquestração):** Um motor de execução **não-interativo e automatizado**. Ele interpreta arquivos de workflow (`.yaml`) para orquestrar sequências complexas de tarefas, ideal para automação e CI/CD.

### ✨ Funcionalidades Chave

- 💬 **Sessões Interativas com Agentes:** Dialogue com IAs especialistas para refinar ideias. [saiba mais](docs/features/interactive-sessions.md)
- 🤖 **Multi-Provedor de IA:** Suporte para Claude e Gemini, configurável por agente. [saiba mais](docs/features/multi-provider-ai.md)
- 📂 **Arquitetura Orientada a Ambientes:** Gerencie e opere de forma segura em múltiplos projetos e ambientes. [saiba mais](docs/features/environment-oriented-architecture.md)
- 🛠️ **Sistema de Ferramentas com Escopo de Escrita:** Agentes podem interagir com o sistema de arquivos de forma segura. [saiba mais](docs/features/scoped-tool-system.md)
- 🧬 **Metaprogramação:** Capacidade de criar e gerenciar agentes usando o `AgentCreator_Agent`. [saiba mais](docs/features/metaprogramming.md)
- 📋 **Execução Baseada em Planos:** Orquestração automatizada de tarefas de codificação a partir de um plano YAML. [saiba mais](docs/features/plan-based-execution.md)
- 🔒 **Segurança e Confiabilidade:** Confirmação humana e políticas de segurança para operações de escrita. [saiba mais](docs/features/security-and-reliability.md)

## 🏁 Como Começar

Siga estes passos para configurar e executar seu primeiro agente.

### Passo 1: Configurar o Ambiente (`workspaces.yaml`)

Antes de tudo, você precisa informar ao Conductor onde seus projetos residem. Isso é feito no arquivo `config/workspaces.yaml`, que mapeia um nome de ambiente (como `develop`) para um caminho absoluto no seu sistema.

**Exemplo:**
```yaml
# config/workspaces.yaml
workspaces:
  # Mapeia o ambiente 'develop' para um diretório específico
  develop: /home/user/projetos/desenvolvimento
  main: /home/user/projetos/producao
```

### Passo 2: Onboarding Guiado (`OnboardingGuide_Agent`)

Este é o ponto de partida recomendado. Um agente especialista irá guiá-lo em um processo conversacional para:
- Entender seu perfil e as necessidades do seu projeto.
- Recomendar e configurar um **Team Template** (uma equipe de agentes pré-configurada).
- Deixar seu ambiente pronto para o trabalho.

**Inicie o onboarding com o comando:**
```bash
python scripts/admin.py --agent OnboardingGuide_Agent --repl
```

### Passo 3: Executar um Agente de Projeto (`genesis_agent.py`)

Após o onboarding, você terá agentes prontos para serem executados no seu projeto.

**Sintaxe:**
```bash
python scripts/genesis_agent.py --environment <env> --project <proj> --agent <agent_id> --repl
```

---

### (Alternativa ao Passo 2) Criar um Agente Manualmente

Se você prefere criar um agente do zero em vez de usar o onboarding guiado, pode usar o `AgentCreator_Agent`.

```bash
# Inicia o criador de agentes em modo interativo
python scripts/admin.py --agent AgentCreator_Agent --repl
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

Para um mergulho profundo no design e nas melhores práticas, consulte nossos documentos principais:

- **[📖 Especificação Arquitetural "Maestro"](docs/GEMINI_ARCH_SPEC.md)**
- **[🚀 Design Técnico do Genesis](docs/GENESIS_TECHNICAL_DESIGN.md)**
- **[Guia de Onboarding de Projetos](docs/ONBOARDING_NEW_PROJECT.md)**
- **[Guia de Design de Agentes](docs/AGENT_DESIGN_PATTERNS.md)**

---

**🎼 Conductor & Maestro** - Orquestrando o diálogo e transformando ideias em código.