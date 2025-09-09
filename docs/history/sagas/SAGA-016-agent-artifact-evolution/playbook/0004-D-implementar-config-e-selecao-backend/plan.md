# Plano: 0004-D - Config: Implementar `config.yaml` e Seleção de Backend

## Contexto

Atualmente, nosso `AgentService` está acoplado ao `FileSystemStorage`. Precisamos introduzir uma camada de configuração que permita ao Conductor decidir qual backend de armazenamento usar (`filesystem` ou `mongodb`).

Este plano foca em refatorar o `ConfigManager` existente para carregar e validar um novo `config.yaml` que contém a seção `storage_backend`. Também criaremos uma "fábrica" de repositórios que instancia o storage correto com base nessa configuração.

## Checklist de Verificação

- [ ] Modificar o `ConfigManager` (localizado em `src/config.py`) para ler o arquivo `config.yaml` na raiz do projeto.
- [ ] O `ConfigManager` deve carregar a seção `storage_backend`, que contém `type` e `workspace_path`.
- [ ] Adicionar validação no `ConfigManager` para garantir que `type` seja 'filesystem' ou 'mongodb'.
- [ ] Criar um novo arquivo `src/infrastructure/repository_factory.py`.
- [ ] Na `repository_factory.py`, criar uma função `get_repository(config: AppConfig)` que recebe o objeto de configuração.
- [ ] A função `get_repository` deve ler o `config.storage_backend.type` e retornar uma instância de `FileSystemStorage` se o tipo for 'filesystem'. (A lógica do MongoDB será um placeholder por enquanto).
- [ ] Refatorar o ponto de entrada da aplicação (provavelmente no `src/container.py` ou `src/cli/admin.py`) para:
    1. Carregar a configuração usando o `ConfigManager`.
    2. Chamar `get_repository()` para obter a instância de armazenamento.
    3. Injetar essa instância no `AgentService`.
- [ ] Criar um arquivo `config.yaml` na raiz do projeto com a configuração padrão para `filesystem`.
