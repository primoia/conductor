# Referência de Artefatos do Agente

Este documento é a fonte única da verdade sobre a estrutura e o propósito de cada arquivo que compõe uma **Instância de Agente** no Conductor.

## 1. Visão Geral

Uma Instância de Agente é uma entidade autocontida que possui dois tipos de artefatos:

*   **Artefatos de Definição (Definition Artifacts):** Descrevem a identidade, o comportamento e as "lições aprendidas" do agente. São semi-estáticos e modificados principalmente por humanos (diretamente ou através de um meta-agente). São eles: `definition.yaml`, `persona.md`, e `playbook.md`.
*   **Artefatos de Estado (State Artifacts):** Registram a experiência e o contexto de execução do agente. São dinâmicos e modificados exclusivamente pelo sistema durante a operação. São eles: `memory.json` e `session.json`.

---

## 2. `definition.yaml`

*   **Propósito:** Fornecer metadados estruturados para que o sistema (especialmente o Orquestrador) possa identificar, filtrar e entender as capacidades de um agente de forma rápida e programática.
*   **Formato:** YAML
*   **Quem Utiliza:** Primariamente a Máquina (Orquestrador).
*   **Ciclo de Vida:** Criado durante o onboarding a partir de um template. Modificado raramente, geralmente por um humano para atualizar a versão ou adicionar novas capacidades.

### Estrutura

```yaml
# ID único do agente. Corresponde ao nome do diretório.
id: "KotlinEntityCreator_Agent" 

# Nome legível para exibição.
name: "Kotlin Entity Creator Agent"

# Descrição curta para listagens e logs.
description: "Um agente especialista na criação de classes de entidade Kotlin com anotações JPA."

# Versionamento semântico do agente.
version: "1.0.0"

# Palavras-chave para filtragem. O Orquestrador usa isso para encontrar candidatos.
tags: ["kotlin", "backend", "database", "jpa"]

# Lista explícita das "ferramentas" ou "habilidades" que este agente possui.
# Usado pelo Orquestrador para uma correspondência mais precisa de tarefas.
capabilities:
  - "create_kotlin_entity"
  - "add_jpa_annotations"
  - "generate_dto_from_entity"

# Permissões explícitas para as Tools do sistema.
# Um agente só pode usar as ferramentas listadas aqui.
allowed_tools:
  - "file.write"
  - "file.read"
```

---

## 3. `persona.md`

*   **Propósito:** Definir a "personalidade", o estilo de comunicação, as responsabilidades e o escopo de atuação do agente. É um documento narrativo que guia o LLM em seu comportamento e na tomada de decisões semânticas.
*   **Formato:** Markdown
*   **Quem Utiliza:** Primariamente o LLM e o Humano (para entender e afinar o agente).
*   **Ciclo de Vida:** Criado durante o onboarding. Pode ser afinado por um humano através de um meta-agente (`AgentTuner_Agent`) para melhorar o comportamento do agente.

### Estrutura

````markdown
# Persona: Kotlin Entity Creator

## Perfil

Eu sou um agente especialista focado exclusivamente no ecossistema de persistência de dados do Kotlin com Spring Data JPA. Minha principal função é criar código limpo, idiomático e livre de erros para entidades, DTOs e repositórios.

## Minhas Responsabilidades

1.  **Criação de Entidades:** Recebo uma descrição de alto nível de uma entidade e gero a classe de dados (`data class`) Kotlin correspondente com as anotações JPA (`@Entity`, `@Id`, `@Column`, etc.).
2.  **Geração de DTOs:** A partir de uma entidade existente, posso gerar um DTO (Data Transfer Object) para evitar a exposição de detalhes de implementação na API.
3.  **Validação de Relacionamentos:** Eu entendo e aplico corretamente os relacionamentos JPA como `@OneToMany` e `@ManyToOne`.

## Meu Comportamento

*   **Proativo:** Se uma instrução for ambígua, farei perguntas para esclarecer os requisitos antes de escrever o código.
*   **Focado em Qualidade:** Sigo estritamente as melhores práticas definidas no meu `playbook.md`.
*   **Conciso:** Minha comunicação é direta e focada na tarefa em questão.
````

