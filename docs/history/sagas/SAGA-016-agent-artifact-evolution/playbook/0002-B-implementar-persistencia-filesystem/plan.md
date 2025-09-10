# Plano: 0002-B - Infra: Persistência de Artefatos (Filesystem)

## Contexto

Com as estruturas de dados definidas no plano anterior, o próximo passo é implementar a camada de persistência para o backend `filesystem`. O objetivo é criar repositórios responsáveis por ler e escrever cada artefato de agente em arquivos físicos no workspace.

Cada tipo de artefato (`Definition`, `Persona`, `Playbook`, etc.) terá seu próprio "repositório" (na forma de uma classe de serviço) que encapsula a lógica de serialização (para YAML/JSON) e manipulação de arquivos.

Vamos criar um novo módulo `src/infrastructure/filesystem_storage.py` para abrigar toda essa lógica, mantendo o código de infraestrutura isolado do domínio.

## Checklist de Verificação

- [x] Criar um novo arquivo `src/infrastructure/filesystem_storage.py`.
- [x] Implementar uma classe `FileSystemStorage` que recebe o caminho base do workspace do agente no construtor.
- [x] Na classe, implementar um método `save_definition(definition: AgentDefinition)` que salva `definition.yaml`.
- [x] Implementar um método `load_definition() -> AgentDefinition` que carrega `definition.yaml`.
- [x] Implementar métodos `save_persona(persona: AgentPersona)` e `load_persona() -> AgentPersona` para `persona.md`.
- [x] Implementar métodos `save_playbook(playbook: AgentPlaybook)` e `load_playbook() -> AgentPlaybook` para `playbook.yaml`.
- [x] Implementar métodos `save_knowledge(knowledge: AgentKnowledge)` e `load_knowledge() -> AgentKnowledge` para `knowledge.json`.
- [x] Implementar um método `append_to_history(entry: HistoryEntry)` que adiciona uma nova linha ao `history.log` (formato JSON Lines).
- [x] Implementar um método `load_history() -> List[HistoryEntry]` que lê todas as linhas do `history.log`.
- [x] Implementar métodos `save_session(session: AgentSession)` e `load_session() -> AgentSession` para `session.json`.
