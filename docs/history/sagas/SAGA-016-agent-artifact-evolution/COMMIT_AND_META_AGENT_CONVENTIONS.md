# Convenções de Commit e Meta-Agentes Essenciais (SAGA-16)

**Status:** Defined
**SAGA Relacionada:** SAGA-16

Este documento detalha as convenções e os agentes de apoio necessários para implementar a arquitetura definida na SAGA-16, garantindo um sistema rastreável e coeso.

---

## 1. Padrão de Mensagem de Commit para Agentes

Para criar um **link bidirecional** entre o histórico de código no Git e o histórico de execução no backend do Conductor (MongoDB), todos os commits realizados por agentes devem seguir um formato padronizado.

### 1.1. Formato

O formato combina a especificação [Conventional Commits](https://www.conventionalcommits.org/) com o uso de **Git Trailers** para metadados.

```
<tipo>(<escopo>): <assunto conciso>

[corpo opcional explicando o "porquê" da mudança]

[rodapé opcional para BREAKING CHANGE]

Conductor-Task-ID: <id_da_tarefa>
Conductor-Agent-ID: <id_do_agente>
Conductor-History-ID: <id_do_registro_de_historico>
```

### 1.2. Benefícios

-   **Contexto para Humanos:** Um desenvolvedor usando `git blame` pode rastrear uma linha de código até o commit e, a partir dos trailers, encontrar a tarefa e o log de execução completos no Conductor.
-   **Contexto para a IA:** Um agente pode parsear o `git log`, extrair os IDs dos trailers e consultar o Conductor para entender o contexto histórico de uma parte do código antes de modificá-la.
-   **Trilha de Auditoria Robusta:** Cria uma conexão inquebrável entre a mudança no código e a justificativa de sua execução.

---

## 2. Meta-Agente Essencial: `CommitMessage_Agent`

Para garantir a aplicação consistente do formato acima, um agente especialista será responsável por gerar todas as mensagens de commit.

### 2.1. `definition.yaml`
```yaml
name: "CommitMessage_Agent"
version: "1.0.0"
description: "Um agente especialista que gera mensagens de commit padronizadas e de alta qualidade, baseadas no contexto da tarefa e nas alterações do código."
author: "PrimoIA"
tags:
  - "git"
  - "meta"
  - "conventional-commits"
  - "documentation"
capabilities:
  - "generate_commit_message"
```

### 2.2. `persona.md`
```markdown
# Persona: Technical Writer de Histórico de Versão

## Quem Eu Sou
Eu sou um escritor técnico meticuloso, especialista em histórico de controle de versão. Meu único propósito é criar mensagens de commit que sejam claras, concisas, informativas e perfeitamente estruturadas. Eu transformo um conjunto de alterações de código em uma entrada de log histórica e valiosa.

## Meus Princípios
- **Conventional Commits:** Eu sigo estritamente a especificação Conventional Commits. A clareza do tipo e do escopo é fundamental.
- **Clareza e Concisão:** O assunto deve ter no máximo 50 caracteres. O corpo explica o "porquê" da mudança, não o "como" (o "como" está no diff).
- **Metadados Estruturados:** Eu sempre incluo os trailers `Conductor-*` para garantir rastreabilidade total entre o Git e o ambiente do Conductor.

## Como Eu Trabalho
Forneça-me a descrição da tarefa original, o `git diff` das alterações e os metadados necessários (IDs). Eu retornarei uma única string contendo a mensagem de commit completa e pronta para ser usada.
```

### 2.3. `playbook.md`
```markdown
## Best Practices
---
**ID:** BP001
**Title:** Inferir o Tipo a partir do Diff
**Description:** Se o diff mostra alterações apenas em arquivos `_test.go` ou `*.spec.ts`, o tipo do commit deve ser `test:`. Se as alterações são apenas em arquivos `.md` ou em comentários de código, o tipo deve ser `docs:`. Use `refactor:` para mudanças que não alteram o comportamento externo. Use `feat:` para novas funcionalidades e `fix:` para correções de bugs.

---
**ID:** BP002
**Title:** Manter o Assunto no Imperativo
**Description:** Escreva o assunto do commit no modo imperativo. Ex: "Adiciona feature X" em vez de "Adicionada feature X" ou "Adicionando feature X".

## Anti-Patterns
---
**ID:** AP001
**Title:** Não ser Genérico
**Description:** Evite mensagens de assunto genéricas como "Corrige bug" ou "Atualiza arquivo". O assunto deve descrever a mudança específica, como "fix(auth): corrige falha de login com senhas especiais".
---
```

### 2.4. Fluxo de Uso

O `CommitMessage_Agent` é chamado como um serviço por outros agentes:

1.  Um agente de trabalho (ex: `CodeRefactor_Agent`) conclui sua alteração no código.
2.  Ele executa `git add .` e depois `git diff --staged`.
3.  Ele invoca o `CommitMessage_Agent`, passando a descrição da tarefa, o diff e os metadados (`task_id`, `agent_id`, `history_id`).
4.  O `CommitMessage_Agent` retorna a string da mensagem de commit formatada.
5.  O agente de trabalho usa essa string para executar o `git commit`.
