# Plano: 0001-A - Fundação: Estruturas de Dados dos Artefatos

## Contexto

Este é o primeiro e mais crucial passo na implementação da nova arquitetura. Nosso objetivo é traduzir o `SAGA-016-FINAL-PLAN.md` em estruturas de dados Python concretas e fortemente tipadas. Vamos usar `dataclasses` para garantir imutabilidade e clareza.

A implementação correta dessas estruturas é fundamental, pois todo o sistema de persistência e a lógica de negócios dependerão delas.

Este plano foca exclusivamente na **definição** das classes de dados, sem qualquer lógica de persistência ou de negócios. Elas devem residir em um novo módulo `src/core/domain.py` para estabelecer uma camada de domínio clara.

## Checklist de Verificação

- [ ] Criar um novo arquivo `src/core/domain.py`.
- [ ] No arquivo `src/core/domain.py`, importar `dataclass` e outros tipos necessários de `typing`.
- [ ] Definir a dataclass `AgentDefinition` com os campos: `name`, `version`, `schema_version`, `description`, `author`, `tags` (List[str]), `capabilities` (List[str]), `allowed_tools` (List[str]).
- [ ] Definir a dataclass `AgentPersona` com o campo `content` (str).
- [ ] Definir as dataclasses `PlaybookBestPractice` e `PlaybookAntiPattern`, ambas com `id`, `title`, e `description`.
- [ ] Definir a dataclass `AgentPlaybook` com os campos `best_practices` (List[PlaybookBestPractice]) e `anti_patterns` (List[PlaybookAntiPattern]).
- [ ] Definir a dataclass `KnowledgeItem` com os campos `summary`, `purpose`, e `last_modified_by_task`.
- [ ] Definir a dataclass `AgentKnowledge` com o campo `artifacts` (Dict[str, KnowledgeItem]).
- [ ] Definir a dataclass `HistoryEntry` com os campos `_id`, `agent_id`, `task_id`, `status`, `summary`, e `git_commit_hash`.
- [ ] Definir a dataclass `AgentSession` com o campo `current_task_id` e `state` (Dict).
