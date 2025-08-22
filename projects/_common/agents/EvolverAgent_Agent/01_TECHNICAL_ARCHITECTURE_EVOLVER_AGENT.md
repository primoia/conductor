# 🧠 EvolverAgent: Arquitetura Técnica

Este documento descreve a arquitetura técnica do `EvolverAgent`, um agente de IA autônomo projetado para analisar, otimizar e evoluir continuamente o ecossistema Primoia.

## 1. Visão Geral e Diretriz Principal

O `EvolverAgent` opera com uma única diretriz: **"Analisar o estado atual do ecossistema, identificar oportunidades de melhoria e gerar artefatos direcionáveis para catalisar a evolução."**

Ele deve ser eficiente, evitando trabalho repetitivo, e suas saídas devem ser estruturadas para serem consumidas tanto por humanos quanto por outros agentes de IA.

## 2. Componentes da Arquitetura

A arquitetura se baseia em três componentes fundamentais que abordam os desafios de eficiência, automação e geração de valor.

### Componente 1: Base de Conhecimento com Estado

Para garantir que o agente não repita análises sobre código inalterado, ele manterá uma base de conhecimento atrelada ao histórico do Git.

*   **Mecanismo:** A chave primária para qualquer análise será o **hash do commit do Git** (`git rev-parse HEAD`).
*   **Armazenamento (Fase 1):** Um diretório `.evolver/knowledge_base/` na raiz do monorepo, contendo arquivos JSON. Cada arquivo será nomeado com o hash do commit analisado (ex: `a1b2c3d4.json`).
*   **Lógica de Execução:**
    1.  No início, o agente obtém o hash do commit atual.
    2.  Verifica se o arquivo `{hash}.json` existe na base de conhecimento.
    3.  **Se existir:** A execução é encerrada (early exit), pois o trabalho já foi feito.
    4.  **Se não existir:** A análise completa é executada. No final, os resultados são salvos no arquivo `{hash}.json`.

### Componente 2: O Ciclo Operacional (Flywheel)

O agente será "colocado na roda" através de um ciclo automatizado, integrado ao fluxo de desenvolvimento via CI/CD (ex: GitHub Actions).

```mermaid
graph TD
    A[Dev faz 'git push'] --> B{Webhook de Git aciona CI/CD};
    B --> C[Pipeline de CI/CD inicia o contêiner do EvolverAgent];
    C --> D{1. Agente verifica o hash do commit na Base de Conhecimento};
    D -- Commit Novo --> E[2. Agente executa a análise completa];
    D -- Commit Já Analisado --> F[Encerra a execução];
    E --> G[3. Agente gera/atualiza os Artefatos Direcionáveis];
    G --> H[4. Agente commita os artefatos de volta no repositório];
    H --> I[5. Agente notifica (opcional)];
```

### Componente 3: Artefatos Direcionáveis

A saída do agente será um conjunto de arquivos estruturados e versionados, servindo como a principal interface para tomada de decisão.

*   **Localização:** Todos os artefatos serão salvos no diretório `.evolver/reports/`.
*   **Artefato para Humanos: `HEALTH_REPORT.md`**
    *   **Formato:** Markdown.
    *   **Conteúdo:** Um dashboard de alto nível com o "placar de saúde" de cada projeto, principais problemas identificados e links diretos para os arquivos e linhas de código relevantes.
*   **Artefato para IA: `TASK_SUGGESTIONS.json`**
    *   **Formato:** JSON.
    *   **Conteúdo:** Uma lista de tarefas acionáveis, prontas para serem lidas por mim (Gemini) ou outros agentes para planejamento e delegação.
    *   **Esquema Proposto:**
        ```json
        [
          {
            "id": "string (ex: REFACTOR-001)",
            "project": "string (nome do projeto, ex: codenoob-social-profile)",
            "type": "enum (REFACTORING, SECURITY, PERFORMANCE, TESTING)",
            "priority": "enum (low, medium, high, critical)",
            "description": "string (Descrição clara do problema)",
            "location": {
              "file": "string (caminho para o arquivo)",
              "line": "integer (número da linha, opcional)"
            },
            "status": "pending"
          }
        ]
        ```

## 3. Roadmap de Implementação

Propomos um desenvolvimento faseado para entregar valor de forma incremental.

*   **Fase 1 (MVP):**
    *   Implementar a lógica da Base de Conhecimento (verificação de hash).
    *   Implementar um módulo de análise inicial (ex: linter e complexidade de código).
    *   Gerar a primeira versão do `HEALTH_REPORT.md`.
    *   Configurar o pipeline de CI/CD para rodar o agente a cada push.
*   **Fase 2:**
    *   Implementar a geração do artefato `TASK_SUGGESTIONS.json`.
    *   Desenvolver a minha capacidade de ler e interpretar este JSON para planejar e delegar tarefas.
*   **Fase 3:**
    *   Adicionar novos módulos de análise (auditoria de segurança, análise de dependências).
    *   Expandir para análise de performance.
