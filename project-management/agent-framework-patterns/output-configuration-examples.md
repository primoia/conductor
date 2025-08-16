# Padrões de Configuração de Saída para Agentes

## Visão Geral

O framework permite que cada agente configure seus artefatos de saída através dos parâmetros `output_artifact` e `output_directory` no `agent.yaml`. Isso torna o framework escalável e reutilizável.

## Exemplos de Configuração

### 1. ProblemRefiner_Agent
```yaml
output_artifact: "polished_problem.md"
output_directory: "workspace/outbox"
execution_task: |
  Gere um documento Markdown (`${output_artifact}`) que descreve claramente...
```

### 2. CodeGenerator_Agent (Hipotético)
```yaml
output_artifact: "generated_service.java"
output_directory: "src/main/java/com/example/service"
execution_task: |
  Com base na especificação, gere uma classe Java (`${output_artifact}`) que implementa...
```

### 3. TestCreator_Agent (Hipotético)
```yaml
output_artifact: "IntegrationTest.java"
output_directory: "src/test/java/com/example"
execution_task: |
  Crie testes automatizados (`${output_artifact}`) que validam...
```

### 4. DocumentationAgent (Hipotético)
```yaml
output_artifact: "API_Documentation.md"
output_directory: "docs/api"
execution_task: |
  Consolide a documentação da API (`${output_artifact}`) incluindo...
```

### 5. RequirementsAnalyzer_Agent (Hipotético)
```yaml
output_artifact: "requirements_specification.doc"
output_directory: "project-docs/requirements"
execution_task: |
  Analise e documente os requisitos (`${output_artifact}`) cobrindo...
```

## Comandos Universais

Com essa parametrização, todos os agentes suportam:

### 0. Help (Sistema de Ajuda)
```bash
help
ajuda
comandos
?
```
**Resultado**: 
- Exibe lista completa de comandos disponíveis
- Instruções de uso do agente
- Workflow recomendado

### 1. Preview (Visualizar sem Salvar)
```bash
preview
preview documento
mostrar documento
```
**Resultado**: 
- Exibe conteúdo completo no chat
- NÃO salva arquivo
- Permite revisar antes de salvar

### 2. Geração/Mesclagem (Salvar com Versionamento)
```bash
gerar documento
criar artefato
salvar documento
executar tarefa
consolidar
```
**Resultado**: 
- **Arquivo novo**: Cria v1.0 baseado no histórico completo
- **Arquivo existente**: Mescla com novas conversas → v1.1, v1.2...
- Salva no diretório configurado
- Preserva contexto anterior + adiciona novos insights

### 3. Workflow Recomendado
```bash
# 1. Primeira iteração
"preview"                    # Ver como ficaria
"gerar documento"           # Salvar v1.0

# 2. Mais conversas...
"preview"                    # Ver como ficaria com mesclagem  
"gerar documento"           # Salvar v1.1 (mesclado)

# 3. Iterações subsequentes...
"consolidar"                # Salvar v1.2, v1.3...
```

## Benefícios

1. **Escalabilidade**: Fácil criação de novos agentes
2. **Consistência**: Mesmo padrão de comandos para todos
3. **Flexibilidade**: Cada agente pode ter saída específica
4. **Versionamento**: Mesclagem incremental automática
5. **Preview**: Testar antes de salvar

## Implementação na Persona

```markdown
### 4.4 Configuração Dinâmica
**O nome do arquivo e diretório de saída são configuráveis:**
- **Arquivo**: Definido em `output_artifact` no agent.yaml
- **Diretório**: Definido em `output_directory` no agent.yaml
- **Para este agente**: `{output_artifact}` em `{output_directory}/`
```

## Padrão de Substituição

O `execution_task` usa `${output_artifact}` que é substituído pelo valor configurado:

```yaml
execution_task: |
  Gere um documento (`${output_artifact}`) que...
```

Isso permite reutilização de templates de persona entre diferentes tipos de agentes.