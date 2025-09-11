# Plano 005: Corrigir Nome do Arquivo de Definição no Repositório

## 1. Contexto e Problema

Testes e2e revelaram um erro "Failed to embody meta-agent". A causa raiz é uma inconsistência entre a especificação da SAGA-16 e a implementação do `FileSystemStateRepository`.

-   **Especificação (SAGA-16):** O arquivo de definição do agente deve se chamar `definition.yaml`.
-   **Implementação Atual:** O método `load_definition` em `FileSystemStateRepository` está procurando por `agent.yaml`.

Esta discrepância impede que qualquer agente seja carregado.

## 2. Objetivo

Corrigir o nome do arquivo no código para alinhá-lo com a especificação da SAGA-16, consertando o bug de "embody".

## 3. Plano de Execução

**Local:** `src/infrastructure/storage/filesystem_repository.py`

**Checklist:**
- [ ] Localizar o método `load_definition`.
- [ ] Alterar a linha `definition_file = os.path.join(agent_dir, "agent.yaml")` para `definition_file = os.path.join(agent_dir, "definition.yaml")`.
- [ ] Atualizar o docstring do método para refletir a mudança de `(agent.yaml)` para `(definition.yaml)`.

## 4. Critérios de Aceitação

1.  O `FileSystemStateRepository` agora procura por `definition.yaml` para carregar a definição do agente.
2.  Após a correção, o comando `python -m src.cli.admin --meta --agent AgentCreator_Agent --repl` deve conseguir incorporar o agente com sucesso.
