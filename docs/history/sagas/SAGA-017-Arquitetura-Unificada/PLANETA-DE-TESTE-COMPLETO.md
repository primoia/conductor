# PLANETA DE TESTE COMPLETO - SAGA-017: Validação de Ambos os Universos

## 🎯 **Objetivo**

Criar um ambiente de teste exaustivo que valide **TODAS** as funcionalidades de ambos os universos antes da migração, garantindo que nenhuma funcionalidade seja perdida e que a transição seja transparente.

## 🏗️ **Estrutura do Planeta de Teste**

### **Universo 1: Sistema Atual (admin.py + agent.py)**
### **Universo 2: Nova Arquitetura (AgentService + Orchestrator + CLI Unificado)**

---

## 📋 **FASE 1: AUDITORIA COMPLETA DE FUNCIONALIDADES**

### **1.1 Mapeamento Exaustivo do admin.py**

#### **Funcionalidades Identificadas:**
- [ ] **Descoberta de Meta-Agents**: `projects/_common/agents/`
- [ ] **Embodiment de Agentes**: `_embody_meta_agent()`
- [ ] **Chat Interativo**: REPL mode com comandos customizados
- [ ] **Chat Não-Interativo**: `--input` com processamento direto
- [ ] **Modo Simulação**: `--simulate-chat` sem chamar provider real
- [ ] **Debug Mode**: `--debug` com logs detalhados
- [ ] **Export de Debug**: `export-debug` command
- [ ] **Context Enhancement**: `_build_enhanced_message()` com variáveis de ambiente
- [ ] **State Management**: `save_agent_state()` via StateManager
- [ ] **Tool Discovery**: `get_available_tools()`
- [ ] **Cleanup de Sessões**: `cleanup_orphan_sessions()`
- [ ] **Validação de Ambiente**: `ErrorHandling.validate_environment()`
- [ ] **Verificação de Permissões**: `ErrorHandling.check_permissions()`
- [ ] **Argument Parsing**: `CLIArgumentParser.create_admin_parser()`
- [ ] **Validação de Argumentos**: `CLIArgumentParser.validate_admin_args()`

#### **Comandos REPL Específicos:**
- [ ] `debug` - Mostra contexto completo
- [ ] `export-debug` - Exporta relatório de debug
- [ ] `state` - Mostra estado do agente
- [ ] `history` - Mostra histórico de conversas
- [ ] `tools` - Lista ferramentas disponíveis
- [ ] `scope` - Mostra restrições de output
- [ ] `status` - Mostra status de segurança

### **1.2 Mapeamento Exaustivo do agent.py**

#### **Funcionalidades Identificadas:**
- [ ] **Descoberta de Project-Agents**: `projects/{environment}/{project}/agents/`
- [ ] **Embodiment de Project-Agents**: `_embody_project_agent()`
- [ ] **Context de Ambiente/Projeto**: Environment + Project + Agent ID
- [ ] **Working Directory**: Mudança para diretório do projeto
- [ ] **Output Scope Restrictions**: `get_output_scope()` com restrições
- [ ] **Chat Interativo**: REPL mode básico
- [ ] **Chat Não-Interativo**: `--input` com processamento direto
- [ ] **State Management**: `save_agent_state()` via StateManager
- [ ] **Tool Discovery**: `get_available_tools()`
- [ ] **Validação de Ambiente**: `ErrorHandling.validate_environment()`
- [ ] **Verificação de Permissões**: `ErrorHandling.check_permissions()`
- [ ] **Argument Parsing**: `CLIArgumentParser.create_agent_parser()`

#### **Comandos REPL Específicos:**
- [ ] `state` - Mostra estado do agente
- [ ] `history` - Mostra histórico de conversas
- [ ] `tools` - Lista ferramentas disponíveis
- [ ] `scope` - Mostra restrições de output
- [ ] `status` - Mostra status de segurança

---

## 🧪 **FASE 2: TESTES EXAUSTIVOS DA NOVA ARQUITETURA**

