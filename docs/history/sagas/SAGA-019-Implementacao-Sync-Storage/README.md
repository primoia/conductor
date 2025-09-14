# SAGA-019: Implementação do Script de Sincronização de Storage

## Visão Geral

Com a arquitetura de persistência agora unificada e refatorada na SAGA-018, esta saga foca em implementar a funcionalidade originalmente desejada: um script robusto e amigável para sincronizar e migrar o estado dos agentes entre os backends `filesystem` e `mongodb`.

## Artefato Principal

O resultado será um novo comando CLI, `conductor storage sync`, que encapsula esta lógica. O comando terá um duplo propósito, controlado por uma flag `--backup`:

1.  **Modo Migração (Padrão):** Copia os dados e atualiza o `config.yaml` para usar o novo backend.
2.  **Modo Backup (`--backup`):** Apenas copia os dados, sem alterar a configuração, ideal para backups manuais.
