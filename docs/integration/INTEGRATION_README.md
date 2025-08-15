# .bmad-core + Conductor Integration

Esta documentação descreve como usar a integração entre o sistema de metodologia `.bmad-core` e o orquestrador de execução `conductor`.

## Visão Geral

A integração permite que o agente `@dev` do `.bmad-core` gere planos de implementação estruturados em YAML, que são então executados automaticamente pelo sistema `conductor`. Isso cria um fluxo de trabalho contínuo desde o planejamento até a implementação.

## Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   .bmad-core    │    │   Implementation │    │    conductor    │
│                 │    │      Plan        │    │                 │
│  @dev agent     │───▶│   (YAML)         │───▶│   Executor      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Componentes

### 1. Template YAML (`implementation-plan-template.yaml`)
- Define a estrutura padrão para planos de implementação
- Localização: `projects/develop/workspace/implementation-plan-template.yaml`

### 2. Tarefa do Agente (`create-implementation-plan.md`)
- Instruções para o agente `@dev` gerar planos
- Localização: `.bmad-core/tasks/create-implementation-plan.md`

### 3. Orquestrador (`run_conductor.py`)
- Script principal que executa os planos
- Localização: `run_conductor.py`

## Como Usar

### Passo 1: Preparar o Ambiente

1. Certifique-se de que o `.bmad-core` está configurado
2. Verifique se o agente `@dev` tem acesso à tarefa `create-implementation-plan`
3. Instale as dependências Python:
   ```bash
   pip install pyyaml
   ```

### Passo 2: Criar um Plano de Implementação

1. Ative o agente `@dev`:
   ```
   @dev
   ```

2. Use o comando para criar um plano:
   ```
   *create-implementation-plan
   ```

3. O agente irá:
   - Analisar a história atual
   - Quebrar a implementação em tarefas
   - Gerar um arquivo `implementation-plan.yaml`

### Passo 3: Executar o Plano

1. Use o conductor para executar o plano:
   ```bash
   python run_conductor.py projects/develop/workspace/implementation-plan.yaml
   ```

2. O conductor irá:
   - Carregar e validar o plano
   - Executar as tarefas na ordem correta
   - Validar os resultados
   - Reportar o progresso

## Estrutura do Plano YAML

```yaml
storyId: "stories/story-XXX.md"
description: "Descrição do que será implementado"

tasks:
  - name: "nome-da-tarefa"
    description: "Descrição detalhada"
    agent: "NomeDoAgente_Type_Agent"
    inputs:
      - "caminho/para/arquivo/entrada.md"
    outputs:
      - "caminho/para/arquivo/saida.kt"
    depends_on: "tarefa-anterior"  # opcional
    validation:
      - "Critério de validação específico"

validationCriteria:
  - "Critério de validação geral 1"
  - "Critério de validação geral 2"
```

## Exemplo Prático

### 1. História de Exemplo
```markdown
# Implementar Entidade Produto

## Critérios de Aceitação
- Criar entidade Product com campos: id, name, price, description
- Implementar operações CRUD básicas
- Adicionar validações de negócio
- Criar testes unitários
```

### 2. Plano Gerado Automaticamente
O agente `@dev` analisa a história e gera um plano como o exemplo em `example-implementation-plan.yaml`.

### 3. Execução
```bash
python run_conductor.py projects/develop/workspace/example-implementation-plan.yaml
```

## Agentes Disponíveis

O conductor pode executar diferentes tipos de agentes especializados:

- `KotlinEntityCreator_Agent`: Cria entidades Kotlin
- `KotlinRepositoryCreator_Agent`: Cria repositórios
- `KotlinServiceCreator_Agent`: Cria serviços
- `KotlinControllerCreator_Agent`: Cria controllers REST
- `KotlinTestCreator_Agent`: Cria testes unitários

## Validação e Rollback

### Validação
- Cada tarefa tem critérios de validação específicos
- O plano tem critérios de validação gerais
- Falhas param a execução imediatamente

### Rollback
- O plano pode incluir instruções de rollback
- Arquivos temporários são limpos automaticamente
- Mudanças podem ser revertidas via git

## Testando a Integração

Execute o script de teste para verificar se tudo está funcionando:

```bash
python test_integration.py
```

Este script demonstra o fluxo completo:
1. Simula o agente `@dev` criando um plano
2. Executa o plano com o conductor
3. Valida os resultados

## Troubleshooting

### Problemas Comuns

1. **Plano não encontrado**
   - Verifique se o arquivo YAML existe
   - Confirme o caminho está correto

2. **Dependências circulares**
   - O conductor detecta e reporta dependências circulares
   - Revise a estrutura de dependências do plano

3. **Agente não encontrado**
   - Verifique se o nome do agente está correto
   - Confirme se o agente está disponível no sistema

4. **Validação falha**
   - Revise os critérios de validação
   - Verifique se os arquivos de saída foram criados corretamente

### Logs

O conductor gera logs detalhados que podem ajudar no diagnóstico:

```bash
python run_conductor.py plan.yaml --verbose
```

## Próximos Passos

1. **Implementar Agentes Reais**: Substituir a simulação por agentes reais
2. **Adicionar Mais Validações**: Implementar validações mais sofisticadas
3. **Interface Web**: Criar uma interface web para monitorar execuções
4. **Integração com CI/CD**: Conectar com pipelines de CI/CD
5. **Métricas e Relatórios**: Adicionar coleta de métricas e relatórios

## Contribuindo

Para contribuir com a integração:

1. Siga o padrão estabelecido nos arquivos existentes
2. Adicione testes para novas funcionalidades
3. Atualize a documentação
4. Mantenha a compatibilidade com o formato YAML existente

## Suporte

Se você encontrar problemas ou tiver dúvidas:

1. Verifique esta documentação
2. Execute o script de teste
3. Revise os logs detalhados
4. Consulte o arquivo `INTEGRATION_PLAN.md` para detalhes técnicos
