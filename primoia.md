# Conductor

Framework multi-agente que transforma dialogo em codigo production-ready atraves de agentes de IA especializados e orquestrados com execucao baseada em planos YAML.

## Responsabilidades
- Criar e gerenciar agentes de IA especializados (CodeReviewer, TestGenerator, DocWriter)
- Executar workflows complexos definidos em planos YAML
- Manter sessoes interativas com historico persistente de conversas
- Gerenciar ambientes isolados com acesso controlado ao file system

## Stack
- Python 3.8+
- MongoDB (storage de agentes/conversas/planos)
- Pydantic + PyYAML
- Multi-provider AI (Gemini, Claude, Cursor Agent)
