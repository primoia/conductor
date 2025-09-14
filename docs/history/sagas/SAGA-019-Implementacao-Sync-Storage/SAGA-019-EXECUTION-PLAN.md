# Plano de Execução: SAGA-019

**Objetivo:** Construir sobre a arquitetura de persistência unificada para implementar um comando CLI que sincroniza e migra dados de agentes entre os backends de `filesystem` e `mongodb`.

---

### Fase 1: Implementação do Motor de Sincronização e CLI

**Descrição:** Criar o script auxiliar que contém a lógica de negócio e a interface de linha de comando para a operação.

*   **Playbook de Implementação:**
    *   `0001-A-criar-script-sync-engine.md`: Cria o arquivo `scripts/helpers/sync_engine.py` contendo a classe `SyncEngine` e o bloco `main` para parse de argumentos (`--direction`, `--backup`). A classe usará a arquitetura de serviços e repositórios já refatorada para realizar a transferência de dados.

---

### Fase 2: Integração com o CLI Principal e Scripts Shell

**Descrição:** Conectar o novo motor de sincronização aos comandos `conductor --backup` e `conductor --restore` existentes, e criar o novo comando de migração.

*   **Playbook de Implementação:**
    *   `0002-B-evoluir-scripts-shell.md`: Modifica `backup_agents.sh` e `restore_agents.sh` para se tornarem "dispatchers", chamando o novo `sync_engine.py` quando a flag `--backend mongodb` for utilizada, e mantendo o comportamento de `rsync` como padrão para garantir retrocompatibilidade.
    *   `0003-C-integrar-comandos-cli.md`: Ajusta `conductor.py` para passar a flag `--backend` para os scripts shell e implementa o novo comando `conductor --migrate-to <backend>`.

---

### Fase 3: Testes e Validação

**Descrição:** Garantir a robustez e a corretude da nova funcionalidade através de testes de integração.

*   **Playbook de Implementação:**
    *   `0004-D-implementar-testes-integracao-sync.md`: Cria os testes de integração para os cenários de Backup, Migração e Restauração, validando tanto a transferência de dados quanto a modificação do `config.yaml`.
