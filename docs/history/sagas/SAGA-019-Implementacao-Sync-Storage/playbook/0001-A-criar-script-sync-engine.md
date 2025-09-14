# Plano: 0001-A - Criar Motor de Sincronização Inteligente

**Objetivo:** Implementar motor de migração bidirecional que usa configuração do `.env`, detecta disponibilidade de backends e opera com logs detalhados.

**Contexto:** Motor deve suportar workflows RAMDisk com preservação de configurações locais, usando a arquitetura `IStateRepository` para máxima performance.

**Executor:** Claude Executor

---

### Checklist de Execução

- [ ] **1. Criar Estrutura Base:**
    - Criar diretório `scripts/helpers/` se não existir
    - Criar arquivo `scripts/helpers/sync_engine.py`

- [ ] **2. Implementar Classe `SyncEngine`:**
    - Imports: `os`, `sys`, `argparse`, `yaml`, configuração do `.env`
    - Classe `SyncEngine` com métodos:
        - `__init__()`: Inicializar com configuração do container DI
        - `check_mongodb_availability()`: Validar .env e conectividade
        - `get_repositories(source_type, dest_type, custom_path)`: Obter instâncias IStateRepository
        - `migrate_agents(source_repo, dest_repo)`: Transferência com logs detalhados
        - `update_config_if_needed(new_backend, no_config_update)`: Atualizar config.yaml condicionalmente

- [ ] **3. Implementar Logs Detalhados:**
    - Progress bars ou indicadores visuais
    - Contagem de agentes e arquivos transferidos
    - Alertas para arquivos não encontrados
    - Tempo total de operação
    - Mensagens de erro descritivas

- [ ] **4. Implementar Bloco Main:**
    - Argumentos: `--source`, `--destination`, `--path`, `--no-config-update`
    - Validações de pré-requisitos
    - Execução da migração
    - Saída com códigos de erro apropriados