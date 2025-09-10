# Guia: Migrando Agentes Legados

Com a introdução da nova arquitetura unificada na SAGA-017, a forma como os agentes são definidos e armazenados mudou. Este guia explica como migrar agentes do formato antigo (baseado em múltiplos arquivos em um diretório) para o novo formato (um único artefato JSON).

## 1. A Mudança Arquitetônica

-   **Formato Antigo:** Um agente era definido por uma coleção de arquivos dentro de um diretório (ex: `agent.yaml`, `persona.md`, `playbook.yaml`).
-   **Formato Novo:** A definição completa de um agente agora reside em um único artefato `.json`, que é armazenado em um backend de persistência (como o diretório `.conductor_workspace/agents/` para o backend `filesystem`).

## 2. A Ferramenta de Migração

Para facilitar a transição, o Conductor fornece um script para automatizar o processo.

-   **Script:** `scripts/migrate_legacy_agents.py`

Este script lê um diretório contendo agentes no formato antigo e gera os novos artefatos `.json` correspondentes.

## 3. Como Usar

### Passo 1: Execute o Script
Abra seu terminal na raiz do projeto e execute o script, fornecendo o diretório de origem (onde seus agentes antigos estão) e um diretório de destino.

**Exemplo:**
```bash
poetry run python scripts/migrate_legacy_agents.py \
    --source-dir path/to/your/legacy_agents \
    --target-dir .conductor_workspace/agents
```
-   `--source-dir`: O diretório que contém as pastas de cada agente a ser migrado.
-   `--target-dir`: O diretório onde os novos arquivos `.json` serão salvos. Para o backend `filesystem`, este deve ser o diretório de agentes dentro do seu workspace.

### Passo 2: Verifique os Resultados
O script irá processar cada subdiretório no diretório de origem e criar um arquivo `.json` correspondente no diretório de destino.

**Estrutura "Antes":**
```
legacy_agents/
└── MyAwesome_Agent/
    ├── agent.yaml
    └── persona.md
```

**Estrutura "Depois":**
```
.conductor_workspace/
└── agents/
    └── MyAwesome_Agent.json
```

O `ConductorService` irá descobrir e carregar automaticamente os agentes a partir deste novo local.