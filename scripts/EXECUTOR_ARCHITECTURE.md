# Executor Architecture - Separação de Responsabilidades

## Visão Geral

A arquitetura de executores foi refatorada seguindo o **Princípio da Responsabilidade Única** para separar claramente as responsabilidades entre agentes de projeto e meta-agentes.

## Executores

### 1. `genesis_agent.py` - Executor de Projeto

**Responsabilidade:** Executar agentes que operam em projetos alvo específicos.

**Características:**
- Requer contexto de ambiente e projeto (`--environment`, `--project`)
- Agentes residem em `projects/<environment>/<project>/agents/`
- Muda para o diretório do projeto alvo (Project Resident Mode)
- Aplica restrições de `output_scope` quando configurado

**Uso:**
```bash
python scripts/genesis_agent.py --environment develop --project nex-web-backend --agent KotlinEntityCreator_Agent --repl
```

**Exemplos de Agentes:**
- `KotlinEntityCreator_Agent`
- `ProblemRefiner_Agent`
- `TestGenerator_Agent`

### 2. `admin.py` - Executor de Administração

**Responsabilidade:** Executar meta-agentes que gerenciam o próprio framework.

**Características:**
- Não requer contexto de projeto/ambiente
- Agentes residem em `projects/_common/agents/`
- Trabalha no diretório raiz do framework
- Sem restrições de output (meta-agentes)

**Uso:**
```bash
python scripts/admin.py --agent AgentCreator_Agent --repl
```

**Exemplos de Meta-Agentes:**
- `AgentCreator_Agent`
- `migrate_agents_v2`
- `update_agents_help_system`

## Módulo Compartilhado

### `agent_common.py`

Contém funções comuns utilizadas por ambos os executores:

- `load_ai_providers_config()` - Carregamento de configuração de IA
- `load_agent_config_v2()` - Carregamento de configuração de agente
- `resolve_agent_paths()` - Resolução de caminhos de agente
- `create_llm_client()` - Criação de cliente LLM
- `start_repl_session()` - Loop de sessão REPL
- `validate_agent_config()` - Validação de configuração

## Benefícios da Separação

### 1. Alta Coesão
- Cada executor tem uma responsabilidade clara e única
- Código mais focado e fácil de entender

### 2. Código Mais Limpo
- Elimina lógica condicional desnecessária
- Reduz complexidade de cada executor

### 3. Clareza para o Usuário
- Separação explícita entre "usar" e "administrar" o framework
- Comandos mais intuitivos e específicos

### 4. Manutenibilidade
- Mudanças em um executor não afetam o outro
- Testes mais focados e isolados

## Fluxo de Decisão

### Quando usar `genesis_agent.py`:
- Agente trabalha em um projeto específico
- Precisa de contexto de ambiente/projeto
- Agente está em `projects/<env>/<project>/agents/`

### Quando usar `admin.py`:
- Agente gerencia o framework
- Não precisa de contexto de projeto
- Agente está em `projects/_common/agents/`

## Migração

### Para Usuários Existentes:
- **Agentes de Projeto:** Continue usando `genesis_agent.py` normalmente
- **Meta-Agentes:** Migre para `admin.py`

### Exemplo de Migração:
```bash
# Antes (funcionava, mas não era ideal)
python scripts/genesis_agent.py --environment _common --project _common --agent AgentCreator_Agent

# Depois (recomendado)
python scripts/admin.py --agent AgentCreator_Agent
```

## Estrutura de Diretórios

```
conductor/
├── scripts/
│   ├── genesis_agent.py      # Executor de projeto
│   ├── admin.py             # Executor de administração
│   └── agent_common.py      # Módulo compartilhado
└── projects/
    ├── _common/
    │   └── agents/          # Meta-agentes
    │       └── AgentCreator_Agent/
    └── develop/
        └── nex-web-backend/
            └── agents/      # Agentes de projeto
                └── KotlinEntityCreator_Agent/
```

## Compatibilidade

- ✅ Totalmente compatível com agentes existentes
- ✅ Não quebra funcionalidade atual
- ✅ Melhora organização e clareza
- ✅ Facilita manutenção futura
