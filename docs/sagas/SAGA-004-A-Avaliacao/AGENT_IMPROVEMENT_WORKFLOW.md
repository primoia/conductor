# Framework de Melhoria Contínua de Agentes

## 1. Objetivo

Este documento descreve o fluxo de trabalho iterativo para criar, testar, diagnosticar e aprimorar sistematicamente os agentes do Conductor. O objetivo é transformar cada agente em uma ferramenta robusta e de alto desempenho, com uma pontuação de avaliação quantificável.

## 2. O Fluxo de Melhoria Contínua

O processo é um ciclo de feedback contínuo, focado em identificar e resolver o ponto de falha mais crítico em cada iteração.

```mermaid
graph TD
    A[<b>Início:</b><br>Definir Objetivo do Agente] --> B{1. Usar AgentCreator_Agent<br>para criar o Agente};
    B --> C{2. Validação Pós-Criação};
    C -->|Agente não encontrado<br>ou no local errado| D[Ajustar parâmetros<br>de environment/project<br>no comando de criação];
    D --> B;
    C -->|Versão Incorreta (V1)| E[Executar migração<br>ou refatorar o .yaml<br>para o formato V2];
    E --> C;
    C -->|Sucesso| F[3. Criar Caso de Teste<br>(.yaml) para o novo agente];
    F --> G{4. Executar Framework de Avaliação<br><code>run_agent_evaluation.sh</code>};
    G --> H[5. Analisar Relatório<br>e Logs];
    H --> I{O 'Correctness' é > 0?};
    I -->|Não: Falha Fundamental| J[<b>Refatorar Persona:</b><br>Ajustar a lógica de execução<br>de ferramentas do agente];
    J --> G;
    I -->|Sim: Funcional| K{A pontuação<br>é satisfatória?<br>(ex: >= 8.0)};
    K -->|Não: Precisa de Refinamento| L[<b>Refinar Persona:</b><br>Ajustar prompts nos testes<br>para serem mais diretos<br>(prompts atômicos)];
    L --> G;
    K -->|Sim: Sucesso| M[<b>Fim:</b><br>Agente Aprovado e<br>Pronto para Uso];
```

## 3. Fases do Fluxo (Detalhado)

#### **Fase 1: Criação do Agente**
O ponto de partida é usar nosso meta-agente `AgentCreator_Agent` para gerar a estrutura base de um novo agente. Isso é feito através do script `genesis_agent_v2.py` (ou `admin.py`), passando um prompt detalhado com as especificações do agente a ser criado.

#### **Fase 2: Validação Pós-Criação**
Após a execução do `AgentCreator_Agent`, a primeira validação é crucial e puramente estrutural. Verificamos dois pontos principais:
1.  **Validação de Localização:** O agente foi criado no diretório correto?
    *   **Falha:** Se o agente não for encontrado ou estiver no local errado (ex: `_common/` em vez de `develop/test-project/`), o erro está no **nosso comando** de criação. Devemos corrigir os parâmetros `--environment` e `--project` e executar a Fase 1 novamente.
2.  **Validação de Versão:** O `agent.yaml` está no formato V2.0?
    *   **Falha:** Se o agente foi criado com uma versão legada, ele não será compatível com o executor. A solução é realizar uma migração manual do `agent.yaml` para o formato V2.0.

#### **Fase 3: Criação do Caso de Teste**
Com um agente estruturalmente correto, criamos um arquivo de teste `.yaml` em `evaluation_cases/`. Este arquivo deve conter de 2 a 3 cenários que testem a funcionalidade principal do agente, com comandos de validação que verificam os artefatos de saída (arquivos criados, conteúdo específico, etc.).

#### **Fase 4: Execução da Avaliação**
Executamos o framework de avaliação com o comando:
`projects/conductor/scripts/run_agent_evaluation.sh --agent <NOME_DO_AGENTE>`

Isso irá gerar um relatório detalhado em `projects/conductor/.evaluation_output/`.

#### **Fase 5: Diagnóstico e Iteração**
Esta é a fase central do ciclo de melhoria. Analisamos o relatório gerado:
1.  **Verificar `Correctness` Primeiro:** A métrica mais importante é a de `Correctness`. Se a pontuação for `0/3`, significa que o agente não está executando sua função principal (ex: não criou os arquivos).
    *   **Ação:** O problema provavelmente está na **persona do agente**. Ela precisa ser refatorada para incluir instruções mais explícitas sobre *como* usar suas ferramentas para atingir o objetivo. Retornamos à Fase 4 após a refatoração.
2.  **Analisar a Pontuação Geral:** Se o `Correctness` for maior que 0, o agente é funcional. Agora olhamos para a pontuação geral.
    *   **Ação:** Se a pontuação for baixa, o problema pode ser um "desencontro" conversacional. A solução é refinar os **prompts dentro do arquivo de teste**, tornando-os mais diretos e "atômicos" para evitar ambiguidade. Retornamos à Fase 4 após o refinamento.
3.  **Ciclo de Melhoria:** Repetimos o ciclo "Executar -> Diagnosticar -> Refinar" até que a pontuação do agente atinja o nível desejado (ex: 8.0/10 ou superior).

#### **Fase 6: Conclusão**
Um agente é considerado "concluído" e aprovado quando atinge consistentemente uma alta pontuação em seus casos de teste, demonstrando que é robusto, correto e eficiente.