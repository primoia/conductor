### Plano de Execução: Estágio 9 - Integração do `PromptEngine`

#### Contexto Arquitetônico

Temos o `AgentExecutor` que atua como nosso "worker" stateless. No entanto, sua implementação atual do prompt é um placeholder. O componente legado `PromptEngine` contém a lógica valiosa para carregar a `persona.md`, o `playbook.yaml` e outros artefatos, e formatá-los em um prompt de sistema rico em contexto. Esta tarefa consiste em refatorar ou reutilizar o `PromptEngine` para que ele possa ser injetado e utilizado pelo `AgentExecutor`.

#### Propósito Estratégico

O objetivo é reaproveitar a lógica de engenharia de prompt existente, que é uma parte crítica da "personalidade" e do desempenho de um agente. Ao integrar o `PromptEngine` ao `AgentExecutor`, garantimos que a nova arquitetura mantenha a mesma qualidade e consistência de prompts da arquitetura legada, ao mesmo tempo que a encapsulamos dentro do nosso novo modelo de execução stateless. Isso evita a reescrita de código e garante a compatibilidade comportamental.

#### Checklist de Execução

- [ ] Analisar o `PromptEngine` legado para identificar as modificações necessárias para que ele funcione de forma stateless (se necessário).
- [ ] O `PromptEngine` provavelmente precisará receber os caminhos para os artefatos em seu construtor, em vez de descobri-los.
- [ ] Modificar o `AgentExecutor` em `src/core/agent_executor.py`.
- [ ] O construtor do `AgentExecutor` deve instanciar o `PromptEngine`.
- [ ] O método `run` do `AgentExecutor` deve usar o `PromptEngine` para construir o prompt final, passando o input do usuário e o histórico da conversa (se aplicável).
- [ ] Remover os placeholders de `PromptEngine` do `AgentExecutor`.
