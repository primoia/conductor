# 🎼 Conductor: The AI-Powered Orchestration Framework

> **Conductor is an AI ecosystem that turns dialogue into production-ready code through interactive and orchestrated agents.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)]()

---

## 🚀 Overview

Conductor is a multi-agent framework designed to provide a robust platform for AI-assisted development and automation. It allows you to create, manage, and orchestrate specialized AI agents that can reason, plan, and execute complex coding tasks by interacting with your codebase.

```
+-----------+        +-------------------+        +----------------+
|           |        |                   |        |                |
|  Developer|--💬-->|     Conductor     |--⚙️-->|    Agents      |
|           | Dialogue   |  (Orchestrator)   | Orchestrates| (Database, Coder)|
+-----------+        |                   |        |                |
                     +---------+---------+        +-------+--------+
                               |                          |
                               | Analysis & Planning      | Execution
                               |                          |
                               ▼                          ▼
                     +------------------------------------------+
                     |                                          |
                     |               Codebase                   |
                     |                                          |
                     +------------------------------------------+
```

-   **Orchestrate Complex Workflows:** Define multi-step plans in simple YAML files and let Conductor execute them automatically.
-   **Interact with Specialist Agents:** Dialogue with AI agents that have access to your code, enabling a conversational approach to development.
-   **Multi-Provider Support:** Flexibly switch between different AI providers like Gemini and Claude for each agent.
-   **Safe & Secure:** Agents operate in a secure environment with scoped file system access and human-in-the-loop confirmations for critical operations.

## ✨ Key Features

-   💬 **Interactive Sessions:** Engage in conversations with AI agents to refine ideas and co-create solutions.
-   🤖 **Multi-Provider AI:** Configure different AI models for different agents to leverage the best tool for the job.
-   📂 **Environment-Oriented Architecture:** Safely manage and operate on multiple projects and environments.
-   🛠️ **Scoped Tool System:** Grant agents secure and controlled access to the file system.
-   🧬 **Metaprogramming:** Use agents to create and manage other agents, enabling a self-improving system.
-   📋 **Plan-Based Execution:** Automate complex coding tasks by defining a sequence of steps in a YAML workflow.

### 💡 A Practical Example

**The traditional way:** To add a field to a database entity, you need to:
1.  Write the database migration.
2.  Change the entity class in the code.
3.  Update the DTO (Data Transfer Object).
4.  Expose the new field in the API.
5.  Update the tests.

**With Conductor:** You simply instruct the agent:
> *"Add a 'last_login' date field to the User entity, including the database migration, DTO, and API endpoint."*

Conductor then orchestrates the specialist agents needed to execute all steps automatically.

### 👥 Who is Conductor for?
- **Developers & Agile Teams** who want to accelerate development and automate repetitive coding tasks.
- **DevOps Engineers** looking to automate the configuration and maintenance of infrastructure as code.
- **AI Enthusiasts** who want a robust platform to build and experiment with multi-agent systems.

## Getting Started

O Conductor agora opera sob uma arquitetura unificada e orientada a serviços. Toda a configuração é centralizada no arquivo `config.yaml` na raiz do projeto.

### 1. Configuração

Antes de rodar qualquer agente, configure seu ambiente no `config.yaml`:

```yaml
# config.yaml
storage:
  type: filesystem
  path: .conductor_workspace

# Adicione aqui diretórios para suas ferramentas customizadas
tool_plugins:
  - custom_tools/
```

-   **storage**: Define onde os dados dos agentes são armazenados.
    -   `filesystem`: (Padrão) Ideal para desenvolvimento local, não requer dependências.
    -   `mongodb`: Para ambientes de equipe ou produção.
-   **tool_plugins**: Lista de diretórios onde o Conductor irá procurar por ferramentas customizadas.

### 2. Executando Agentes

Embora estejamos caminhando para um CLI unificado, você ainda pode usar os CLIs `admin.py` e `agent.py`. Eles agora operam como interfaces para o novo serviço central e respeitam o `config.yaml`.

**Para Meta-Agentes:**
```bash
poetry run python src/cli/admin.py --agent AgentCreator_Agent --input "Crie um novo agente para analisar logs."
```

**Para Agentes de Projeto:**
```bash
poetry run python src/cli/agent.py --environment develop --project desafio-meli --agent ProductAnalyst_Agent --input "Analise os dados de produtos."
```

