# 🎼 Arquitetura do Conductor - Diagrama Visual

## Como eu vejo a arquitetura atual:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CAMADA DE INTERFACE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   admin.py      │    │   agent.py      │    │  conductor.py   │            │
│  │ (Meta-agents)   │    │ (Project agents)│    │  (Futuro CLI)   │            │
│  │                 │    │                 │    │                 │            │
│  │ • AgentCreator  │    │ • KotlinEntity  │    │ • CLI Unificado │            │
│  │ • Migrator      │    │ • TestGenerator │    │ • API REST      │            │
│  │ • HelpSystem    │    │ • ProblemRefiner│    │ • Web UI        │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
│  Nota: Todos os agentes são armazenados em .conductor_workspace/agents/        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            CAMADA DE SERVIÇO (CORE)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        ConductorService                                │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │   │
│  │  │   TaskDTO       │  │  AgentExecutor  │  │  TaskResultDTO  │        │   │
│  │  │   (Input)       │  │   (Execution)   │  │   (Output)      │        │   │
│  │  │                 │  │                 │  │                 │        │   │
│  │  │ • agent_id      │  │ • LLM Client    │  │ • status        │        │   │
│  │  │ • user_input    │  │ • Tools         │  │ • output        │        │   │
│  │  │ • context       │  │ • Prompt Engine │  │ • metadata      │        │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CAMADA DE INFRAESTRUTURA                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Repositories  │  │   LLM Clients   │  │   Tools System  │  │   Storage   │ │
│  │                 │  │                 │  │                 │  │             │ │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────┐ │ │
│  │ │FileSystem   │ │  │ │Claude CLI   │ │  │ │Core Tools   │ │  │ │Session  │ │ │
│  │ │Repository   │ │  │ │Client       │ │  │ │             │ │  │ │JSON     │ │ │
│  │ │             │ │  │ │             │ │  │ │• FileOps    │ │  │ └─────────┘ │ │
│  │ │• load_def   │ │  │ │• send_prompt│ │  │ │• GitOps     │ │  │             │ │
│  │ │• save_state │ │  │ │• stream     │ │  │ │• CodeGen    │ │  │ ┌─────────┐ │ │
│  │ │• list_agents│ │  │ │• timeout    │ │  │ │• TestOps    │ │  │ │Knowledge│ │ │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │  │ │JSON     │ │ │
│  │                 │  │                 │  │                 │  │ └─────────┘ │ │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │             │ │
│  │ │MongoDB      │ │  │ │Gemini CLI   │ │  │ │Plugin Tools │ │  │ ┌─────────┐ │ │
│  │ │Repository   │ │  │ │Client       │ │  │ │             │ │  │ │History  │ │ │
│  │ │             │ │  │ │             │ │  │ │• Custom     │ │  │ │LOG      │ │ │
│  │ │• collections│ │  │ │• API calls  │ │  │ │• Extensions │ │  │ │         │ │ │
│  │ │• indexes    │ │  │ │• rate limit │ │  │ │• Integrations│ │  │ │• JSON   │ │ │
│  │ │• TTL        │ │  │ │• fallback   │ │  │ │• Workflows  │ │  │ │• Lines  │ │ │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────┘ │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CAMADA DE DADOS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    .conductor_workspace/                               │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                    agents/<agent_id>/                           │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │   │
│  │  │  │definition   │ │persona.md   │ │session.json │ │knowledge    │ │   │   │
│  │  │  │.yaml        │ │             │ │             │ │.json        │ │   │   │
│  │  │  │             │ │• Instruções │ │• Estado     │ │• Memória    │ │   │   │
│  │  │  │• Nome       │ │• Comportamento│ │• Contexto   │ │• Artefatos  │ │   │   │
│  │  │  │• Versão     │ │• Capacidades │ │• Ferramentas│ │• Metadados  │ │   │   │
│  │  │  │• Tags       │ │• Exemplos    │ │• Permissões │ │• Histórico  │ │   │   │
│  │  │  │• Tools      │ │• Limitações  │ │• Config     │ │• Aprendizado│ │   │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │   │   │
│  │  │  ┌─────────────┐ ┌─────────────┐                                 │   │   │
│  │  │  │playbook.yaml│ │history.log  │                                 │   │   │
│  │  │  │             │ │             │                                 │   │   │
│  │  │  │• Best       │ │• Execuções  │                                 │   │   │
│  │  │  │  Practices  │ │• Resultados │                                 │   │   │
│  │  │  │• Anti       │ │• Timestamps │                                 │   │   │
│  │  │  │  Patterns   │ │• Git Hashes │                                 │   │   │
│  │  │  │• Rules      │ │• Status     │                                 │   │   │
│  │  │  │• Guidelines │ │• Metadata   │                                 │   │   │
│  │  │  └─────────────┘ └─────────────┘                                 │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Fluxo de Execução Detalhado:

