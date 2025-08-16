# 🎼 Conductor & Maestro Framework

> **Um ecossistema de IA que transforma o diálogo em código de produção, de forma interativa e orquestrada.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🚀 Visão Geral

Este repositório contém uma arquitetura de dois componentes principais que trabalham em harmonia:

1.  **Maestro Framework (via `genesis_agent.py`):** Uma interface de linha de comando **interativa e conversacional**. É aqui que o desenvolvedor (o "Maestro") colabora com Agentes de IA especialistas para analisar problemas, criar planos de implementação e até mesmo criar novos agentes. É o cérebro e o centro de design do ecossistema.

2.  **Conductor Engine (via `run_conductor.py`):** Um motor de execução **não-interativo e automatizado**. Ele pega os planos de implementação (`.yaml`) gerados pelo Maestro e os executa, orquestrando agentes para gerar, modificar e testar o código de forma massiva.

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

## 📁 Estrutura de Diretórios

```
conductor/
├── 📚 docs/                    # Documentação completa da arquitetura
├── 🚀 scripts/                # Scripts principais
│   ├── genesis_agent.py       # O motor INTERATIVO (Maestro)
│   └── run_conductor.py       # O motor AUTOMATIZADO (Conductor)
├── 🔧 projects/               # Definição dos agentes
│   ├── _common/               # (Futuro) Agentes compartilhados
│   └── <ambiente>/            # Ex: develop, main
│       └── <projeto>/         # Ex: nex-web-backend
│           └── agents/        # Agentes específicos para o projeto/ambiente
│               └── <agent_id>/  # Definição do agente (agent.yaml, etc)
└── ...
```

## 🚀 Guia Rápido

### Modo Interativo (Maestro)

Use este modo para analisar, planejar e depurar.

```bash
# Inicie uma sessão de chat com um agente, no contexto de um projeto
python scripts/genesis_agent.py --embody ProblemRefiner_Agent --project-root /path/to/your/project --repl
```

### Modo de Execução (Automático)

Use este modo para executar um plano de implementação já definido.

```bash
# Execute um plano de implementação para um projeto
python scripts/run_conductor.py --projeto /path/to/your/project implementation_plan.yaml
```

## 📚 Documentação Arquitetural

Nossa arquitetura é projetada para ser robusta, escalável e segura. Para entender completamente o design e as melhores práticas, consulte nossos documentos principais:

- **[📖 Especificação Arquitetural "Maestro"](docs/GEMINI_ARCH_SPEC.md)**: O blueprint da nossa arquitetura de agentes.
- **[🚀 Design Técnico do Genesis](docs/GENESIS_TECHNICAL_DESIGN.md)**: Arquitetura detalhada do motor interativo.
- **[Guia de Onboarding de Projetos](docs/ONBOARDING_NEW_PROJECT.md)**: Guia para integrar um novo projeto.
- **[Guia de Design de Agentes](docs/AGENT_DESIGN_PATTERNS.md)**: Melhores práticas para criar novos agentes.
- **[Framework de Agentes v2.1](project-management/agent-framework-patterns/)**: Documentação do sistema padronizado de agentes.

## 🔧 Configuração de Agentes

Cada agente é definido por um conjunto de arquivos, com o `agent.yaml` sendo o principal.

```yaml
# projects/<env>/<proj>/agents/<agent_id>/agent.yaml

id: MyAgent
version: 1.0
description: "Descrição da responsabilidade do agente."
ai_provider: 'claude' # 'claude' ou 'gemini'
persona_prompt_path: "persona.md"
state_file_path: "state.json"
available_tools: ["Read", "Write", "Grep", "Glob"]
execution_task: "Gere um documento (${output_artifact}) com..."

# Configuração de saída parametrizada
output_artifact: "output.md"
output_directory: "workspace/output"
```

### 🆕 Sistema de Comandos Interativos

Todos os agentes agora suportam comandos padronizados:

- **Help**: `help`, `ajuda`, `comandos`, `?` - Mostra comandos disponíveis
- **Preview**: `preview` - Visualiza documento sem salvar  
- **Geração**: `gerar documento` - Salva com versionamento incremental (v1.0 → v1.1...)

**Exemplo de uso:**
```bash
# Modo interativo
python scripts/genesis_agent.py --embody ProblemRefiner_Agent --repl

# No chat do agente:
help                    # Ver comandos disponíveis
preview                 # Visualizar documento
gerar documento         # Salvar com versionamento
```

## 📊 Métricas e Performance

- ⚡ **Execução Otimizada**: Tempo de execução e sucesso otimizados pela seleção dinâmica de IA.
- 🔒 **Robustez Comprovada**: Sistema resiliente a falhas e seguro contra entradas maliciosas.
- 🔄 **Paralelização**: Suporte para execução paralela de tarefas.

## 🙏 Agradecimentos

- **Comunidade de IA** pelas ferramentas e modelos incríveis.
- **Inspiração:** O projeto `.bmad-core` serviu como inspiração inicial para a definição de agentes baseada em arquivos, que evoluiu para o Framework Maestro.

---

**🎼 Conductor & Maestro** - Orquestrando o diálogo e transformando ideias em código.