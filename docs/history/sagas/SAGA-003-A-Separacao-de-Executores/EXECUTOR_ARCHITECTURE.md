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
python scripts/genesis_agent.py --environment develop --project your-project-name --agent KotlinEntityCreator_Agent --repl
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
# Modo interativo
python scripts/admin.py --agent AgentCreator_Agent --repl

# Modo não-interativo com caminho de destino (v2.1)
python scripts/admin.py --agent AgentCreator_Agent --destination-path "/caminho/absoluto" --input "Descrição do agente"
```

**Exemplos de Meta-Agentes:**
- `AgentCreator_Agent` - Criação automatizada de novos agentes
- `migrate_agents_v2` - Migração de agentes para nova arquitetura
- `update_agents_help_system` - Atualização do sistema de ajuda

**Exemplo Prático - Criação de Agente QA:**
```bash
python scripts/admin.py \
  --agent AgentCreator_Agent \
  --destination-path "/projects/conductor/projects/_common/agents/QAAgent_01" \
  --input "Crie um agente para automatizar testes de QA com foco em APIs REST" \
  --ai-provider claude
```

**Resultado:** Cria automaticamente:
- `agent.yaml` - Configuração com ferramentas apropriadas
- `persona.md` - Persona especializada em QA
- `state.json` - Estado inicial limpo v2.0

## Módulo Compartilhado

### `agent_common.py`

Contém funções comuns utilizadas por ambos os executores:

- `load_ai_providers_config()` - Carregamento de configuração de IA
- `load_agent_config_v2()` - Carregamento de configuração de agente
- `resolve_agent_paths()` - Resolução de caminhos de agente
- `create_llm_client()` - Criação de cliente LLM com classes LLM refatoradas
- `start_repl_session()` - Loop de sessão REPL
- `validate_agent_config()` - Validação de configuração

**Classes LLM (v2.1):**
- `LLMClient` - Interface base para provedores de IA
- `ClaudeCLIClient` - Implementação do cliente Claude CLI
- `GeminiCLIClient` - Implementação do cliente Gemini CLI

> **Nota:** As classes LLM foram movidas do `genesis_agent_v2.py` para evitar duplicação e centralizar a lógica de comunicação com provedores de IA.

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
python scripts/admin.py --agent AgentCreator_Agent --repl

# Novo (v2.1): Criação automática de agentes
python scripts/admin.py --agent AgentCreator_Agent \
  --destination-path "/path/to/new/agent" \
  --input "Criar agente para documentação QA" \
  --ai-provider claude
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
        └── your-project-name/
            └── agents/      # Agentes de projeto
                └── KotlinEntityCreator_Agent/
```

## Melhorias v2.1 (Recente)

### Criação Automatizada de Agentes

O `admin.py` foi aprimorado com funcionalidades para criação automática de agentes:

**Parâmetro `--destination-path`:**
- Permite especificar caminho absoluto onde o agente deve ser criado
- Elimina ambiguidade na criação de meta-agentes vs agentes de projeto
- Suporte para automação e scripts

**AgentCreator_Agent Refatorado:**
- Nova persona baseada em caminhos absolutos diretos
- Elimina perguntas sobre ambiente/projeto
- Template de `state.json` v2.0 limpo e padronizado
- Criação direta de arquivos no caminho especificado

**Template state.json v2.0:**
```json
{
  "agent_id": "{{agent_id}}",
  "version": "2.0", 
  "created_at": "{{timestamp}}",
  "last_updated": "{{timestamp}}",
  "execution_stats": {
    "total_executions": 0,
    "last_execution": null
  },
  "conversation_history": []
}
```

### Limpeza de Código

- **Refatoração de Classes LLM:** Removidas duplicações entre `genesis_agent_v2.py` e `agent_common.py`
- **Centralização:** Todas as classes LLM agora residem em `agent_common.py`
- **Consistência:** Melhor organização e manutenibilidade do código

### Benefícios das Melhorias v2.1

1. **Automação Completa:** Criação de agentes via linha de comando sem interação
2. **Estado Limpo:** Agentes sempre começam com `state.json` vazio
3. **Sem Ambiguidade:** Caminho explícito elimina confusão sobre localização
4. **Manutenibilidade:** Código mais limpo e organizado
5. **Testabilidade:** Processo deterministico e validável

### Validação das Melhorias

O processo de criação automatizada foi validado com os seguintes critérios:

✅ **Código de Saída 0:** Comando termina com sucesso  
✅ **Diretório Criado:** Caminho especificado é criado corretamente  
✅ **Arquivos Essenciais:** `agent.yaml`, `persona.md`, `state.json` são gerados  
✅ **Estado Limpo:** `conversation_history: []` no `state.json`

**Comando de Teste:**
```bash
python3 scripts/admin.py \
  --agent AgentCreator_Agent \
  --destination-path "/mnt/ramdisk/test-agent" \
  --input "Agente de teste simples" \
  --ai-provider claude
```

## Compatibilidade

- ✅ Totalmente compatível com agentes existentes
- ✅ Não quebra funcionalidade atual
- ✅ Melhora organização e clareza
- ✅ Facilita manutenção futura
- ✅ **Novo:** Suporte à criação automatizada de agentes
