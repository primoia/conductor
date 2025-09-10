### Plano de Execução: Estágio 25 - Criar Script de Migração de Agentes

#### Contexto Arquitetônico

Nossa nova arquitetura, governada pelo `ConductorService`, opera sobre uma estrutura de artefatos de agente unificada, conforme definido na SAGA-016. No entanto, nossos agentes existentes (`CodeReviewer_Agent`, etc.) ainda residem na estrutura de diretórios antiga. Para que eles se tornem visíveis e operáveis pelo novo sistema, eles precisam ser convertidos. Esta tarefa consiste em criar um script para automatizar essa conversão.

#### Propósito Estratégico

O objetivo é criar uma ferramenta reutilizável e à prova de erros para trazer nossos ativos legados para o novo ecossistema. Uma migração manual seria tediosa e propensa a inconsistências. Um script automatizado garante que todos os agentes sejam migrados de forma consistente, preservando sua definição e persona. Este script é a ponte técnica que permite que nossos agentes antigos atravessem para a nova arquitetura.

#### Checklist de Execução

- [ ] Criar um novo arquivo em `scripts/migrate_legacy_agents.py`.
- [ ] O script deve usar `argparse` para aceitar argumentos de linha de comando, como o diretório de origem do agente legado e o diretório de destino para os novos artefatos.
- [ ] Implementar uma função que leia os múltiplos arquivos de um agente legado (`agent.yaml`, `persona.md`, `playbook.yaml`).
- [ ] A função deve consolidar as informações lidas em uma única estrutura de dicionário Python, que representará o novo "estado" unificado do agente.
- [ ] A função deve então escrever este dicionário consolidado como um único arquivo JSON no diretório de destino.
- [ ] O script deve ser capaz de iterar sobre um diretório contendo múltiplos agentes (como `projects/_common/agents/`) e migrar todos eles de uma vez.
