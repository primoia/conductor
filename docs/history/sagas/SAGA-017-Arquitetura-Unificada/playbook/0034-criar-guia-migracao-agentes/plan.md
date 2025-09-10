### Plano de Execução: Estágio 34 - Criar Guia de Migração de Agentes

#### Contexto Arquitetônico

Executamos a migração de todos os agentes legados usando um script (`scripts/migrate_legacy_agents.py`). No entanto, o conhecimento de como e porquê essa migração foi feita reside apenas no código do script e no histórico desta saga. Para futuros desenvolvedores ou para usuários que queiram migrar seus próprios agentes legados, esse processo não está documentado.

#### Propósito Estratégico

O objetivo é criar uma documentação persistente que explique o processo de migração de agentes. Este guia servirá como referência para a equipe, garantindo que o conhecimento sobre a transição da arquitetura não se perca. Ele também capacita os usuários que podem ter criado seus próprios agentes no formato antigo a atualizá-los para o novo padrão, facilitando a adoção contínua da nova arquitetura.

#### Checklist de Execução

- [x] Criar um novo arquivo em `docs/guides/agent_migration_guide.md`.
- [x] O guia deve explicar brevemente a diferença entre a estrutura de diretórios antiga e a nova estrutura de artefato único em JSON.
- [x] Documentar o propósito do script `scripts/migrate_legacy_agents.py`.
- [x] Fornecer instruções claras e um exemplo de como executar o script a partir da linha de comando, explicando seus argumentos (`--source-dir`, `--target-dir`).
- [x] Mostrar um exemplo da estrutura de arquivos "antes" e do arquivo `.json` "depois".
- [x] Explicar que os novos artefatos devem ser colocados no diretório de workspace (`.conductor_workspace/agents/`) para o backend de `filesystem`.