### **2.1 Testes de FileSystemStorage**

#### **Testes de Descoberta de Agentes:**
```python
def test_list_all_agent_definitions_filesystem():
    """Testa descoberta de agentes no filesystem"""
    # Setup: Criar agentes de teste com definition.yaml
    # Test: Verificar se todos são descobertos
    # Assert: Lista completa de AgentDefinition

def test_agent_discovery_with_missing_files():
    """Testa comportamento com arquivos faltantes"""
    # Setup: Agente com definition.yaml mas sem persona.md
    # Test: Verificar tratamento de erro
    # Assert: Erro apropriado, outros agentes ainda descobertos

def test_agent_discovery_empty_workspace():
    """Testa descoberta em workspace vazio"""
    # Setup: Workspace sem agentes
    # Test: Verificar retorno
    # Assert: Lista vazia, sem erros
```

#### **Testes de Carregamento de Artefatos:**
```python
def test_load_agent_instance_complete():
    """Testa carregamento completo de instância"""
    # Setup: Agente com todos os artefatos
    # Test: Carregar AgentInstance
    # Assert: Todos os artefatos carregados corretamente

def test_load_agent_instance_missing_artifacts():
    """Testa carregamento com artefatos faltantes"""
    # Setup: Agente com alguns artefatos faltantes
    # Test: Verificar tratamento de erro
    # Assert: Erro apropriado com detalhes

def test_schema_version_validation():
    """Testa validação de versão de schema"""
    # Setup: Agente com schema_version incompatível
    # Test: Carregar agente
    # Assert: CompatibilityError apropriado
```

### **2.2 Testes de MongoDB Storage**

#### **Testes de Transparência de Backend:**
```python
def test_mongodb_storage_equivalence():
    """Testa equivalência entre FileSystem e MongoDB"""
    # Setup: Mesmo agente em ambos os backends
    # Test: Carregar de ambos
    # Assert: AgentInstance idênticos

def test_backend_switching_transparency():
    """Testa transparência na troca de backend"""
    # Setup: Configurar filesystem, depois mongodb
    # Test: Executar mesmas operações
    # Assert: Comportamento idêntico

def test_mongodb_connection_handling():
    """Testa tratamento de conexão MongoDB"""
    # Setup: MongoDB indisponível
    # Test: Tentar operações
    # Assert: Erro apropriado, fallback se configurado
```

### **2.3 Testes de Orchestrator**

#### **Testes de Descoberta Inteligente:**
```python
def test_find_best_agent_for_task():
    """Testa descoberta de melhor agente para tarefa"""
    # Setup: Múltiplos agentes com capabilities diferentes
    # Test: Buscar agente para tarefa específica
    # Assert: Agente correto selecionado

def test_no_suitable_agent_found():
    """Testa comportamento quando nenhum agente adequado"""
    # Setup: Tarefa sem agentes compatíveis
    # Test: Buscar agente
    # Assert: NoSuitableAgentFoundError apropriado

def test_multiple_candidates_handling():
    """Testa seleção entre múltiplos candidatos"""
    # Setup: Múltiplos agentes com capabilities similares
    # Test: Buscar agente
    # Assert: Seleção consistente (primeiro candidato)
```

### **2.4 Testes de CLI Unificado**

#### **Testes de Compatibilidade com Funcionalidades Atuais:**
```python
def test_cli_unified_admin_equivalence():
    """Testa equivalência com funcionalidades do admin.py"""
    # Setup: Mesmo agente, mesmos argumentos
    # Test: Executar via CLI unificado vs admin.py
    # Assert: Comportamento idêntico

def test_cli_unified_agent_equivalence():
    """Testa equivalência com funcionalidades do agent.py"""
    # Setup: Mesmo agente, mesmos argumentos
    # Test: Executar via CLI unificado vs agent.py
    # Assert: Comportamento idêntico

def test_cli_unified_repl_commands():
    """Testa comandos REPL do CLI unificado"""
    # Setup: Agente carregado via CLI unificado
    # Test: Executar todos os comandos REPL
    # Assert: Todos os comandos funcionam

def test_cli_unified_orchestration():
    """Testa funcionalidade de orquestração"""
    # Setup: Múltiplos agentes disponíveis
    # Test: Executar tarefa via orquestração
    # Assert: Agente correto selecionado e executado
```

