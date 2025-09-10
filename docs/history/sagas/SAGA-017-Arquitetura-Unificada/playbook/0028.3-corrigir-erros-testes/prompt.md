# Especificação Técnica e Plano de Execução: 0028.3-corrigir-erros-testes

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa restaurar a estabilidade da suíte de testes, abordando múltiplos erros e falhas introduzidos por refatorações anteriores. Uma suíte de testes funcional é essencial para a qualidade e confiabilidade do projeto.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve implementar as seguintes correções:

1.  **`src/ports/state_repository.py`**: Adicionar o método `list_agents` à interface `IStateRepository` (se ainda não estiver lá) e garantir que as implementações concretas (`FileStateRepository`, `MongoStateRepository`) e mocks (`MockStateRepository`) implementem-no, retornando uma lista vazia por padrão.

2.  **`src/core/domain.py`**: Remover a definição duplicada da classe `AgentDefinition`. Mantenha apenas a versão que não espera `agent_id` no construtor (`name`, `version`, `schema_version`, `description`, `author`, `tags`, `capabilities`, `allowed_tools`).

3.  **`tests/core/test_agent_executor.py`**: Ajustar o fixture `mock_dependencies` para criar `AgentDefinition` sem `agent_id` no construtor, e passar `agent_id` como um atributo separado se necessário para o teste.

4.  **`tests/e2e/test_full_flow.py`**: Ajustar a criação de `AgentDefinition` no fixture `filesystem_service` para não passar `agent_id` no construtor.

5.  **`tests/test_core.py`**: Ajustar `MockStateRepository` para implementar `list_agents` e `load_state` (retornando `[]` e `{}` respectivamente). Ajustar `AgentDefinition` no `test_embody_agent_success` para corresponder à nova estrutura.

6.  **`src/infrastructure/persistence/state_repository.py`**: Implementar o método `list_agents` em `FileStateRepository` e `MongoStateRepository` (retornando `[]`).

7.  **`tests/e2e/test_containerized_service.py`**: Substituir `docker-compose` por `docker compose` (com espaço) nos comandos `subprocess.run` para compatibilidade com versões mais recentes do Docker.

8.  **`tests/core/test_conductor_service.py`**: Ajustar a asserção em `test_load_tools_invalid_plugin_path` para verificar o `logger.error` em vez de `print`.

9.  **`src/core/prompt_engine.py`**: Revisar a lógica de `load_context` e `_load_agent_config` para garantir que `agent.yaml` e `persona.md` sejam carregados corretamente e que as exceções sejam lançadas apenas quando apropriado.

10. **`tests/core/test_prompt_engine.py`**: Revisar os testes que falharam (`test_prompt_engine_fails_on_missing_config`, `test_prompt_engine_fails_on_missing_persona`, `test_build_prompt_without_loaded_context`, `test_validate_config_missing_required_fields`) para garantir que eles testam o comportamento esperado da nova lógica de `PromptEngine`.

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
