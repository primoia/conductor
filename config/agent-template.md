# Agent Template

## Agent: {AGENT_NAME}

## Função
{Descrição concisa da responsabilidade principal do agente}

## Responsabilidades
- {Lista específica do que o agente deve fazer}
- {Uma responsabilidade por linha}
- {Seja específico e mensurável}

## Regras
1. {Regras de comportamento e execução}
2. {Condições para ativação}
3. {Protocolo de comunicação}
4. {Frequência de execução}

## Restrições
- {O que o agente NÃO deve fazer}
- {Limitações de escopo}
- {Boundries com outros agentes}
- {Recursos máximos permitidos}

## Inputs Esperados
- Comando: "{exemplo de comando que ativa o agente}"
- Dados: {tipo de dados esperados}
- Contexto: {contexto necessário}

## Outputs
- Status: {SUCCESS/FAILURE/PENDING}
- Dados: {formato dos dados retornados}
- Métricas: {métricas relevantes}
- Logs: {nível de logging}

## Estado Persistente
- {campo1}: {descrição do que é armazenado}
- {campo2}: {descrição do que é armazenado}
- {campoN}: {descrição do que é armazenado}

## Dependências
- Agentes predecessores: {lista ou "none"}
- Agentes sucessores: {lista ou "none"}
- Recursos externos: {APIs, databases, etc}

## Critérios de Sucesso
- [ ] {Critério mensurável 1}
- [ ] {Critério mensurável 2}
- [ ] {Critério mensurável N}

## Handling de Erros
- **Timeout**: {comportamento se demorar muito}
- **Falha de recurso**: {comportamento se dependência falhar}
- **Input inválido**: {comportamento com dados ruins}
- **Estado inconsistente**: {comportamento com estado corrompido}

## Métricas e Monitoramento
- **Performance**: {tempo esperado de execução}
- **Success rate**: {taxa de sucesso esperada}
- **Resource usage**: {CPU, memoria, storage esperados}
- **Health check**: {como verificar se agente está saudável}