---

## 🔄 **FASE 3: TESTES DE TRANSIÇÃO E COMPATIBILIDADE**

### **3.1 Testes de Migração de Agentes**

#### **Testes de Conversão de Estrutura:**
```python
def test_agent_yaml_to_definition_yaml():
    """Testa conversão de agent.yaml para definition.yaml"""
    # Setup: Agente com estrutura antiga
    # Test: Converter para nova estrutura
    # Assert: Todos os campos convertidos corretamente

def test_persona_md_preservation():
    """Testa preservação do persona.md"""
    # Setup: Agente com persona.md existente
    # Test: Migrar agente
    # Assert: persona.md preservado

def test_state_json_migration():
    """Testa migração do state.json"""
    # Setup: Agente com state.json existente
    # Test: Migrar para nova estrutura
    # Assert: Estado preservado em session.json
```

### **3.2 Testes de Funcionalidades Pós-Migração**

#### **Testes de Continuidade:**
```python
def test_agent_functionality_after_migration():
    """Testa funcionalidade de agente após migração"""
    # Setup: Agente migrado
    # Test: Executar todas as funcionalidades
    # Assert: Comportamento idêntico ao original

def test_state_persistence_after_migration():
    """Testa persistência de estado após migração"""
    # Setup: Agente com estado existente
    # Test: Migrar e continuar sessão
    # Assert: Estado preservado

def test_tool_access_after_migration():
    """Testa acesso a ferramentas após migração"""
    # Setup: Agente com ferramentas configuradas
    # Test: Migrar e usar ferramentas
    # Assert: Ferramentas funcionam corretamente
```

---

## 🛠️ **FASE 4: TESTES DE FERRAMENTAS E CAPACIDADES**

### **4.1 Testes de Sistema de Ferramentas**

#### **Testes de Descoberta de Ferramentas:**
```python
def test_tool_discovery_mechanism():
    """Testa mecanismo de descoberta de ferramentas"""
    # Setup: Ferramentas disponíveis no sistema
    # Test: Descobrir ferramentas
    # Assert: Todas as ferramentas descobertas

def test_tool_plugin_loading():
    """Testa carregamento de plugins de ferramentas"""
    # Setup: Plugin de ferramenta customizado
    # Test: Carregar plugin
    # Assert: Ferramenta disponível para agentes

def test_tool_security_policies():
    """Testa políticas de segurança de ferramentas"""
    # Setup: Políticas de segurança configuradas
    # Test: Executar ferramentas com restrições
    # Assert: Políticas aplicadas corretamente
```

### **4.2 Testes de Configuração**

#### **Testes de Configuração Dinâmica:**
```python
def test_config_yaml_loading():
    """Testa carregamento de config.yaml"""
    # Setup: config.yaml com configurações
    # Test: Carregar configuração
    # Assert: Configurações carregadas corretamente

def test_storage_backend_switching():
    """Testa troca de backend de armazenamento"""
    # Setup: Configuração para filesystem
    # Test: Trocar para mongodb
    # Assert: Troca transparente

def test_tool_config_application():
    """Testa aplicação de configuração de ferramentas"""
    # Setup: Configuração de ferramentas
    # Test: Aplicar configuração
    # Assert: Configurações aplicadas
```

---

## 📊 **FASE 5: MÉTRICAS E VALIDAÇÃO**

### **5.1 Métricas de Performance**

#### **Benchmarks:**
- [ ] **Tempo de Descoberta**: FileSystem vs MongoDB
- [ ] **Tempo de Carregamento**: Agente completo vs parcial
- [ ] **Tempo de Execução**: CLI antigo vs novo
- [ ] **Uso de Memória**: Diferentes backends
- [ ] **Tempo de Resposta**: Orchestrator vs descoberta manual

