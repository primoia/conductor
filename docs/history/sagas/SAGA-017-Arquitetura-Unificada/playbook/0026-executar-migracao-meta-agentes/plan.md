### Plano de Execução: Estágio 26 - Executar a Migração para os Meta-Agentes

#### Contexto Arquitetônico

Temos o script `migrate_legacy_agents.py`, a nossa ferramenta de conversão. Agora, precisamos aplicá-lo ao primeiro e mais importante conjunto de agentes: os meta-agentes, que residem em `projects/_common/agents/`. Esta tarefa consiste em executar o script para converter esses agentes legados e verificar o resultado.

#### Propósito Estratégico

O objetivo é realizar a primeira migração real de ativos, provando que nosso script funciona e trazendo os agentes fundamentais do sistema para a nova arquitetura. Uma vez que os meta-agentes estejam no novo formato, eles se tornarão "visíveis" para o `ConductorService` através da sua lógica de descoberta, um passo crítico para a unificação completa do sistema.

#### Checklist de Execução

- [x] Criar um diretório de destino para os novos artefatos. Uma boa prática seria um diretório temporário ou um diretório claramente nomeado, como `.conductor_workspace/agents/`.
- [x] Executar o script `scripts/migrate_legacy_agents.py` a partir da linha de comando.
- [x] Passar `projects/_common/agents/` como o `--source-dir`.
- [x] Passar o diretório de destino criado como o `--target-dir`.
- [x] Inspecionar o diretório de destino para verificar se os arquivos `.json` foram criados para cada meta-agente.
- [x] Abrir um dos arquivos `.json` gerados e verificar se ele contém a estrutura de dados consolidada (definição, persona, etc.) corretamente.