> **Nota:** Todos os agentes são armazenados em `.conductor_workspace/agents/` independentemente do tipo.

## Como Usar o Conductor

### 🚀 CLI Unificado (Recomendado)

O Conductor possui um CLI unificado que simplifica todas as operações:

#### **Executando Comandos**

```bash
# Opção 1: Script executável (mais fácil)
./conductor <comando>

# Opção 2: Via Python (sempre funciona)
python src/cli/conductor.py <comando>
```

#### **Comandos Principais**

##### 📋 **Listar Agentes Disponíveis**
```bash
./conductor list-agents
```
Mostra todos os agentes disponíveis com suas capacidades e tags.

##### 🤖 **Executar um Agente**
```bash
# Sintaxe básica
./conductor execute --agent <agent_id> --input "<sua_mensagem>"

# Com timeout personalizado (em segundos)
./conductor execute --agent <agent_id> --input "<sua_mensagem>" --timeout 300

# Exemplos práticos
./conductor execute --agent SystemGuide_Meta_Agent --input "Explique a arquitetura do sistema"
./conductor execute --agent CommitMessage_Agent --input "Gere mensagem de commit para as mudanças atuais"
./conductor execute --agent AgentCreator_Agent --input "Crie um agente para revisar código Python"

# Para tarefas complexas que precisam de mais tempo
./conductor execute --agent APIArchitect_Agent --input "Projete uma API completa" --timeout 300
```

##### 🔍 **Informações Detalhadas de um Agente**
```bash
./conductor info --agent <agent_id>

# Exemplo
./conductor info --agent SystemGuide_Meta_Agent
```
Mostra informações completas: capacidades, tags, arquivos, estatísticas e status.

##### ✅ **Validar Configuração**
```bash
./conductor validate-config
```
Verifica se a configuração está correta, agentes são válidos e o sistema está funcionando.

### 🔧 CLIs Legados (Compatibilidade)

Os CLIs originais ainda funcionam para compatibilidade:

#### **Admin CLI (Meta-Agentes)**
```bash
# Para agentes que gerenciam o framework
python src/cli/admin.py --agent <agent_id> --input "<mensagem>" --meta

# Exemplo
python src/cli/admin.py --agent AgentCreator_Agent --input "Crie um novo agente" --meta
```

#### **Agent CLI (Agentes de Projeto)**
```bash
# Para agentes específicos de projeto
python src/cli/agent.py --environment <env> --project <proj> --agent <agent_id> --input "<mensagem>"

# Exemplo
python src/cli/agent.py --environment develop --project meu-projeto --agent TestAgent --input "Execute testes"
```

### 🎯 Fluxo Típico de Uso

#### **1. Verificar Agentes Disponíveis**
```bash
./conductor list-agents
```

#### **2. Criar um Novo Agente (se necessário)**
```bash
./conductor execute --agent AgentCreator_Agent --input "Crie um agente para [sua necessidade]"
```

#### **3. Usar o Agente Criado**
```bash
./conductor execute --agent NovoAgente --input "Execute sua tarefa"
```

#### **4. Verificar Informações do Agente**
```bash
./conductor info --agent NovoAgente
```

### 🛠️ Exemplos Práticos

#### **Criar e Usar um Agente de Code Review**
```bash
# 1. Criar o agente
./conductor execute --agent AgentCreator_Agent --input "Crie um CodeReviewer_Agent para analisar qualidade de código Python"

# 2. Usar o agente criado
./conductor execute --agent CodeReviewer_Agent --input "Revise este código: def exemplo(): pass"

# 3. Ver informações do agente
./conductor info --agent CodeReviewer_Agent
```

#### **Gerar Mensagens de Commit**
```bash
./conductor execute --agent CommitMessage_Agent --input "Gere mensagem de commit para: adicionei validação de entrada e corrigir bug na autenticação"
```

#### **Obter Ajuda do Sistema**
```bash
./conductor execute --agent SystemGuide_Meta_Agent --input "Como funciona o sistema de agentes?"
```

### 🔧 Troubleshooting

#### **Comando não encontrado: `conductor`**
```bash
# Use o caminho completo
python src/cli/conductor.py list-agents

# Ou torne o script executável
chmod +x conductor
./conductor list-agents
```

