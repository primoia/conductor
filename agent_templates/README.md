# Agent Templates

This directory contains agent templates organized by category. The templates are versioned in Git and can be quickly installed by users.

## 📁 Structure

```
agent_templates/
├── core_tools/           # Essential Conductor tools
├── web_development/      # Web development (React, Angular, etc.)
├── backend_development/  # Backend development (APIs, databases, etc.)
├── data_science/         # Data science and analysis
├── portfolio/            # Portfolio and career development
├── devops/              # DevOps and infrastructure
└── mobile_development/   # Mobile development
```

## 🚀 How to Use

### List Available Templates
```bash
conductor install --list
```

### Install Complete Category
```bash
conductor install --category core_tools
conductor install --category web_development
conductor install --category backend_development
```

### Install Specific Agent
```bash
conductor install --agent AgentCreator_Agent
conductor install --agent ReactExpert_Agent
```

## 📋 Available Categories

### 🛠️ Core Tools
Essential tools for any developer:
- **AgentCreator_Agent**: Creates new agents
- **CommitMessage_Agent**: Generates standardized commit messages
- **CodeReviewer_Agent**: Reviews code quality
- **DocWriter_Agent**: Writes technical documentation
- **SystemGuide_Meta_Agent**: Explains system architecture

### 🌐 Web Development
Frontend development specialists:
- **ReactExpert_Agent**: Expert in React, hooks, state management
- **AngularExpert_Agent**: Expert in Angular, TypeScript, RxJS, NgRx

### 🔧 Backend Development
Backend development specialists:
- **APIArchitect_Agent**: Design of REST and GraphQL APIs
- **DatabaseExpert_Agent**: Database design and optimization
- **SecuritySpecialist_Agent**: Application security
- **PerformanceOptimizer_Agent**: Performance optimization
- **TestingSpecialist_Agent**: Comprehensive testing strategies

### 📊 Data Science
Data analysis specialists:
- **DataAnalyst_Agent**: Data analysis with Python/R

### 📁 Portfolio
Career and portfolio development:
- **PortfolioAssistant_Agent**: Professional portfolio creation and management

### 🚀 DevOps
*Under development*

### 📱 Mobile Development
*Under development*

## 🔧 Template Structure

Each agent template contains:

```
AgentName_Agent/
├── definition.yaml    # Agent configuration
└── persona.md        # Knowledge and behavior
```

### definition.yaml
```yaml
name: "AgentName_Agent"
version: "1.0.0"
schema_version: "1.0"
description: "Description of what the agent does"
author: "Conductor Templates"
type: "project"
tags: ["tag1", "tag2", "tag3"]
capabilities: ["capability1", "capability2"]
allowed_tools: ["tool1", "tool2"]
```

### persona.md
Markdown file with:
- Agent expertise
- Principles and guidelines
- Response format
- Code examples
- Tools and technologies

## 📝 Contributing

To add new templates:

1. Create the directory in the appropriate category
2. Add `definition.yaml` and `persona.md`
3. Test the template locally
4. Commit the changes

### Example Contribution
```bash
# Create new template
mkdir -p agent_templates/web_development/VueExpert_Agent

# Create files
touch agent_templates/web_development/VueExpert_Agent/definition.yaml
touch agent_templates/web_development/VueExpert_Agent/persona.md

# Test
conductor install --agent VueExpert_Agent
conductor execute --agent VueExpert_Agent --input "test"
```

## 🎯 Template Benefits

- **Fast Onboarding**: Install specialized agents instantly
- **Guaranteed Quality**: Tested and optimized templates
- **Standardization**: Consistent structure across agents
- **Versioning**: Controlled evolution of templates
- **Sharing**: The community can contribute new templates

## 💡 Tips

- Use `--list` to explore available templates
- Install complete categories for a comprehensive toolkit
- Templates are copied to `.conductor_workspace/agents/` when installed
- Installed agents can be customized locally
- Original templates remain unchanged