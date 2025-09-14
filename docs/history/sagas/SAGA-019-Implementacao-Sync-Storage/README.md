# SAGA-019 (Revisão Final): Implementação da Sincronização de Storage

## Visão Geral

Esta saga implementa a funcionalidade de **migração bidirecional** de dados de agentes entre os backends `filesystem` e `mongodb`. A solução foi projetada especificamente para suportar workflows com RAMDisk, permitindo backup seguro sem forçar alterações de configuração, mantendo a simplicidade para novos desenvolvedores.

## Casos de Uso Principais

1. **Backup Seguro (RAMDisk)**: Migração temporária filesystem → mongodb sem alterar config.yaml
2. **Restore de Emergência**: Migração temporária mongodb → filesystem sem alterar config.yaml  
3. **Migração Permanente**: Mudança definitiva de backend com atualização do config.yaml
4. **Backup Externo**: Suporte a paths externos para repositórios Git privados

## Arquitetura da Solução

A solução opera em três níveis, respeitando a arquitetura de serviços estabelecida na SAGA-018:

1.  **CLI (`conductor.py`):** Interface unificada com comando `--migrate-to` e flag opcional `--no-config-update`
2.  **Scripts Shell (`backup_agents.sh`, etc.):** Mantêm funcionalidade `rsync` existente, com extensão para novo sistema
3.  **Motor de Sincronização (`sync_engine.py`):** Lógica de negócio operando na camada `IStateRepository` para máxima performance, usando configuração do `.env` existente