### **5.2 Métricas de Funcionalidade**

#### **Cobertura de Testes:**
- [ ] **Cobertura de Código**: >95% para componentes críticos
- [ ] **Cobertura de Funcionalidades**: 100% das funcionalidades mapeadas
- [ ] **Cobertura de Casos de Erro**: Todos os cenários de erro
- [ ] **Cobertura de Integração**: Todos os fluxos end-to-end

### **5.3 Validação de Requisitos**

#### **Checklist de Validação:**
- [ ] **Todas as funcionalidades do admin.py funcionam no CLI unificado**
- [ ] **Todas as funcionalidades do agent.py funcionam no CLI unificado**
- [ ] **Troca de backend é transparente**
- [ ] **Migração de agentes preserva funcionalidade**
- [ ] **Sistema de ferramentas funciona corretamente**
- [ ] **Orquestração funciona como esperado**
- [ ] **Performance é aceitável ou melhor**

---

## 📝 **FASE 6: DOCUMENTAÇÃO ATUALIZADA**

### **6.1 Atualização do AGENT_DESIGN_PATTERNS.md**

#### **Novas Seções a Adicionar:**
- [ ] **Nova Estrutura de Artefatos**: definition.yaml, playbook.yaml, knowledge.json
- [ ] **Sistema de Descoberta**: Como agentes são descobertos automaticamente
- [ ] **Orquestração**: Como usar o Orchestrator para delegação
- [ ] **Backends de Armazenamento**: Filesystem vs MongoDB
- [ ] **CLI Unificado**: Comandos e funcionalidades
- [ ] **Migração de Agentes**: Como migrar da estrutura antiga

### **6.2 Documentação de Funcionalidades Descobertas**

#### **Funcionalidades Não Documentadas:**
- [ ] **Sistema de Debug**: Modo simulação, export de debug
- [ ] **Context Enhancement**: Variáveis de ambiente automáticas
- [ ] **State Management**: Persistência de estado entre sessões
- [ ] **Tool Security**: Políticas de segurança granulares
- [ ] **REPL Commands**: Comandos interativos disponíveis
- [ ] **Error Handling**: Tratamento de erros e validações

---

## 🚀 **PLANO DE EXECUÇÃO**

### **Semana 1: Auditoria e Mapeamento**
- [ ] Mapear todas as funcionalidades do admin.py
- [ ] Mapear todas as funcionalidades do agent.py
- [ ] Documentar comandos REPL e funcionalidades ocultas
- [ ] Criar checklist de validação

### **Semana 2: Implementação de Testes**
- [ ] Implementar testes de FileSystemStorage
- [ ] Implementar testes de MongoDB Storage
- [ ] Implementar testes de Orchestrator
- [ ] Implementar testes de CLI unificado

### **Semana 3: Testes de Integração**
- [ ] Testes de migração de agentes
- [ ] Testes de compatibilidade
- [ ] Testes de transição de backends
- [ ] Testes de sistema de ferramentas

### **Semana 4: Validação e Documentação**
- [ ] Executar todos os testes
- [ ] Validar métricas de performance
- [ ] Atualizar documentação
- [ ] Criar relatório de validação

---

## 🎯 **CRITÉRIOS DE SUCESSO**

### **Funcionalidade:**
- ✅ **100% das funcionalidades atuais funcionam no novo sistema**
- ✅ **Troca de backend é transparente**
- ✅ **Migração preserva funcionalidade**
- ✅ **Orquestração funciona corretamente**

### **Performance:**
- ✅ **Tempo de resposta ≤ tempo atual**
- ✅ **Uso de memória ≤ uso atual**
- ✅ **Descoberta de agentes < 1 segundo**

### **Qualidade:**
- ✅ **Cobertura de testes > 95%**
- ✅ **Documentação atualizada**
- ✅ **Zero regressões funcionais**

---

**Data de Criação:** $(date)
**Status:** Em Planejamento
**Próxima Revisão:** Após implementação dos testes
