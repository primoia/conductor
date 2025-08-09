# Orchestrator Sequence Template

## Objetivo
{Descrição do que esta sequência de orquestração deve alcançar}

## Cenário
{Contexto e background do problema sendo resolvido}

## Agentes Envolvidos
- **{agent-name-1}**: {função resumida}
- **{agent-name-2}**: {função resumida}
- **{agent-name-n}**: {função resumida}

## Fluxo de Execução

### Fase 1: {Nome da Fase}
**Objetivo**: {O que esta fase deve alcançar}

#### Passo 1.1: {Nome do Passo}
- **Trigger**: {agent-name}
- **Comando**: `{comando específico}`
- **Input esperado**: {tipo de input}
- **Output esperado**: {tipo de output}
- **Dependências**: {none ou lista}
- **Critério de sucesso**: {como saber se funcionou}

#### Passo 1.2: {Nome do Passo}
- **Trigger**: {agent-name}
- **Comando**: `{comando específico}`
- **Input esperado**: {tipo de input}
- **Output esperado**: {tipo de output}
- **Dependências**: {none ou lista}
- **Critério de sucesso**: {como saber se funcionou}

### Fase 2: {Nome da Fase}
**Objetivo**: {O que esta fase deve alcançar}

#### Passo 2.1: {Nome do Passo}
- **Trigger**: {agent-name}
- **Comando**: `{comando específico}`
- **Input esperado**: {tipo de input}
- **Output esperado**: {tipo de output}
- **Dependências**: {resultado da Fase 1}
- **Critério de sucesso**: {como saber se funcionou}

## Validações

### Teste de Coordenação
- [ ] {Validação específica 1}
- [ ] {Validação específica 2}
- [ ] {Validação específica N}

### Teste de Persistência
- [ ] Estados mantidos após interrupção
- [ ] Agentes recuperam contexto corretamente
- [ ] Possível continuar execução do ponto de parada

### Teste de Falhas
- [ ] Sistema resiliente a falha de agent individual
- [ ] Rollback funciona quando necessário
- [ ] Error handling adequado

## Critérios de Sucesso Global
- [ ] {Objetivo principal alcançado}
- [ ] {Métrica de qualidade}
- [ ] {Métrica de performance}
- [ ] {Critério de usabilidade}

## Contingências

### Se Agente X Falhar
- **Ação**: {o que fazer}
- **Rollback**: {como reverter se necessário}
- **Retry**: {condições para tentar novamente}

### Se Tempo Limite Excedido  
- **Timeout**: {tempo máximo aceitável}
- **Ação**: {o que fazer quando exceder}
- **Escalation**: {quando envolver humano}

### Se Dados Inconsistentes
- **Detecção**: {como identificar inconsistência}
- **Correção**: {processo de correção}
- **Prevenção**: {como evitar no futuro}

## Métricas de Execução
- **Tempo total esperado**: {X minutos}
- **Success rate esperada**: {X%}
- **Recursos necessários**: {CPU, memoria, etc}
- **Pontos de checkpoint**: {onde salvar progresso}

## Post-Execution
- **Cleanup**: {o que limpar depois}
- **Reporting**: {que relatórios gerar}
- **Lessons learned**: {como capturar aprendizados}
- **Next steps**: {próximas ações se bem-sucedido}