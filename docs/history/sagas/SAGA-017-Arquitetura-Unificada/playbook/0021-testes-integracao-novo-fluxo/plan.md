### Plano de Execução: Estágio 21 - Testes de Integração do Novo Fluxo

#### Contexto Arquitetônico

Com os testes unitários garantindo a corretude das peças individuais, precisamos agora validar se elas funcionam juntas. Esta tarefa consiste em escrever testes de integração que exercitem o fluxo completo da nova arquitetura, desde a chamada de um CLI refatorado até a interação com um backend de armazenamento real (tanto o `filesystem` quanto o `mongodb` do `docker-compose`).

#### Propósito Estratégico

O objetivo é garantir que a "fiação" entre os componentes está correta. Testes de integração validam que o `ConductorService` interage corretamente com o repositório, que o `AgentExecutor` é instanciado com os dados corretos, e que o resultado final é o esperado. Estes testes são a nossa maior garantia de que a "cirurgia" foi um sucesso e que o sistema como um todo é funcional.

#### Checklist de Execução

- [ ] Criar um novo arquivo de teste em `tests/e2e/test_full_flow.py`.
- [ ] O teste deve usar o ambiente do `docker-compose` (definido na Fase II) para ter um `mongodb` real disponível.
- [ ] Escrever um teste que usa o `ConductorService` para interagir com o backend `filesystem`.
    -   O teste deve criar uma estrutura de agente mock no filesystem.
    -   Chamar `discover_agents` e `execute_task`.
    -   Verificar se o resultado foi processado corretamente.
- [ ] Escrever um teste similar que configura o `ConductorService` para usar o backend `mongodb`.
    -   O teste deve inserir um documento de agente mock no MongoDB.
    -   Chamar `discover_agents` e `execute_task`.
    -   Verificar o resultado.
- [ ] Estes testes não devem mockar o `ConductorService` nem o repositório, apenas o cliente LLM.
