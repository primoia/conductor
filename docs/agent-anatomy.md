# Anatomia e Ciclo de Vida de um Agente Conductor

Este documento detalha a arquitetura padrão para qualquer agente operando dentro do ecossistema Conductor. Aderir a esta estrutura garante que todos os agentes sejam resilientes, com estado, auditáveis e interoperáveis com o Orquestrador.

## Princípios Fundamentais

1.  **Isolamento Total**: Um agente não tem conhecimento direto de outros agentes. Toda a comunicação é indireta, mediada pelo Orquestrador através de artefatos no sistema de arquivos.
2.  **Estado Persistente**: O conhecimento e o contexto de um agente sobrevivem a reinicializações. Agentes "aprendem" e mantêm sua especialização ao longo do tempo.
3.  **Resiliência**: Um agente deve ser capaz de se recuperar de uma falha e continuar o trabalho de onde parou, sem intervenção manual.
4.  **Auditabilidade**: Todas as ações e decisões tomadas por um agente são registradas em um histórico imutável, permitindo depuração e análise de causa raiz.
5.  **Comunicação por Contrato**: Agentes recebem tarefas e entregam resultados através de formatos de mensagem bem definidos ("Contratos"), garantindo a interoperabilidade.

## O Padrão "Caixa Postal do Agente"

Cada agente no sistema possui seu próprio diretório de trabalho isolado, que funciona como seu "escritório" ou "caixa postal". Esta estrutura é o alicerce para todos os princípios acima.

### Estrutura de Diretórios Padrão

```
agentes/
└── {agent-type}-{instance-id}/  (ex: agente-implementador-servico-01)
    ├── 📥 inbox/              # Fila de entrada de tarefas.
    ├── 📤 outbox/             # Fila de saída de resultados.
    ├── 🧠 context/            # Memória de longo prazo e conhecimento do agente.
    ├── 📜 history/            # Log de auditoria de todas as ações.
    └── 🔒 .lock              # Arquivo de trava para controle de concorrência.
```

### Detalhes dos Componentes

*   **`inbox/` (Caixa de Entrada)**
    *   **Propósito:** Fila de tarefas pendentes. O Orquestrador é o único ator que pode colocar "cartas" (arquivos de contrato/tarefa) aqui.
    *   **Formato:** Cada arquivo é um JSON representando uma única tarefa a ser executada.
    *   **Operação:** O agente consome as tarefas desta pasta, uma de cada vez.

*   **`outbox/` (Caixa de Saída)**
    *   **Propósito:** Local para depositar os resultados do trabalho concluído. O Orquestrador monitora esta pasta para coletar os resultados e acionar os próximos passos no workflow.
    *   **Formato:** Arquivos JSON representando o resultado de uma tarefa, sempre correlacionados com a tarefa de entrada.

*   **`context/` (Cérebro / Memória)**
    *   **Propósito:** Armazenar o estado interno e o conhecimento especializado do agente. Permite que o agente "aprenda" e melhore com o tempo.
    *   **Exemplos de Conteúdo:** `knowledge_base.json` com preferências de bibliotecas, padrões de código aprendidos, resumos de interações passadas, etc.

*   **`history/` (Arquivo Morto / Log de Auditoria)**
    *   **Propósito:** Manter um registro cronológico e imutável de todas as ações significativas tomadas pelo agente. Essencial para depuração.
    *   **Formato:** Arquivos de log com timestamp (ex: `2025-08-09T12-30-00.log`), detalhando a tarefa recebida, a análise feita e o resultado produzido.

*   **`.lock` (A Tranca na Porta)**
    *   **Propósito:** Um mecanismo de semáforo simples para garantir que apenas um processo esteja operando no "escritório" do agente por vez.
    *   **Operação:** O processo do agente cria este arquivo ao iniciar seu ciclo de trabalho e o remove ao concluir. Se o arquivo já existir, o processo sabe que outra instância está ativa e deve aguardar ou terminar.

## Ciclo de Vida de Execução de uma Tarefa

Um agente bem-comportado segue um ciclo de vida rigoroso para garantir a resiliência.

1.  **Ativação (Wake Up):** O processo do agente é iniciado.
2.  **Trava (Lock):** Tenta criar o arquivo `.lock`. Se falhar, sai.
3.  **Verificar Caixa de Saída (Check Outbox):** Verifica se há resultados na `outbox` que o Orquestrador ainda não coletou.
4.  **Verificar Caixa de Entrada (Check Inbox):** Procura por uma nova tarefa na `inbox/`. Se vazia, entra em modo de espera ou termina.
5.  **Carregar Contexto (Load Context):** Lê os arquivos da pasta `context/` para carregar sua memória e conhecimento.
6.  **Iniciar Trabalho (Process Task):**
    *   Move a tarefa da `inbox/` para um estado "em processamento".
    *   Registra o início da tarefa no `history/`.
    *   Executa sua lógica de negócio para processar a tarefa.
    *   Registra as decisões chave no `history/`.
