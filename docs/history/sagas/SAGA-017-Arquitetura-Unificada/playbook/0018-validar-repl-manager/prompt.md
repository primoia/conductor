# Especificação Técnica e Plano de Execução: 0018-validar-repl-manager

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa garante que a refatoração do núcleo da aplicação não introduziu regressões na camada de interface do usuário interativa. Validar que o `REPLManager` continua funcionando perfeitamente confirma o sucesso da "cirurgia", provando que a nova arquitetura pode ser integrada de forma transparente sem degradar a experiência do usuário.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Foco em Validação:** Esta tarefa é primariamente de validação. A expectativa é que **nenhuma mudança de código** seja necessária no `REPLManager`, pois ele interage com os métodos públicos dos CLIs que foram preservados.
- **Não é um Teste Unitário:** Esta não é uma tarefa para escrever testes unitários do `REPLManager`. É uma tarefa de **teste de integração de alto nível** para verificar o comportamento do sistema como um todo no modo interativo.
- **Execução Manual:** Dada a natureza interativa do REPL, a execução deste plano envolve um roteiro de teste manual detalhado.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Esta tarefa não envolve escrita de código de produção. Você deve executar o seguinte **roteiro de teste manual** e garantir que todos os passos sejam concluídos com sucesso.

##### **Roteiro de Teste de Validação**

**Parte 1: Validação com `admin.py`**

1.  **Inicie o REPL:** No seu terminal, execute o comando:
    ```bash
    poetry run python src/cli/admin.py --agent CodeReviewer_Agent --repl
    ```
2.  **Verifique a Inicialização:** A saída deve indicar que o `AdminCLI` foi inicializado e está usando o `ConductorService`.
3.  **Envie uma Mensagem:** No prompt do REPL, digite: `Olá` e pressione Enter.
4.  **Verifique a Resposta:** Você deve receber uma resposta simulada que foi processada pelo `ConductorService` e pelo `AgentExecutor` (ex: `Resposta simulada para o prompt: ...`).
5.  **Teste o Comando de Debug:** Digite `:debug` e pressione Enter. A saída deve mostrar o contexto do `AdminCLI` refatorado.
6.  **Encerre a Sessão:** Digite `:quit` e pressione Enter. O programa deve encerrar graciosamente.

**Parte 2: Validação com `agent.py`**

1.  **Inicie o REPL:** No seu terminal, execute o comando:
    ```bash
    poetry run python src/cli/agent.py --environment develop --project desafio-meli --agent CodeReviewer_Agent --repl
    ```
2.  **Verifique a Inicialização:** A saída deve indicar que o `AgentCLI` foi inicializado e está usando o `ConductorService`.
3.  **Envie uma Mensagem:** No prompt do REPL, digite: `Teste` e pressione Enter.
4.  **Verifique a Resposta:** Você deve receber uma resposta simulada do `ConductorService`.
5.  **Encerre a Sessão:** Digite `:quit` e pressione Enter.

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando você puder confirmar que todos os passos do roteiro de teste manual foram executados e produziram os resultados esperados.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
