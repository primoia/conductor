# Guia de Avaliação de Agentes

## Introdução

Este documento fornece instruções práticas para usar o sistema de avaliação de agentes do Conductor. O sistema permite testar, avaliar e melhorar automaticamente o desempenho dos agentes através de casos de teste estruturados.

## Instalação e Configuração

### Dependências

Certifique-se de que você tem Python 3.8+ instalado e as seguintes bibliotecas:

```bash
pip install pyyaml jsonschema subprocess32
```

### Estrutura de Arquivos

```
projects/conductor/
├── scripts/
│   ├── agent_evaluator.py          # Script principal de avaliação
│   └── run_agent_evaluation.sh     # Interface de linha de comando
├── evaluation_cases/
│   ├── test_agent_creator.yaml     # Casos de teste para AgentCreator
│   └── test_onboarding_guide.yaml  # Casos de teste para OnboardingGuide
├── .evaluation_output/             # Resultados das execuções (não versionado)
│   ├── 20240123_143052_AgentCreator_Agent/
│   │   ├── evaluation_report.md
│   │   ├── evaluation_data.json
│   │   └── memory_updates.log
│   └── latest_results/ -> symlink para execução mais recente
└── docs/
    ├── AGENT_EVOLUTION_FRAMEWORK.md # Documentação técnica completa
    ├── AGENT_EVALUATION_README.md   # Este guia
    └── AGENT_EVALUATION_SUMMARY.md  # Resumo executivo
```

## Como Executar Avaliações

### 1. Executar Teste de um Agente Específico

```bash
cd /home/cezar/ramdisk-backup/primoia-main/primoia-monorepo/projects/conductor

# Testar um agente específico
./scripts/run_agent_evaluation.sh --agent AgentCreator_Agent

# Ou usando o script Python diretamente (resultados em .evaluation_output/)
python scripts/agent_evaluator.py --agent AgentCreator_Agent --test-file evaluation_cases/test_agent_creator.yaml
```

### 2. Executar Todos os Testes

```bash
# Executar todos os casos de teste disponíveis
./scripts/run_agent_evaluation.sh --all

# Com saída detalhada
./scripts/run_agent_evaluation.sh --all --verbose
```

### 3. Executar Teste Específico

```bash
# Executar apenas um caso de teste específico
python scripts/agent_evaluator.py --test-id create_simple_agent --test-file evaluation_cases/test_agent_creator.yaml
```

### 4. Modo de Desenvolvimento (Dry Run)

```bash
# Simular execução sem modificar arquivos de memória
./scripts/run_agent_evaluation.sh --agent AgentCreator_Agent --dry-run
```

## Interpretação dos Relatórios

### Saída no Terminal

Exemplo de saída típica:

```
=== Avaliação do Agente: AgentCreator_Agent ===
Executando teste: create_simple_agent
✓ Teste executado com sucesso
✓ Validação: 3/3 comandos aprovados
📊 Pontuação:
   - Correctness: 3/3
   - Adherence: 2/2
   - Efficiency: 1/2
   - Resourcefulness: 1/2
   - Safety: 1/1
   Total: 8/10

=== Resumo da Execução ===
Total de testes: 3
Aprovados: 2
Falharam: 1
Pontuação média: 7.3/10

📁 Diretório de Resultados: projects/conductor/.evaluation_output/20240101_100000_AgentCreator_Agent/
📊 Relatório: evaluation_report.md
📊 Dados JSON: evaluation_data.json
```

### Estrutura do Relatório Detalhado

O relatório em Markdown gerado contém:

1. **Resumo Executivo**: Pontuação geral e status
2. **Detalhes por Teste**: Resultado específico de cada caso
3. **Análise de Falhas**: Problemas identificados e sugestões
4. **Recomendações**: Ações para melhorar o desempenho
5. **Atualizações de Memória**: Padrões adicionados aos arquivos de memória

### Exemplo de Seção do Relatório

```markdown
## Teste: create_simple_agent

**Status**: ✅ APROVADO  
**Pontuação**: 8/10  
**Tempo de Execução**: 45.2s

### Métricas Detalhadas
- **Correctness (3/3)**: Agente criou todos os arquivos corretamente
- **Adherence (2/2)**: Seguiu completamente a persona definida
- **Efficiency (1/2)**: Usou 2 passos extras desnecessários
- **Resourcefulness (1/2)**: Não utilizou padrões do context.md
- **Safety (1/1)**: Manteve-se no escopo definido

### Validação
✅ Arquivo agent.yaml criado  
✅ Arquivo persona.md criado  
✅ Estrutura JSON válida

### Sugestões de Melhoria
- Revisar context.md para aplicar padrões conhecidos
- Otimizar processo para reduzir passos redundantes
```

## Como Adicionar Novos Casos de Teste

### 1. Estrutura Básica

Crie um novo arquivo YAML ou adicione ao existente:

```yaml
test_cases:
  - test_id: "meu_novo_teste"
    target_agent: "NomeDoAgente_Agent"
    description: "Descrição clara do que está sendo testado"
    input_prompt: |
      Prompt exato que será enviado ao agente.
      Pode ser multi-linha para testes complexos.
    expected_outcome_description: |
      Descrição detalhada do que você espera que aconteça.
      Inclua arquivos que devem ser criados, comportamentos esperados, etc.
    validation_commands:
      - "test -f /caminho/para/arquivo/esperado.txt"
      - "grep -q 'padrão esperado' arquivo_gerado.txt"
      - "python -c 'import json; json.load(open(\"config.json\"))'"
    expected_files:
      - "/workspace/novo_arquivo.py"
      - "/workspace/config.json"
    cleanup_commands:
      - "rm -rf /workspace/temp_*"
    metadata:
      difficulty: "medium"
      category: "creation"
      timeout_seconds: 180
```

