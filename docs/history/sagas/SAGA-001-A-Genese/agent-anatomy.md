# Anatomia e Ciclo de Vida de um Agente Conductor

Este documento detalha a arquitetura de arquivos e os princípios operacionais para qualquer agente no ecossistema Conductor. Esta estrutura garante que cada agente seja único, autônomo, com estado, auditável e capaz de aprendizado contínuo.

## Paradigma Central: Agentes como Mantenedores de Domínio

O Conductor abandona o modelo de "agentes-por-função" genéricos em favor de um modelo mais poderoso: **agentes-por-domínio**.

*   **Agente de Domínio:** Um agente não é um "criador de testes" genérico, mas sim o **"mantenedor virtual"** de um componente de software específico. Por exemplo, existe o `AccountService_Test_Agent` e o `AccountService_Implementation_Agent`.
*   **Histórico Linear:** Cada agente mantém o histórico completo e linear de todas as alterações dentro de seu domínio específico. O `AccountService_Test_Agent` conhece a história de cada teste já criado para esse serviço.
*   **Propriedade de Código:** Cada agente é "dono" de um conjunto específico de arquivos no codebase, definido em seu manifesto.
*   **Coordenação de Especialistas:** Um Agente de Domínio pode invocar "Agentes Especialistas" (ferramentas genéricas) para realizar tarefas, mas ele permanece como o coordenador e detentor do contexto.

---

## Estrutura de Arquivos de um Agente (`/{uuid}/`)

A pasta de um agente é seu "DNA digital". Ela contém tudo o que uma IA precisa para incorporar aquele agente, executar uma tarefa e evoluir.

```
{uuid}/
├── manifest.json             #  identidade (quem eu sou)
├── persona.md                # propósito (o que eu faço)
├── .lock                     # status de concorrência (estou ocupado?)
│
├── memory/                   # cérebro (o que eu sei)
│   ├── state.json            #   - memória de curto prazo (status atual)
│   ├── recommendations.json  #   - conselhos (o que aprendi com os outros)
│   ├── avoid_patterns.md     #   - cicatrizes (o que aprendi com meus erros)
│   └── context.md            #   - autobiografia (minha história de sucesso)
│
├── workspace/                # mesa de trabalho (o que estou fazendo)
│   ├── inbox/                #   - caixa de entrada de tarefas
│   ├── outbox/               #   - caixa de saída de resultados
│   └── processing/           #   - trabalho em andamento
│
└── log/                      # diário (tudo o que eu já fiz)
    └── 2025-08-11.log        #   - registro detalhado e imutável
```

### 1. Identidade e Propósito

*   **`manifest.json`**: O "passaporte" do agente. Metadados estáticos para descoberta e governança.
    *   **Exemplo de Conteúdo:**
        ```json
        {
          "uuid": "a1b2c3d4...",
          "human_name": "Mantenedor de Testes para AccountService",
          "agent_type": "TestAgent",
          "domain_ownership": "src/test/kotlin/com/example/AccountServiceTest.kt",
          "version": "1.0",
          "tags": ["kotlin", "test", "account-service"]
        }
        ```

*   **`persona.md`**: A "alma" do agente. O prompt principal que define seu papel, responsabilidades, regras e limites.
    *   **Exemplo de Conteúdo:** "Eu sou o responsável por garantir a qualidade do AccountService através de uma suíte de testes completa. Meu histórico reflete todas as estratégias de teste já tentadas para este serviço. Eu sigo estritamente as recomendações do meu `recommendations.json` e evito os erros documentados em `avoid_patterns.md`."

### 2. Memória e Aprendizado (`memory/`)

O cérebro do agente, onde o conhecimento é acumulado e refinado.

*   **`state.json`**: Memória de curto prazo. Contém o status operacional (ex: `idle`, `processing`), métricas de desempenho (taxa de sucesso, tempo médio) e informações sobre a tarefa atual.

*   **`recommendations.json`**: O "manual de boas práticas". Este arquivo é atualizado por um `Supervisor-Agent` e contém as melhores abordagens observadas em todo o sistema (ex: versões de bibliotecas e padrões de código que levam a mais sucesso). Isso permite aprendizado coletivo.

*   **`avoid_patterns.md`**: O "diário de falhas" ou "cicatrizes". Um log em markdown onde o próprio agente (ou o orquestrador) anota estratégias que falharam, para evitar repeti-las.
    *   **Exemplo:** "Tentei usar MockK `v1.12` para mocks estáticos e falhou; a abordagem correta é `v1.13+` com `mockkStatic`."

*   **`context.md`**: A "autobiografia" ou memória de longo prazo. Um resumo dos sucessos e aprendizados mais importantes extraídos do `log/` por um Meta-Agente. Mantém o contexto rico sem sobrecarregar a IA.

### 3. Trabalho e Fluxo (`workspace/`)

A "caixa de correio" que gerencia o fluxo de trabalho de forma assíncrona e resiliente.

*   **`inbox/`**: Contém arquivos de tarefas (ex: `task-123.json`) a serem processadas.
*   **`outbox/`**: Contém os resultados das tarefas concluídas para o orquestrador coletar.
*   **`processing/`**: Diretório para onde uma tarefa é movida enquanto está ativa. Se o agente falhar, a tarefa em `processing/` pode ser recuperada ou reiniciada.

### 4. Auditoria (`log/`)

O registro imutável de todas as ações, decisões e observações do agente.

*   **Conteúdo:** Arquivos de log diários (ex: `2025-08-11.log`) com entradas JSON estruturadas e com timestamp.
*   **Finalidade:** É a fonte da verdade para depuração, auditoria e a matéria-prima para todos os Meta-Agentes (Supervisores, Compressores de Contexto) aprenderem. É o ativo mais valioso do agente.

### 5. Controle (`.lock`)

*   Um arquivo vazio que, quando existe, sinaliza que o agente está ativo. Impede que o mesmo agente seja executado por múltiplos processos simultaneamente, garantindo a integridade de seu estado.

---

## Unicidade da Chamada de IA

Esta estrutura garante que cada chamada para a IA seja perfeitamente única e contextualizada. O prompt efetivo para o agente `uuid-123` é uma composição de:

> "Incorpore a persona de **`persona.md`**. Seu conhecimento acumulado está em **`context.md`**. Siga as melhores práticas de **`recommendations.json`** e, crucialmente, não repita os erros de **`avoid_patterns.md`**. Sua tarefa atual é **`workspace/inbox/task-456.json`**."

Essa combinação de identidade, propósito, experiência e tarefa garante uma execução com o máximo de contexto e inteligência possível.