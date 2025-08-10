# Anatomia e Ciclo de Vida de um Agente Conductor

Este documento detalha a arquitetura padrão para qualquer agente operando dentro do ecossistema Conductor. Aderir a esta estrutura garante que todos os agentes sejam resilientes, com estado, auditáveis e interoperáveis com o Orquestrador.

## Princípios Fundamentais

1.  **Isolamento Total**: Um agente não tem conhecimento direto de outros agentes. Toda a comunicação é indireta, mediada pelo Orquestrador através de artefatos no sistema de arquivos.
2.  **Estado Persistente**: O conhecimento e o contexto de um agente sobrevivem a reinicializações. Agentes "aprendem" e mantêm sua especialização ao longo do tempo.
3.  **Resiliência**: Um agente deve ser capaz de se recuperar de uma falha e continuar o trabalho de onde parou, sem intervenção manual.
4.  **Auditabilidade**: Todas as ações e decisões tomadas por um agente são registradas em um histórico imutável, permitindo depuração e análise de causa raiz.
5.  **Comunicação por Contrato**: Agentes recebem tarefas e entregam resultados através de formatos de mensagem bem definidos ("Contratos"), garantindo a interoperabilidade.

## Gerenciamento de Identidade e Endereçamento de Agentes

Para operar em um ambiente com múltiplos projetos e microserviços, uma estratégia de endereçamento robusta é fundamental. O Conductor adota o padrão **"DNS com Escopo de Projeto"** para garantir unicidade, descoberta e governança.

### O Padrão: DNS com Escopo de Projeto

O princípio central é a separação entre o **Endereço Físico** de um agente (onde ele "mora" no sistema) e sua **Identidade Lógica** (como ele é "conhecido" e suas capacidades).

#### 1. Endereço Físico (Governança e Isolamento)

A localização de um agente no sistema de arquivos reflete sua "cidadania", garantindo que agentes de um projeto não interfiram em outros.

*   **Estrutura:** `agentes/{nome_do_projeto}/{nome_do_microservico}/{uuid_do_agente}/`
*   **Exemplo:** `agentes/develop/user-service/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/`
*   **Função:** O Orquestrador, ao operar em um determinado contexto de projeto, é restringido a interagir apenas com os agentes dentro do diretório daquele projeto. Isso cria uma fronteira de segurança e organização.

#### 2. Identidade Lógica (Descoberta e Capacidades)

Dentro do "endereço físico" do agente, um manifesto define suas capacidades de forma flexível e pesquisável.

*   **Artefato:** `.../{uuid_do_agente}/context/manifest.json`
*   **Conteúdo de Exemplo:**
    ```json
    {
      "uuid": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
      "human_name": "Java User Service Test Executor",
      "project": "develop",
      "microservice": "user-service",
      "tags": [
        "language:java",
        "purpose:test-executor",
        "framework:spring-boot",
        "supports_batching:true"
      ]
    }
    ```

#### 3. O Registro de Agentes (O "Servidor DNS")

Um componente central, o **Registro de Agentes** (`agent_registry.json`), indexa os manifestos de todos os agentes para permitir a descoberta rápida e com escopo definido.

*   **Estrutura do Registro (Particionada):**
    ```json
    {
      "develop": {
        "user-service": {
          "a1b2c3d4-e5f6...": {
            "tags": [ "language:java", "purpose:test-executor" ]
          }
        }
      }
    }
    ```
*   **Fluxo de Consulta:** O Orquestrador sempre consulta o registro com um escopo. Ex: "No projeto `develop`, microserviço `user-service`, encontre agentes com a tag `purpose:test-executor`".

## O Padrão "Caixa Postal do Agente"

Cada agente, em seu "endereço físico", segue o padrão de "Caixa Postal" para gerenciar seu estado e tarefas.

### Estrutura de Diretórios Padrão

```
.../{uuid_do_agente}/
    ├── 📥 inbox/              # Fila de entrada de tarefas.
    ├── 📤 outbox/             # Fila de saída de resultados.
    ├── 🧠 context/            # Memória de longo prazo e o manifest.json.
    ├── 📜 history/            # Log de auditoria de todas as ações.
    └── 🔒 .lock              # Arquivo de trava para controle de concorrência.
```

*Para detalhes sobre cada pasta, consulte a seção de Ciclo de Vida abaixo.*

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