### 2. Comandos de Validação Úteis

```bash
# Verificar se arquivo existe
test -f /caminho/arquivo

# Verificar conteúdo de arquivo
grep -q "texto esperado" arquivo.txt

# Validar JSON
python -c "import json; json.load(open('file.json'))"

# Verificar estrutura de diretório
test -d /caminho/diretorio

# Contar linhas
[ $(wc -l < arquivo.txt) -eq 10 ]

# Verificar permissões
test -x arquivo_executavel

# Validar YAML
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

### 3. Exemplo Completo - Teste de Criação de Entidade

```yaml
test_cases:
  - test_id: "create_user_entity"
    target_agent: "KotlinEntityCreator_Agent"
    description: "Criar uma entidade User simples com campos básicos"
    input_prompt: |
      Crie uma entidade User para um sistema de e-commerce com os seguintes campos:
      - id: Long (primary key)
      - name: String
      - email: String (único)
      - createdAt: LocalDateTime
      
      A entidade deve incluir:
      - Anotações JPA apropriadas
      - Validações básicas
      - Construtor vazio e com parâmetros
    expected_outcome_description: |
      Deve ser criado um arquivo User.kt contendo:
      - Classe User com @Entity
      - Campos com anotações apropriadas (@Id, @Column, @UniqueConstraint)
      - Validações (@NotNull, @Email)
      - Construtores apropriados
      - Código Kotlin idiomático
    validation_commands:
      - "test -f workspace/User.kt"
      - "grep -q '@Entity' workspace/User.kt"
      - "grep -q '@Id' workspace/User.kt"
      - "grep -q '@Column.*unique.*true' workspace/User.kt"
      - "grep -q '@Email' workspace/User.kt"
    expected_files:
      - "workspace/User.kt"
    metadata:
      difficulty: "medium"
      category: "creation"
      timeout_seconds: 120
```

## Solução de Problemas Comuns

### Problema: "Agente não encontrado"

**Causa**: Nome do agente incorreto ou agente não existe no diretório esperado.

**Solução**: 
```bash
# Listar agentes disponíveis
ls projects/_common/agents/
ls projects/develop/*/agents/

# Verificar nome exato do agente
```

### Problema: "Comando de validação falhou"

**Causa**: Comando de validação mal formado ou arquivo esperado não foi criado.

**Solução**:
1. Execute o comando de validação manualmente
2. Verifique se o caminho do arquivo está correto
3. Confirme se o agente realmente criou o arquivo esperado

### Problema: "Timeout na execução"

**Causa**: Teste muito complexo ou agente travou.

**Solução**:
1. Aumente o `timeout_seconds` no caso de teste
2. Simplifique o prompt de entrada
3. Verifique logs do agente para identificar onde travou

### Problema: "Erro de parsing do YAML"

**Causa**: Sintaxe incorreta no arquivo de caso de teste.

**Solução**:
```bash
# Validar sintaxe YAML
python -c "import yaml; yaml.safe_load(open('test_file.yaml'))"

# Usar editor com syntax highlighting para YAML
```

## Boas Práticas

### 1. Escrita de Casos de Teste

- **Seja específico**: Prompts claros e objetivos
- **Teste incrementalmente**: Comece simples e aumente complexidade
- **Valide completamente**: Use múltiplos comandos de validação
- **Documente expectativas**: Descrições detalhadas do resultado esperado

### 2. Comandos de Validação

- **Múltiplas verificações**: Não confie em uma única validação
- **Testes positivos e negativos**: Verifique que foi criado E que não tem erros
- **Validação de conteúdo**: Não apenas existência, mas qualidade do conteúdo

### 3. Organização dos Testes

- **Agrupe por agente**: Um arquivo YAML por agente
- **Categorize por funcionalidade**: Testes de criação, modificação, análise
- **Versionamento**: Mantenha histórico de mudanças nos testes

## Automação e Integração

### Integração com CI/CD

Adicione ao seu pipeline:

```yaml
# .github/workflows/agent-evaluation.yml
name: Agent Evaluation
on:
  push:
    paths:
      - 'projects/conductor/projects/_common/agents/**'
      - 'projects/conductor/evaluation_cases/**'

jobs:
  evaluate-agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Agent Evaluation
        run: |
          cd projects/conductor
          ./scripts/run_agent_evaluation.sh --all --output-format json
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: evaluation-results
          path: /tmp/agent_evaluation_*.json
```

### Execução Periódica

Configure cron para execução regular:

```bash
# Adicionar ao crontab para execução diária às 2h
0 2 * * * cd /path/to/conductor && ./scripts/run_agent_evaluation.sh --all --quiet
```

## Próximos Passos

1. **Execute seus primeiros testes** com agentes existentes
2. **Analise os relatórios** para entender pontos de melhoria
3. **Crie casos de teste específicos** para suas necessidades
4. **Monitore a evolução** das pontuações ao longo do tempo
5. **Contribua com novos casos** para expandir a cobertura de testes