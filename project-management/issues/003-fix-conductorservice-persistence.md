# Plano 003: Implementar Persistência no ConductorService

## 1. Contexto e Problema

O code review anterior (Plano 002) revelou que, embora a camada de repositório (`IStateRepository` e `FileSystemStateRepository`) tenha sido corretamente refatorada, o `ConductorService` não a utiliza para salvar o estado de um agente após a execução de uma tarefa. Ele apenas carrega dados, mas não persiste as alterações, tornando os agentes "sem memória".

## 2. Objetivo

Implementar a lógica de persistência de estado que falta no método `execute_task` do `ConductorService`, garantindo que as alterações na sessão, conhecimento e histórico do agente sejam salvas após cada tarefa bem-sucedida.

## 3. Plano de Execução

**Local:** `src/core/conductor_service.py`

**Checklist:**

- [ ] Localizar o método `execute_task`.
- [ ] Dentro do bloco `try`, após a linha `result = executor.run(task)`, adicionar uma verificação para `if result.status == "success":`.
- [ ] Dentro deste `if`, adicionar a lógica para persistir os dados contidos no objeto `result`:
  - [ ] Chamar `self.repository.save_session(task.agent_id, result.updated_session)` para salvar o estado da sessão atualizada.
  - [ ] Chamar `self.repository.save_knowledge(task.agent_id, result.updated_knowledge)` para salvar a memória de conhecimento atualizada.
  - [ ] Chamar `self.repository.append_to_history(task.agent_id, result.history_entry)` para adicionar o registro da tarefa ao histórico.
- [ ] Garantir que os dados corretos do `TaskResultDTO` (`updated_session`, `updated_knowledge`, `history_entry`) sejam passados para os métodos do repositório.

## 4. Critérios de Aceitação

1.  Após a execução bem-sucedida de uma tarefa via `ConductorService`, os arquivos `session.json`, `knowledge.json` e `history.log` no diretório do agente (dentro de `.conductor_workspace`) são criados/atualizados.
2.  A lógica de salvamento só é acionada se o `result.status` for `"success"`.
3.  O `TaskResultDTO` deve ser adaptado, se necessário, para conter os campos `updated_session`, `updated_knowledge`, e `history_entry` para que o `ConductorService` possa acessá-los.