#### **Agente não encontrado**
```bash
# Listar agentes disponíveis
./conductor list-agents

# O sistema sugere agentes similares automaticamente
./conductor execute --agent AgenteTeste --input "teste"
# Output: ❌ Agente 'AgenteTeste' não encontrado
#         💡 Agentes similares: TestAgent, SystemGuide_Meta_Agent
```

#### **Timeout em operações longas**
```bash
# Se o agente demorar muito (timeout padrão: 120s)
./conductor execute --agent MyAgent --input "tarefa complexa" --timeout 300

# Para tarefas muito complexas
./conductor execute --agent MyAgent --input "análise completa" --timeout 600
```

#### **Validar se tudo está funcionando**
```bash
./conductor validate-config
```

### 💡 Dicas Avançadas

- **Cache**: O sistema usa cache de 5 minutos para descoberta de agentes
- **Sugestões**: Quando um agente não é encontrado, o sistema sugere similares
- **Histórico**: Cada agente mantém histórico de conversas em `history.log`
- **Validação**: Use `validate-config` para diagnosticar problemas

## 🎯 Como Usar o Conductor

O Conductor oferece múltiplas formas de interagir com seus agentes. Aqui está um guia completo de como usar todas as funcionalidades disponíveis.

### 🚀 Métodos de Execução

#### 1. CLI Unificado (Recomendado)
```bash
# Executar diretamente
./conductor <comando> [opções]

# Ou via Python
python src/cli/conductor.py <comando> [opções]
```

#### 2. Usando Poetry (Recomendado para Desenvolvimento)
```bash
# Para comandos do conductor
poetry run python src/cli/conductor.py <comando> [opções]

# Para CLIs legados
poetry run python src/cli/admin.py [opções]
poetry run python src/cli/agent.py [opções]
```

### 📋 Comandos Principais

#### `list-agents` - Listar Agentes Disponíveis
```bash
# Listar todos os agentes
./conductor list-agents

# Exemplo de saída:
🤖 Agentes disponíveis em .conductor_workspace/agents/:
============================================================
 1. AgentCreator_Agent
     Nome: Agent Creator
     Capacidades: agent_creation, yaml_generation, code_analysis
     Tags: meta, creator, framework

 2. DocumentAnalyst_Agent  
     Nome: Document Analyst
     Capacidades: document_analysis, content_extraction, summarization
     Tags: analysis, documents, nlp

📊 Total: 15 agentes encontrados
```

#### `execute` - Executar um Agente
```bash
# Executar agente básico
./conductor execute --agent AgentCreator_Agent --input "Crie um novo agente para análise de logs"

# Executar com contexto de projeto
./conductor execute --agent DocumentAnalyst_Agent --environment develop --project my-project --input "Analise o arquivo README.md"

# Exemplo de saída:
🤖 Executando agente: DocumentAnalyst_Agent
==================================================
✅ Execução bem-sucedida:
[Resposta detalhada do agente...]
```

#### `info` - Informações Detalhadas do Agente
```bash
# Ver informações completas de um agente
./conductor info --agent AgentCreator_Agent

# Exemplo de saída:
🔍 Informações do agente: AgentCreator_Agent
============================================================
📋 INFORMAÇÕES BÁSICAS
   ID: AgentCreator_Agent
   Nome: Agent Creator
   Versão: 1.0.0
   Autor: Conductor Framework
   Descrição: Especialista em criação de novos agentes

🏷️  TAGS
   • meta
   • creator
   • framework

🛠️  CAPACIDADES
   • agent_creation
   • yaml_generation
   • code_analysis

🔧 FERRAMENTAS PERMITIDAS
   • file_operations
   • yaml_parser
   • code_generator
```

#### `validate-config` - Validar Configuração
```bash
# Verificar se tudo está configurado corretamente
./conductor validate-config

# Exemplo de saída:
🔍 Validando configuração do Conductor...
============================================================
📋 1. Validando arquivo de configuração...
   ✅ config.yaml carregado com sucesso

💾 2. Validando configuração de storage...
   Tipo: filesystem
   Caminho: .conductor_workspace
   ✅ Diretório base existe
   ✅ Permissões de escrita OK

🤖 3. Validando diretório de agentes...
   ✅ Diretório existe: .conductor_workspace/agents
   📊 Agentes encontrados: 15
```

### 🎭 Exemplos Práticos de Uso