7.  **Depositar Resultado (Deposit Result):** Coloca o arquivo de resultado na `outbox/`.
8.  **Atualizar Contexto (Update Context):** Salva qualquer novo aprendizado na pasta `context/`.
9.  **Limpeza (Clean Up):** Remove a tarefa processada do estado "em processamento".
10. **Destrava (Unlock):** Remove o arquivo `.lock`.
11. **Repetir:** Volta ao Passo 3.

## Padrões de Agentes para Tarefas em Larga Escala

Para tarefas que envolvem um grande número de itens (ex: executar 400 testes), o Orquestrador pode adotar diferentes estratégias, utilizando tipos de agentes especializados.

### Modelo A: Hiper-Especialização (Agentes de Tarefa Única)

Neste modelo, o Orquestrador instancia um grande número de agentes efêmeros, onde cada agente é responsável por uma única e minúscula parte do trabalho.

*   **Conceito:** 400 testes a serem executados resultam em 400 instâncias de `Agente-Executor-de-Teste`, cada um com um único teste em seu contexto.
*   **Prós:**
    *   **Paralelismo Massivo:** Permite a maior distribuição de carga possível, ideal para nuvem.
    *   **Resiliência Máxima:** A falha de um agente não afeta nenhum outro.
*   **Contras:**
    *   **Ineficiência de Recursos:** Inviável para tarefas com alto custo de setup (ex: iniciar um contexto Spring), pois o custo seria multiplicado por 400.
    *   **Alta Sobrecarga de Gerenciamento:** O Orquestrador precisa gerenciar um número enorme de agentes.
*   **Caso de Uso Ideal:** Testes unitários puros e outras tarefas com custo de inicialização próximo de zero.

### Modelo B: Especialista em Lotes (Agentes de Lote)

Neste modelo, um único agente especializado é projetado para receber um array de tarefas e processá-las em um lote.

*   **Conceito:** Os 400 testes são agrupados em um único arquivo de tarefa (um array JSON) e enviados para a `inbox` de um `Agente-Executor-de-Lotes-Spring`.
*   **Prós:**
    *   **Eficiência de Recursos Máxima:** O custo de setup (iniciar o contexto Spring) é pago apenas uma vez.
    *   **Baixa Sobrecarga de Gerenciamento:** O Orquestrador lida com uma única tarefa e um único resultado.
*   **Contras:**
    *   **Paralelismo Limitado:** A velocidade é limitada pela capacidade de um único agente/processo.
    *   **Resiliência Fraca:** Uma falha em um item do lote pode comprometer o lote inteiro, exigindo lógica de tratamento de erro parcial muito mais complexa dentro do agente.
*   **Caso de Uso Ideal:** Testes de integração ou componente que compartilham um contexto de setup caro.

### O Orquestrador como Estrategista

A arquitetura do Conductor não força a escolha de um modelo. A inteligência reside no **Orquestrador**, que deve atuar como um **Estrategista de Execução**. Com base na natureza da tarefa, ele deve decidir dinamicamente se a melhor abordagem é a distribuição em massa (Modelo A) ou o agrupamento em lotes (Modelo B).

## Considerações e Desafios Futuros

Esta arquitetura é robusta, mas apresenta desafios que guiarão nossa evolução futura.

1.  **Escalabilidade de Agentes "Trabalhadores":** O modelo de um agente por "escritório" pode ser um gargalo para tarefas massivamente paralelas (ex: executar 400 testes). Pode ser necessário projetar "super-agentes" que possam gerenciar paralelismo interno, ou um mecanismo para criar dinamicamente um grande número de agentes temporários.

2.  **O Orquestrador como Ponto de Afunilamento:** O Orquestrador, como distribuidor central de tarefas, é um potencial ponto de falha e gargalo. Futuras versões do Conductor podem precisar de um Orquestrador distribuído ou com alta disponibilidade.

3.  **Gerenciamento do Ciclo de Vida do Contexto:** As pastas `context/` e `history/` crescerão indefinidamente. Será necessário implementar estratégias de sumarização, compressão e arquivamento, possivelmente através de "Agentes-Zeladores" especializados, para garantir a performance do sistema a longo prazo.