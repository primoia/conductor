# Plano: 0008-H - Meta-Agentes: `CommitMessage_Agent`

## Contexto

Com a infraestrutura principal se solidificando, podemos começar a construir os Meta-Agentes. O primeiro e mais simples é o `CommitMessage_Agent`. Este agente é um especialista que recebe um `diff` de código e gera uma mensagem de commit seguindo o padrão de Conventional Commits e adicionando os trailers do Conductor.

Este plano foca em criar a definição e a persona deste agente. A lógica de execução será responsabilidade do orquestrador (a ser implementado depois), que saberá como invocar agentes.

## Checklist de Verificação

- [ ] Criar a estrutura de diretórios para o novo agente: `.conductor_workspace/agents/CommitMessage_Agent/`.
- [ ] Criar o arquivo `definition.yaml` para o `CommitMessage_Agent`, com `name`, `version`, `description`, `author`, `tags: ["meta", "git"]` e `capabilities: ["generate_commit_message"]`.
- [ ] O `allowed_tools` para este agente pode ser vazio, pois sua lógica é puramente de transformação de texto baseada no LLM.
- [ ] Criar o arquivo `persona.md` detalhando o propósito do agente: ser um especialista em controle de versão que cria mensagens de commit claras, concisas e padronizadas a partir de um `diff`.
- [ ] A persona deve instruir o agente a seguir estritamente o formato: `type(scope): subject`, corpo opcional, e os trailers `Conductor-Task-ID`, `Conductor-Agent-ID`, `Conductor-History-ID`.
