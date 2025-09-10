### Plano de Execução: Estágio 20 - Testes Unitários para `AgentExecutor`

#### Contexto Arquitetônico

O `AgentExecutor` é o nosso "worker" stateless, responsável pela execução de uma única tarefa. Sua lógica interna, embora focada, é crítica: ele interage com o `PromptEngine` para construir o prompt e com o cliente LLM para obter a resposta. Esta tarefa consiste em escrever testes unitários para validar essa interação e a lógica de empacotamento do resultado.

#### Propósito Estratégico

O objetivo é garantir a confiabilidade do nosso componente de execução. Testar o `AgentExecutor` de forma isolada, com o `PromptEngine` e o cliente LLM mockados, nos permite verificar se a orquestração interna da execução está correta, independentemente da complexidade da engenharia de prompt ou da resposta do LLM. Isso cria uma base sólida para a confiabilidade de todas as execuções de agentes no sistema.

#### Checklist de Execução

- [x] Criar um novo arquivo de teste em `tests/core/test_agent_executor.py`.
- [x] Usar `pytest` e `unittest.mock`.
- [x] Escrever um teste para o cenário de sucesso:
    -   Instanciar o `AgentExecutor` com dependências mockadas (`PromptEngine`, `LLMClient`).
    -   Chamar o método `run`.
    -   Verificar se o `PromptEngine` foi chamado com os argumentos corretos (input do usuário, histórico).
    -   Verificar se o cliente LLM foi chamado com o prompt construído pelo `PromptEngine`.
    -   Verificar se o `TaskResultDTO` retornado contém o status `success` e a resposta do LLM mockado.
- [x] Escrever um teste para o cenário de falha, onde o cliente LLM lança uma exceção.
- [x] Verificar se o `TaskResultDTO` retornado contém o status `error` e a mensagem de erro correta.
- [x] Atingir uma cobertura de teste de pelo menos 90% para `src/core/agent_executor.py`.
