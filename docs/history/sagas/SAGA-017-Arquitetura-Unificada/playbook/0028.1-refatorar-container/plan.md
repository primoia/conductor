### Plano de Execução: Estágio 28.1 - Refatorar `container.py`

#### Contexto Arquitetônico

Durante a tentativa de depreciar `config/workspaces.yaml` (Passo 28), foi identificado que o `src/container.py` ainda possui métodos (`load_workspaces_config`, `resolve_agent_paths`) que dependem deste arquivo legado. Para completar a migração para uma configuração unificada, essas dependências precisam ser removidas.

#### Propósito Estratégico

O objetivo é eliminar as últimas dependências do código no `workspaces.yaml`, tornando o `config.yaml` a única fonte da verdade para a configuração. Isso permitirá que o Passo 28 original seja re-executado com sucesso, completando a consolidação da configuração.

#### Checklist de Execução

- [x] Modificar `src/container.py`.
- [x] Remover o método `load_workspaces_config`.
- [x] Refatorar o método `resolve_agent_paths` para não depender mais do `workspaces.yaml`. A lógica de resolução de caminhos deve ser simplificada ou adaptada para usar informações do `ConductorService` ou do backend de armazenamento, se necessário.
- [x] Remover quaisquer outros usos do `workspaces.yaml` dentro do `container.py`.
