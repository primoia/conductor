# Conductor: AI-Powered Orchestration Framework

Project: conductor

## Contexto
Framework multi-agente que transforma diálogo em código production-ready através de agentes especializados e orquestrados. Permite criar, gerenciar e orquestrar agentes de IA que raciocinam, planejam e executam tarefas complexas de codificação interagindo diretamente com o codebase. Introduz o conceito de "plan-based execution" onde workflows complexos são definidos em YAML e executados automaticamente.

## Stack
- **Language**: Python 3.8+
- **Core Libraries**: Pydantic 2.11+ (validation), PyYAML 6.0+ (config)
- **Database**: MongoDB 4.3+ com PyMongo (storage de agentes/conversas/plans)
- **Logging**: python-json-logger (structured logging)
- **CLI**: prompt-toolkit 3.0+ (REPL interativo), Pygments 2.19+ (syntax highlighting)
- **AI Providers**: Suporte multi-provider (Gemini, Claude, Cursor Agent) configurável por agente
- **Architecture**: Environment-oriented com scoped file system access
- **Execution Modes**: Stateless (rápido, sem histórico), contextual (com histórico), interactive (REPL)

## Capacidades Principais
- **Multi-Agent System**: Crie e gerencie agentes especializados (CodeReviewer, TestGenerator, DocWriter, etc.) com diferentes AI models
- **Plan-Based Execution**: Workflows YAML com sequência de steps executados automaticamente (suporta parallel execution)
- **Interactive Sessions**: Diálogo conversacional com agentes via REPL, preservando contexto entre mensagens
- **Conversation Management**: Histórico persistente de conversas multi-agente com tracking de participantes e contexto markdown
- **AgentCreator Meta-Agent**: Agente que cria outros agentes (metaprogramming), gera configuração YAML a partir de descrição natural
- **Environment Management**: Isolamento de contexto por projeto, múltiplos environments simultâneos
- **Scoped Tools**: Sistema de ferramentas com acesso controlado ao file system (read, write, execute, search)
- **Template System**: Instalação de agent templates pré-configurados (web_development, portfolio, testing, etc.)
- **Stateless Execution**: Execução rápida sem overhead de histórico (ideal para CI/CD, automation)
- **Contextual Chat**: Conversas com histórico preservado, múltiplas rodadas de refinamento
- **Backup/Restore**: Sistema completo de backup de agentes e restauração
- **Storage Migration**: Migração filesystem ↔ MongoDB sem perda de dados
- **Validation System**: Validação de configuração, agentes e system health
- **CLI Completo**: Interface de linha de comando com autocomplete e syntax highlighting