```
1. 👤 Usuário → CLI (admin.py/agent.py)
   │
   ▼
2. 🔧 CLI → ConductorService.execute_task(TaskDTO)
   │
   ▼
3. 📋 ConductorService → Repository.load_definition(agent_id)
   │
   ▼
4. 🛠️ ConductorService → ToolLoader.load_tools()
   │
   ▼
5. 🤖 ConductorService → AgentExecutor(definition, llm_client, tools)
   │
   ▼
6. 💬 AgentExecutor → LLM Client (Claude/Gemini)
   │
   ▼
7. 🔧 AgentExecutor → Tools (se necessário)
   │
   ▼
8. 📊 AgentExecutor → TaskResultDTO
   │
   ▼
9. 💾 ConductorService → Repository.save_state()
   │
   ▼
10. 👤 CLI → Usuário (resultado)
```

## 🎯 Componentes Principais:

### **Camada de Interface:**
- **admin.py**: Meta-agentes (criação, migração, help)
- **agent.py**: Agentes de projeto (desenvolvimento, testes)
- **conductor.py**: CLI unificado (futuro)

### **Camada de Serviço:**
- **ConductorService**: Orquestrador central
- **AgentExecutor**: Executor de tarefas
- **TaskDTO/ResultDTO**: Transferência de dados

### **Camada de Infraestrutura:**
- **Repositories**: Persistência (FileSystem/MongoDB)
- **LLM Clients**: Comunicação com IA (Claude/Gemini)
- **Tools System**: Ferramentas core + plugins
- **Storage**: Gerenciamento de estado

### **Camada de Dados:**
- **definition.yaml**: Identidade do agente
- **persona.md**: Comportamento e instruções
- **session.json**: Estado volátil
- **knowledge.json**: Memória semântica
- **playbook.yaml**: Regras e práticas
- **history.log**: Log de execuções

## 🏗️ Princípios Arquiteturais:

### ✅ **Pontos Fortes:**
- **Separação clara** de responsabilidades
- **Inversão de dependência** via interfaces
- **Extensibilidade** através de plugins
- **Multi-provider** para LLMs
- **Persistência** evolutiva de estado

### ⚠️ **Pontos de Atenção:**
- **ConductorService** faz muitas coisas (SRP)
- **Falta de cache** distribuído
- **Sem middleware** para cross-cutting concerns
- **Concorrência limitada** (fila em memória)

## 🚀 **Comparação com Spring Framework:**

| Aspecto | Spring | Conductor |
|---------|--------|-----------|
| **IoC Container** | ApplicationContext | DIContainer |
| **Service Layer** | @Service | ConductorService |
| **Repository** | @Repository | IStateRepository |
| **Configuration** | application.yml | config.yaml |
| **Dependency Injection** | @Autowired | Constructor injection |
| **Interfaces** | Interfaces/Abstractions | Ports/Interfaces |

## 📊 **Métricas da Arquitetura:**

- **Linhas de código**: ~351K (1.084 arquivos Python)
- **Documentação**: 405 arquivos MD
- **Testes**: 32 unitários + 1 E2E
- **Agentes**: Ilimitados (extensível)
- **LLM Providers**: 2 (Claude, Gemini)
- **Storage Backends**: 2 (FileSystem, MongoDB)

## 🎯 **Conclusão:**

A arquitetura do Conductor é **bem estruturada** e segue **padrões comprovados** (similar ao Spring Framework), mas aplicados ao domínio específico de **orquestração de agentes de IA**. 

**Nota da Arquitetura: 8.5/10** - Sólida, mas precisa de refinamentos para produção.
