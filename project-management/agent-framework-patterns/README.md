# 🤖 Framework de Agentes v2.1 - Documentação

> **Sistema padronizado para criação e gerenciamento de agentes com comandos interativos e versionamento incremental**

## 📋 Visão Geral

Este framework fornece um sistema completo e padronizado para agentes do Conductor & Maestro, incluindo:

- ✅ **Parametrização de saída**: Configuração flexível de arquivos gerados
- ✅ **Sistema de help interativo**: Comandos autodocumentados em cada agente  
- ✅ **Preview sem commit**: Visualização antes de salvar
- ✅ **Versionamento incremental**: Mesclagem automática v1.0 → v1.1 → v1.2...
- ✅ **Interface padronizada**: Mesmos comandos em todos os agentes

## 📁 Estrutura da Documentação

| Arquivo | Descrição |
|---------|-----------|
| `output-configuration-examples.md` | Exemplos de configuração parametrizada por tipo de agente |
| `persona-commands-template.md` | Template reutilizável para adicionar comandos em personas |
| `README.md` | Este arquivo - guia principal da documentação |

## 🚀 Guia de Implementação

### 1. Configuração de Agent.yaml

```yaml
# Configuração obrigatória para todos os agentes
execution_task: |
  Gere um documento (${output_artifact}) com...

# Parametrização de saída
output_artifact: "filename.ext"
output_directory: "path/to/output"

# Ferramentas modernas padronizadas
available_tools:
  - Read                # Substitui read_file
  - Write               # Substitui write_file  
  - Grep                # Busca avançada
  - Glob                # Padrões de arquivo
```

### 2. Sistema de Help em Personas

Cada persona deve incluir a seção de comandos:

```markdown
## Available Commands

### Help Command
**Commands accepted:** help, ajuda, comandos, ?

### Preview Command  
**Commands accepted:** preview, preview documento, mostrar documento

### Generation/Merge Command
**Commands accepted:** gerar documento, criar artefato, salvar documento, executar tarefa, consolidar
```

## 🔧 Tipos de Agentes Suportados

### Agentes de Código
- **KotlinEntityCreator_Agent**: Gera `Entity.kt`
- **KotlinRepositoryCreator_Agent**: Gera `Repository.kt`
- **KotlinServiceCreator_Agent**: Gera `Service.kt`
- **KotlinTestCreator_Agent**: Gera `IntegrationTest.kt`

### Agentes de Documentação
- **ProblemRefiner_Agent**: Gera `polished_problem.md`
- **PlanCreator_Agent**: Gera `implementation_plan.yaml`
- **PythonDocumenter_Agent**: Gera `python_documentation.md`

### Agentes de Sistema
- **AgentCreator_Agent**: Gera `agent_creation_report.md`
- **OnboardingGuide_Agent**: Gera `onboarding_report.md`

## 🎯 Comandos Universais

Todos os agentes suportam:

### 📋 Preview (Visualizar sem Salvar)
```
preview
preview documento
mostrar documento
```
**Resultado**: Exibe conteúdo no chat, não salva arquivo

### 💾 Geração/Mesclagem (Salvar com Versionamento)
```
gerar documento
criar artefato
salvar documento
executar tarefa
consolidar
```
**Resultado**: 
- **Primeira vez**: Cria v1.0
- **Já existe**: Mescla → v1.1, v1.2...

### ❓ Ajuda
```
help
ajuda
comandos
?
```
**Resultado**: Mostra comandos disponíveis e configuração do agente

## 🔄 Workflow Recomendado

```bash
# 1. Conversar com agente
python scripts/genesis_agent.py --embody AgentName --repl

# 2. No chat do agente:
help                    # Ver comandos disponíveis
# ... discutir problema/requisitos ...
preview                 # Ver como ficaria o documento
gerar documento         # Salvar v1.0

# 3. Mais conversas e refinamentos:
# ... mais discussões ...
preview                 # Ver mesclagem com novas informações
consolidar              # Salvar v1.1

# 4. Iterações subsequentes:
# ... refinamentos contínuos ...
gerar documento         # Salvar v1.2, v1.3...
```

## 📊 Benefícios do Sistema

### Para Desenvolvedores
- **Consistência**: Interface uniforme em todos os agentes
- **Produtividade**: Preview evita commits desnecessários
- **Iteração**: Versionamento facilita refinamentos incrementais

### Para o Framework
- **Escalabilidade**: Fácil criação de novos agentes
- **Manutenibilidade**: Padrões reduzem complexidade
- **Qualidade**: Validação automática e estrutura consistente

### Para Usuários
- **Autodocumentação**: Help embutido explica cada agente
- **Transparência**: Preview mostra resultado antes de salvar
- **Controle**: Versionamento preserva histórico de mudanças

## 🔧 Migração de Agentes Legados

Para atualizar agentes existentes:

1. **Agent.yaml**: Adicionar `output_artifact` e `output_directory`
2. **Persona.md**: Incluir seção "Available Commands" 
3. **Tools**: Atualizar para Read/Write/Grep/Glob
4. **Teste**: Validar help, preview e geração

Consulte `persona-commands-template.md` para template completo.

## 📈 Próximos Passos

- [ ] Implementar templates de agentes específicos por domínio
- [ ] Adicionar métricas de uso dos comandos
- [ ] Criar validação automática de configurações
- [ ] Expandir tipos de versionamento (semântico)

---

**🎼 Framework de Agentes v2.1** - Padronização, escalabilidade e excelência em cada interação.