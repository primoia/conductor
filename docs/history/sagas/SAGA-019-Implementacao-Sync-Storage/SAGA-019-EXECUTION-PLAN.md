# Plano de Execução (Revisão Final): SAGA-019

**Objetivo:** Implementar funcionalidade de **migração bidirecional** entre backends filesystem e mongodb, com suporte especial para workflows RAMDisk e preservação de configurações locais.

## Interface CLI Final

```bash
# Migração com preservação de config (uso principal)
conductor --migrate-to mongodb --no-config-update
conductor --migrate-to filesystem --no-config-update

# Migração permanente (altera config.yaml)
conductor --migrate-to mongodb
conductor --migrate-to filesystem

# Suporte a paths externos
conductor --migrate-to filesystem --path "/path/to/external/backup"
```

---

### Fase 1: Motor de Sincronização Inteligente

**Descrição:** Criar motor que usa configuração do `.env`, detecta disponibilidade de backends e opera bidirecionalmente.

*   **Playbook de Implementação:**
    *   `0001-A-criar-script-sync-engine.md`: Cria `scripts/helpers/sync_engine.py` com:
        - Uso de configuração do `.env` (mongo_uri, mongo_database)
        - Detecção automática de disponibilidade MongoDB
        - Suporte bidirecional (filesystem ↔ mongodb)
        - Logs detalhados de progresso
        - Validação de pré-requisitos

---

### Fase 2: Interface CLI Unificada

**Descrição:** Implementar comando `--migrate-to` com flag `--no-config-update` para preservar configurações locais.

*   **Playbook de Implementação:**
    *   `0002-B-implementar-cli-migrate.md`: Adiciona ao `conductor.py`:
        - Argumento `--migrate-to` com opções [mongodb, filesystem]
        - Flag `--no-config-update` para preservar config.yaml
        - Parâmetro `--path` para backups externos
        - Validações e alertas de configuração

---

### Fase 3: Compatibilidade com Scripts Existentes

**Descrição:** Manter funcionalidade rsync/SSD existente e integrar com novo sistema.

*   **Playbook de Implementação:**
    *   `0003-C-manter-compatibilidade-scripts.md`: 
        - Preservar `backup_agents.sh` e `restore_agents.sh` existentes
        - Adicionar integração opcional com novo sistema
        - Garantir retrocompatibilidade total

---

### Fase 4: Testes e Validação

**Descrição:** Validar workflows completos, especialmente cenarios RAMDisk.

*   **Playbook de Implementação:**
    *   `0004-D-implementar-testes-completos.md`: 
        - Testes de migração bidirecional
        - Validação de preservação de config.yaml
        - Testes de conectividade e erro handling
        - Testes de coexistência com backup SSD