#### Cenário 1: Criando um Novo Agente
```bash
# 1. Primeiro, valide sua configuração
./conductor validate-config

# 2. Liste agentes existentes para ver o que está disponível
./conductor list-agents

# 3. Use o AgentCreator para criar um novo agente
./conductor execute --agent AgentCreator_Agent --input "Crie um agente especializado em análise de performance de APIs REST"

# 4. Verifique se o agente foi criado
./conductor list-agents
```

#### Cenário 2: Analisando um Projeto
```bash
# 1. Execute um agente de análise em um projeto específico
./conductor execute --agent ProjectAnalyst_Agent --environment production --project ecommerce --input "Analise a arquitetura atual do sistema"

# 2. Obtenha informações detalhadas sobre o agente usado
./conductor info --agent ProjectAnalyst_Agent
```

#### Cenário 3: Trabalhando com Documentação
```bash
# Execute um agente para analisar documentação
./conductor execute --agent DocumentAnalyst_Agent --input "Analise todos os arquivos README do projeto e gere um resumo"
```

### 🔧 CLIs Legados (Compatibilidade)

Embora recomendemos o uso do CLI unificado, os CLIs legados ainda estão disponíveis:

#### `admin.py` - Meta-Agentes
Para agentes que trabalham com o próprio framework Conductor:
```bash
# Criar novos agentes
poetry run python src/cli/admin.py --agent AgentCreator_Agent --input "Crie um agente para análise de logs"

# Gerenciar framework
poetry run python src/cli/admin.py --agent FrameworkManager_Agent --input "Atualize a configuração do sistema"

# Modo interativo (REPL)
poetry run python src/cli/admin.py --agent AgentCreator_Agent
# (Inicia sessão interativa)
```

#### `agent.py` - Agentes de Projeto
Para agentes que trabalham com projetos específicos:
```bash
# Análise de projeto específico
poetry run python src/cli/agent.py --environment develop --project my-app --agent CodeAnalyst_Agent --input "Analise a qualidade do código"

# Com contexto de ambiente
poetry run python src/cli/agent.py --environment production --project ecommerce --agent SecurityAuditor_Agent --input "Faça uma auditoria de segurança"

# Modo interativo
poetry run python src/cli/agent.py --environment develop --project my-app --agent CodeAnalyst_Agent
```

### 🔨 Como Criar Novos Agentes

#### Método 1: Usando o AgentCreator_Agent (Recomendado)
```bash
# Criação assistida de agente
./conductor execute --agent AgentCreator_Agent --input "Crie um agente para análise de performance de banco de dados com as seguintes capacidades: query_analysis, index_optimization, performance_monitoring"
```

#### Método 2: Criação Manual
```bash
# 1. Crie o diretório do agente
mkdir -p .conductor_workspace/agents/MyNewAgent_Agent

# 2. Crie o arquivo de definição
cat > .conductor_workspace/agents/MyNewAgent_Agent/definition.yaml << 'EOF'
name: "My New Agent"
version: "1.0.0"
author: "Seu Nome"
description: "Descrição do que o agente faz"
capabilities:
  - capability1
  - capability2
tags:
  - tag1
  - tag2
allowed_tools:
  - file_operations
  - web_search
EOF

# 3. Crie o arquivo de persona
cat > .conductor_workspace/agents/MyNewAgent_Agent/persona.md << 'EOF'
# Persona: Seu Agente

## Descrição
Descrição detalhada do comportamento e especialização do agente.

## Instruções
- Instrução 1
- Instrução 2
- Instrução 3
EOF

# 4. Verifique se o agente foi criado corretamente
./conductor info --agent MyNewAgent_Agent
```

### 🚨 Troubleshooting Básico

#### Problema: Agente não encontrado
```bash
# ❌ Erro: Agente 'MinhaAgent' não encontrado
./conductor execute --agent MinhaAgent --input "test"

# ✅ Solução: Listar agentes disponíveis
./conductor list-agents

# ✅ Ou obter sugestões similares
./conductor info --agent MinhaAgent
```

#### Problema: Erro de configuração
```bash
# ✅ Sempre valide a configuração primeiro
./conductor validate-config

# Se houver problemas, verifique:
# 1. Se o arquivo config.yaml existe
# 2. Se o diretório .conductor_workspace tem permissões corretas
# 3. Se os agentes têm arquivos definition.yaml válidos
```

