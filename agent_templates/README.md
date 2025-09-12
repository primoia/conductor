# Agent Templates

Este diretório contém templates de agentes organizados por categoria. Os templates são versionados no Git e podem ser instalados rapidamente pelos usuários.

## 📁 Estrutura

```
agent_templates/
├── core_tools/           # Ferramentas essenciais do Conductor
├── web_development/      # Desenvolvimento web (React, Angular, etc.)
├── backend_development/  # Desenvolvimento backend (APIs, databases, etc.)
├── data_science/         # Ciência de dados e análise
├── devops/              # DevOps e infraestrutura
└── mobile_development/   # Desenvolvimento mobile
```

## 🚀 Como Usar

### Listar Templates Disponíveis
```bash
./conductor install --list
```

### Instalar Categoria Completa
```bash
./conductor install --category core_tools
./conductor install --category web_development
./conductor install --category backend_development
```

### Instalar Agente Específico
```bash
./conductor install --agent AgentCreator_Agent
./conductor install --agent ReactExpert_Agent
```

## 📋 Categorias Disponíveis

### 🛠️ Core Tools
Ferramentas essenciais para qualquer desenvolvedor:
- **AgentCreator_Agent**: Cria novos agentes
- **CommitMessage_Agent**: Gera mensagens de commit padronizadas
- **CodeReviewer_Agent**: Revisa qualidade de código
- **DocWriter_Agent**: Escreve documentação técnica
- **SystemGuide_Meta_Agent**: Explica arquitetura do sistema

### 🌐 Web Development
Especialistas em desenvolvimento frontend:
- **ReactExpert_Agent**: Expert em React, hooks, state management
- **AngularExpert_Agent**: Expert em Angular, TypeScript, RxJS, NgRx

### 🔧 Backend Development
Especialistas em desenvolvimento backend:
- **APIArchitect_Agent**: Design de APIs REST e GraphQL
- **DatabaseExpert_Agent**: Design e otimização de bancos de dados
- **SecuritySpecialist_Agent**: Segurança de aplicações
- **PerformanceOptimizer_Agent**: Otimização de performance
- **TestingSpecialist_Agent**: Estratégias de teste abrangentes

### 📊 Data Science
Especialistas em análise de dados:
- **DataAnalyst_Agent**: Análise de dados com Python/R

### 🚀 DevOps
*Em desenvolvimento*

### 📱 Mobile Development
*Em desenvolvimento*

## 🔧 Estrutura de um Template

Cada template de agente contém:

```
AgentName_Agent/
├── definition.yaml    # Configuração do agente
└── persona.md        # Conhecimento e comportamento
```

### definition.yaml
```yaml
name: "AgentName_Agent"
version: "1.0.0"
schema_version: "1.0"
description: "Descrição do que o agente faz"
author: "Conductor Templates"
type: "project"
tags: ["tag1", "tag2", "tag3"]
capabilities: ["capability1", "capability2"]
allowed_tools: ["tool1", "tool2"]
```

### persona.md
Arquivo markdown com:
- Expertise do agente
- Princípios e guidelines
- Formato de resposta
- Exemplos de código
- Ferramentas e tecnologias

## 📝 Contribuindo

Para adicionar novos templates:

1. Crie o diretório na categoria apropriada
2. Adicione `definition.yaml` e `persona.md`
3. Teste o template localmente
4. Faça commit das mudanças

### Exemplo de Contribuição
```bash
# Criar novo template
mkdir -p agent_templates/web_development/VueExpert_Agent

# Criar arquivos
touch agent_templates/web_development/VueExpert_Agent/definition.yaml
touch agent_templates/web_development/VueExpert_Agent/persona.md

# Testar
./conductor install --agent VueExpert_Agent
./conductor execute --agent VueExpert_Agent --input "teste"
```

## 🎯 Benefícios dos Templates

- **Onboarding Rápido**: Instale agentes especializados instantaneamente
- **Qualidade Garantida**: Templates testados e otimizados
- **Padronização**: Estrutura consistente entre agentes
- **Versionamento**: Evolução controlada dos templates
- **Compartilhamento**: Comunidade pode contribuir com novos templates

## 💡 Dicas

- Use `--list` para explorar templates disponíveis
- Instale categorias completas para ter um toolkit abrangente
- Templates são copiados para `.conductor_workspace/agents/` quando instalados
- Agentes instalados podem ser personalizados localmente
- Templates originais permanecem inalterados