---

## 4. `playbook.md`

*   **Propósito:** Servir como um banco de conhecimento estruturado e incremental de "lições aprendidas". Ele guia o LLM sobre o que fazer (`Best Practices`) e o que não fazer (`Anti-Patterns`), permitindo um ciclo de melhoria contínua baseado no feedback humano.
*   **Formato:** Markdown (com estrutura específica)
*   **Quem Utiliza:** Primariamente o LLM e o Humano.
*   **Ciclo de Vida:** Criado com um conjunto inicial de regras. É o artefato mais dinâmico da definição, sendo constantemente atualizado por humanos (via `AgentTuner_Agent`) à medida que novos padrões e erros são identificados.

### Estrutura

```markdown
## Best Practices

---
**ID:** BP001
**Title:** Usar Tipos de Coleção Apropriados
**Description:** Para relacionamentos `*-to-many`, sempre use `Set<T>` em vez de `List<T>` para evitar problemas de performance e duplicatas ao usar JPA.

---
**ID:** BP002
**Title:** Preferir a API Java Time
**Description:** Para campos de data e hora, sempre use `java.time.LocalDate` ou `java.time.LocalDateTime`, pois são imutáveis e mais precisos que a antiga `java.util.Date`.

## Anti-Patterns

---
**ID:** AP001
**Title:** Evitar `FetchType.EAGER` em Coleções
**Description:** Nunca use `fetch = FetchType.EAGER` em relacionamentos `@OneToMany` ou `@ManyToMany`. Isso causa o problema N+1 e degrada severamente a performance. O padrão (`LAZY`) é quase sempre a melhor escolha.
---
```

---

## 5. `memory.json`

*   **Propósito:** Manter um registro de longo prazo de todas as tarefas executadas pelo agente. Serve como um log de auditoria e uma base de dados para futuras análises e aprendizado.
*   **Formato:** JSON
*   **Quem Utiliza:** Exclusivamente a Máquina.
*   **Ciclo de Vida:** Criado na primeira vez que uma tarefa é concluída (ou falha). Novas entradas são adicionadas ao final do arquivo (ou na coleção do DB) a cada tarefa executada.

### Estrutura

```json
[
  {
    "taskId": "task-001-20250910T100000Z",
    "startTime": "2025-09-10T10:00:00Z",
    "endTime": "2025-09-10T10:01:30Z",
    "status": "completed",
    "userInput": "Crie uma entidade User com os campos id, name e email.",
    "summary": "Criei com sucesso a entidade User em 'src/main/kotlin/com/example/User.kt', incluindo anotações JPA para os campos id, name e email.",
    "tool_calls": [
      {
        "tool_name": "file.write",
        "params": {
          "path": "src/main/kotlin/com/example/User.kt",
          "content": "..."
        },
        "status": "success",
        "timestamp": "2025-09-10T10:01:25Z"
      }
    ]
  }
]
```

---

## 6. `session.json`

*   **Propósito:** Armazenar o estado volátil e de curto prazo da tarefa atualmente em execução. Ele permite que o agente "lembre" o que está fazendo entre os turnos de uma conversa, especialmente em modo interativo (`--repl`).
*   **Formato:** JSON
*   **Quem Utiliza:** Exclusivamente a Máquina.
*   **Ciclo de Vida:** Criado no início de uma tarefa. Seu conteúdo é constantemente lido e atualizado durante a execução da tarefa. É (ou deveria ser) limpo ou arquivado após a conclusão da tarefa.

### Estrutura

```json
{
  "currentTaskId": "task-002-20250910T110000Z",
  "status": "in_progress",
  "history": [
    {
      "role": "user",
      "content": "Agora adicione um campo 'lastLogin' do tipo LocalDateTime."
    },
    {
      "role": "assistant",
      "content": "Entendido. Para qual arquivo devo adicionar este campo?"
    }
  ],
  "scratchpad": {
    "target_file": "src/main/kotlin/com/example/User.kt",
    "field_to_add": {
      "name": "lastLogin",
      "type": "LocalDateTime"
    }
  }
}
```