#### Problema: Permissões de arquivo
```bash
# ✅ Garanta que o executável conductor tem permissões
chmod +x conductor

# ✅ Verifique permissões do workspace
ls -la .conductor_workspace/
```

#### Problema: Dependências Python
```bash
# ✅ Instale dependências
poetry install

# ✅ Ative o ambiente virtual
poetry shell

# ✅ Execute com poetry
poetry run python src/cli/conductor.py list-agents
```

#### Problema: Agente não responde ou falha
```bash
# ✅ Verifique logs detalhados (se disponível)
./conductor execute --agent ProblematicAgent --input "test" --debug

# ✅ Verifique a estrutura do agente
./conductor info --agent ProblematicAgent

# ✅ Valide a definição do agente manualmente
cat .conductor_workspace/agents/ProblematicAgent/definition.yaml
```

### 💡 Dicas Avançadas

#### 1. **Uso de Variáveis de Ambiente**
```bash
# Configure variáveis para diferentes ambientes
export CONDUCTOR_ENV=development
./conductor execute --agent MyAgent --input "Analise o ambiente $CONDUCTOR_ENV"
```

#### 2. **Piping e Automação**
```bash
# Encadear comandos
./conductor list-agents | grep "Analyst" | head -5

# Usar em scripts bash
#!/bin/bash
for agent in $(./conductor list-agents | grep "Agent" | awk '{print $2}'); do
    echo "Verificando $agent..."
    ./conductor info --agent "$agent"
done
```

#### 3. **Contexto de Projeto Flexível**
```bash
# Use variáveis para projetos dinâmicos
PROJECT=$(basename $(pwd))
./conductor execute --agent ProjectAnalyst_Agent --project "$PROJECT" --input "Analise este projeto"
```

### 📊 Comandos de Referência Rápida

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `list-agents` | Lista todos os agentes | `./conductor list-agents` |
| `execute` | Executa um agente | `./conductor execute --agent MyAgent --input "texto"` |
| `info` | Mostra detalhes do agente | `./conductor info --agent MyAgent` |
| `validate-config` | Valida configuração | `./conductor validate-config` |

### 🔄 Migração dos CLIs Legados

Para migrar do uso dos CLIs legados para o CLI unificado:

```bash
# Antes (admin.py):
poetry run python src/cli/admin.py --agent AgentCreator_Agent --input "criar agente"

# Depois (conductor unificado):
./conductor execute --agent AgentCreator_Agent --input "criar agente"

# Antes (agent.py):
poetry run python src/cli/agent.py --environment dev --project app --agent CodeAnalyst_Agent --input "analisar"

# Depois (conductor unificado):
./conductor execute --agent CodeAnalyst_Agent --environment dev --project app --input "analisar"
```

## 📚 Documentation

-   **[Full Documentation](docs/README.md):** Dive deeper into Conductor's architecture, features, and guides.
-   **[Configuration Guide](docs/guides/configuration.md):** Learn how to configure workspaces, AI providers, and workflows.
-   **[Agent Design Patterns](docs/guides/AGENT_DESIGN_PATTERNS.md):** Best practices for creating effective agents.

## ❤️ Support Conductor

Conductor is an open-source project driven by passion and innovation. Your support helps us maintain the project, develop new features, improve documentation, and grow our community.

### Ways to Support:

-   **Become a GitHub Sponsor:** Support us with recurring contributions directly through GitHub.
    [![Sponsor](https://img.shields.io/github/sponsors/cezarfuhr?style=flat&label=Sponsor)](https://github.com/sponsors/cezarfuhr)
    *(You'll need to set up GitHub Sponsors on your profile.)*
-   **Buy Me a Coffee:** Make a one-time or recurring donation to support our work.
    [![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow.svg)](https://buymeacoffee.com/cezarfuhr)
-   **Direct Contributions:** For larger contributions or corporate partnerships, please reach out via our [Consulting & Advisory Services](project-management/CONSULTING.md) page.
-   **Spread the Word:** Star our repository, share it with your network, and use Conductor in your projects!

Thank you for being a part of our journey!

## 🤝 Contributing

We welcome contributions from the community! Please read our **[Contributing Guide](CONTRIBUTING.md)** to learn how you can get involved.

Also, be sure to review our **[Code of Conduct](CODE_OF_CONDUCT.md)** to understand our community standards.

---

**🎼 Conductor** - Orchestrating dialogue, transforming ideas into code.