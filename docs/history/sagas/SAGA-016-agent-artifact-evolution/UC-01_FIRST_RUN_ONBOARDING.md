# UC-01: First Run Onboarding Flow

## 1. Objetivo

Este documento descreve o fluxo de trabalho da primeira vez que um usuário executa o Conductor. O objetivo é inicializar o ambiente de trabalho local do usuário de forma transparente, sem exigir nenhuma dependência externa (como bancos de dados), garantindo uma experiência de "clonar e executar" (clone and run).

## 2. Atores

*   **Usuário:** O desenvolvedor que executa o Conductor pela primeira vez.
*   **Conductor (Core System):** O sistema principal que orquestra a inicialização.

## 3. Pré-condições

*   O usuário clonou o repositório do Conductor.
*   O diretório de trabalho local `.conductor_workspace/` **não existe** na raiz do projeto.
*   O repositório contém o diretório `_agent_templates/` com os templates dos agentes iniciais.
*   O arquivo `config.yaml` pode ou não existir na raiz do projeto.

## 4. Fluxo Passo a Passo

1.  O Usuário executa um comando do Conductor pela primeira vez (ex: `python src/cli/agent.py --agent Help_Agent`).
2.  O Conductor (Core System) inicia e procura por um arquivo `config.yaml` na raiz do projeto.
3.  Se `config.yaml` não for encontrado, o sistema o cria com o conteúdo padrão: `storage_backend: filesystem`.
4.  O sistema lê o `config.yaml` e determina que o `storage_backend` é `filesystem`.
5.  Com base nisso, o sistema verifica a existência do diretório `.conductor_workspace/`. Como ele não existe, o fluxo de "First Run Onboarding" é ativado.
6.  O sistema cria o diretório `.conductor_workspace/` e a subpasta `agents/`.
7.  O sistema itera sobre cada template de agente encontrado em `_agent_templates/`.
8.  Para cada template (ex: `AgentCreator_Agent`), o sistema:
    a. Cria um diretório correspondente dentro de `.conductor_workspace/agents/` (ex: `.conductor_workspace/agents/AgentCreator_Agent/`).
    b. Copia os artefatos do template (`definition.yaml`, `persona.md`, `playbook.md`) para o novo diretório da instância.
9.  O sistema adiciona a entrada `.conductor_workspace/` ao arquivo `.gitignore` na raiz do projeto, se ainda não existir.
10. Com o ambiente inicializado, o Conductor prossegue com a execução normal do comando original do usuário.

## 5. Pós-condições

*   O arquivo `config.yaml` existe na raiz do projeto.
*   O diretório `.conductor_workspace/` existe na raiz do projeto e não contém um `config.yaml`.
*   O diretório `.conductor_workspace/agents/` contém subdiretórios para cada um dos agentes iniciais, e cada um contém seus respectivos artefatos de *definição*. Os artefatos de *estado* (`memory.json`, `session.json`) ainda não existem.
*   O arquivo `.gitignore` principal contém a entrada `.conductor_workspace/`.
*   O comando original do usuário é executado com sucesso no ambiente recém-inicializado.

## 6. Impacto na Estrutura de Arquivos

Este fluxo estabelece a seguinte estrutura de diretórios e arquivos:

```
/conductor-project-root
├── .git/
├── .gitignore               # Deve conter ".conductor_workspace/"
├── .conductor_workspace/    # Diretório de trabalho local, não versionado
│   └── agents/
│       ├── AgentCreator_Agent/
│       │   ├── definition.yaml
│       │   ├── persona.md
│       │   └── playbook.md
│       │
│       └── ... (outros agentes iniciais)
│
├── _agent_templates/        # Templates base, versionados
│   ├── AgentCreator_Agent/
│   │   ├── definition.yaml
│   │   ├── persona.md
│   │   └── playbook.md
│   └── ... (outros agentes iniciais)
│
├── config.yaml              # <<< ARQUIVO DE CONFIGURAÇÃO PRINCIPAL
│
└── src/
    └── ... (código fonte do Conductor)
```

**Nota sobre Artefatos de Estado:** Os arquivos `memory.json` e `session.json` serão criados dinamicamente dentro do diretório de cada agente (ex: `.conductor_workspace/agents/AgentCreator_Agent/`) na primeira vez que aquela instância de agente precisar persistir seu estado.

**Nota sobre a Estrutura do `playbook.md`:** Conforme definido na SAGA principal, cada `playbook.md` segue uma estrutura incremental com seções `## Best Practices` e `## Anti-Patterns`, onde cada entrada possui um `ID` único, `Title` e `Description` para permitir modificações programáticas precisas.
