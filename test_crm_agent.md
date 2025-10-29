# Teste do CRMAnalytics_Agent

## Comando de Teste

```bash
# Teste 1: Análise de deal individual
conductor --agent CRMAnalytics_Agent --input "Analise o deal da Acme Corp - R$ 180k MRR, estágio de negociação há 60 dias, último contato há 15 dias, CFO aprovou budget mas CEO não confirmou timing, temos 2 concorrentes no processo"

# Teste 2: Identificação de riscos em pipeline
conductor --agent CRMAnalytics_Agent --input "Liste os principais riscos do meu pipeline atual considerando deals acima de R$ 100k que estão parados há mais de 30 dias"

# Teste 3: Análise de pipeline completo
conductor --agent CRMAnalytics_Agent --input "Faça uma análise completa do pipeline de vendas considerando 45 deals ativos totalizando R$ 5.2M, com taxa de conversão média de 28% e ciclo médio de 75 dias"

# Teste 4: Scoring com contexto
conductor --agent CRMAnalytics_Agent --input "Score este deal: TechStart (startup Series A), R$ 90k MRR, 3 reuniões realizadas, demo aprovada, champion forte (CTO), mas sem budget confirmado, competindo com 1 concorrente maior"
```

## Exemplos de Perguntas Esperadas

1. **Análise de Deal Específico**
   - "Analise o deal da [Cliente] no valor de [X], há [Y] dias na etapa [Z]"
   - "Por que o deal da [Cliente] está em risco?"
   - "Qual o score do deal da [Cliente] e o que fazer para melhorar?"

2. **Identificação de Riscos**
   - "Quais deals estão em risco crítico no meu pipeline?"
   - "Identifique sinais de ghosting nos meus deals ativos"
   - "Qual deal acima de R$ 100k tem maior probabilidade de perder?"

3. **Análise de Pipeline**
   - "Como está a saúde do meu pipeline?"
   - "Onde estão os gargalos no funil de vendas?"
   - "Qual minha previsão de fechamento para este trimestre?"

4. **Insights Estratégicos**
   - "Quais padrões identificam deals de sucesso?"
   - "Como melhorar minha taxa de conversão?"
   - "Qual o perfil de cliente ideal baseado no histórico?"

## Resultado Esperado

O agente deve retornar análises em Markdown formatado com:

✅ **Score numérico claro** (X/100)
✅ **Status visual** (🟢 Saudável / 🟡 Atenção / 🔴 Risco)
✅ **Justificativas baseadas em dados** para cada dimensão
✅ **Sinais de risco identificados** com evidências concretas
✅ **Próximos passos acionáveis** com prazos e responsáveis
✅ **Insights comerciais inteligentes**
✅ **Formato visual e organizado** (tabelas, listas, seções)

## Características do Agente

- **Analítico**: Considera contexto completo antes de pontuar
- **Proativo**: Identifica riscos antes que afetem resultados
- **Orientado à Execução**: Recomendações práticas e acionáveis
- **Inteligente Contextualmente**: Avalia deals com nuance (não usa fórmulas genéricas)
- **Transparente**: Explica raciocínio por trás de scores e alertas
- **Comercialmente Inteligente**: Entende dinâmicas B2B e negociação
- **Tom Profissional**: Direto ao ponto, baseado em evidências

## Validação de Sucesso

O teste é bem-sucedido se o agente:

1. ✅ Retorna resposta em Markdown formatado e legível
2. ✅ Fornece score numérico justificado por dimensões
3. ✅ Identifica riscos específicos com evidências
4. ✅ Sugere próximos passos concretos (não genéricos)
5. ✅ Usa tom profissional e objetivo
6. ✅ Organiza informação visualmente (emojis estratégicos, tabelas)
7. ✅ Demonstra inteligência contextual (não repete templates)
