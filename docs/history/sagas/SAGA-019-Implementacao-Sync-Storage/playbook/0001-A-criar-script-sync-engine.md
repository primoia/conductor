# Plano: 0001-A - Criar Script `sync_engine.py`

**Objetivo:** Implementar a lógica central de sincronização em um script Python auxiliar, desacoplado e reutilizável, que opera sobre a arquitetura de serviços já corrigida.

**Contexto:** Com as interfaces `IAgentStorage` e `IStateRepository` e suas implementações devidamente separadas, podemos agora criar o motor que orquestra a transferência de dados de forma segura, usando as abstrações corretas.

**Executor:** Claude Executor (ou similar)

---

### Checklist de Execução

- [ ] **1. Criar o Arquivo:** Crie o novo arquivo em `scripts/helpers/sync_engine.py`.

- [ ] **2. Adicionar Imports:** Inclua os imports necessários, como `argparse`, `os`, e as classes de serviço e repositório relevantes.
    ```python
    # scripts/helpers/sync_engine.py
    import argparse
    import os
    # Supondo que o container de DI esteja acessível
    # from src.container import container
    ```

- [ ] **3. Implementar a Classe `SyncEngine`:**
    - Crie a classe `SyncEngine`.
    - No construtor (`__init__`), obtenha o `storage_service` do container de DI.
    - Crie o método principal `run_sync(self, source_backend_name: str, dest_backend_name: str)`.
    - Dentro de `run_sync`, use o método `storage_service.get_repository_by_name()` para instanciar `source_repo` e `destination_repo`.
    - Implemente o loop que chama `source_repo.list_agents()`, e para cada agente, transfere todos os artefatos usando os métodos `load_*` da origem e `save_*` do destino.

- [ ] **4. Implementar o Bloco de Execução (`main`):**
    - Adicione o bloco `if __name__ == "__main__":`.
    - Dentro dele, configure o `argparse` para os argumentos `--direction` e `--backup`.
    - Instancie e execute a classe `SyncEngine` com base nos argumentos fornecidos.
    - Adicione a lógica para ler/modificar o `config.yaml` se a flag `--backup` não estiver presente.
    - Inclua mensagens de progresso, sucesso e erro claras para o usuário.
