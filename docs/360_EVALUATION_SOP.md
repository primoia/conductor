# POP - Procedimento Operacional Padrão para Avaliação 360

## 1. Objetivo

Este documento descreve o processo padrão e reutilizável para conduzir uma avaliação 360 do framework Conductor. O ciclo consiste em criar um agente dinamicamente, usar esse agente para executar uma tarefa (como criar um projeto), avaliar formalmente o desempenho do agente e registrar o resultado para análise de melhoria contínua.

---

## 2. Fases de Execução

O ciclo é dividido em 4 fases principais, orquestradas pelo Gemini e executadas pelo Claude.

### Fase 0: Estudo e Preparação (Orquestrador)

Antes de iniciar um novo ciclo, o orquestrador (Gemini) deve estudar os scripts (`admin.py`, `genesis_agent_v2.py`, `run_agent_evaluation.sh`) para garantir que os comandos e parâmetros a serem usados estão corretos e atualizados.

### Fase 1: Criação do Agente

- **Ferramenta:** `admin.py`
- **Comando Padrão:**
  ```bash
  python projects/conductor/scripts/admin.py --agent AgentCreator_Agent --prompt "<PROMPT_PARA_CRIACAO_DO_AGENTE>" --provider claude
  ```

### Fase 2: Execução do Agente Criado

- **Ferramenta:** `genesis_agent_v2.py`
- **Comando Padrão:**
  ```bash
  python projects/conductor/scripts/genesis_agent_v2.py --agent <NOME_DO_AGENTE_CRIADO> --environment <AMBIENTE_ALVO> --project <PROJETO_ALVO> --prompt "<PROMPT_PARA_EXECUCAO_DA_TAREFA>" --provider claude
  ```

### Fase 3: Avaliação Formal

- **Ferramenta:** `run_agent_evaluation.sh`
- **Pré-requisito:** Um caso de teste (`.yaml`) deve ser criado em `projects/conductor/evaluation_cases/` para o agente em questão.
- **Comando Padrão:**
  ```bash
  bash projects/conductor/scripts/run_agent_evaluation.sh --agent <NOME_DO_AGENTE_CRIADO>
  ```

---

## 3. Procedimento Pós-Ciclo

Ao final de cada ciclo de execução, as seguintes etapas de verificação e registro são mandatórias.

1.  **Revisão dos Artefatos:** O orquestrador deve revisar todos os artefatos gerados durante o processo. Isso inclui os arquivos de configuração do novo agente, o projeto ou os arquivos criados pela tarefa, e os logs de execução para garantir a qualidade e consistência.

2.  **Coleta de Resultados:** O orquestrador deve localizar o relatório de avaliação gerado em `projects/conductor/.evaluation_output/` e extrair a pontuação final consolidada.

3.  **Registro no LOG:** **A etapa final e obrigatória é registrar os resultados.** A data, o ID do ciclo, o agente testado, a nota final e as observações relevantes devem ser adicionados como uma nova linha na tabela do arquivo `360_EVALUATION_LOG.md`.

---

## 4. Referência de Parâmetros

Esta seção documenta os parâmetros dos scripts principais usados neste ciclo de avaliação.

### `admin.py`

- **Objetivo:** Executar meta-agentes que gerenciam o próprio framework (ex: `AgentCreator_Agent`).
- **Parâmetros Relevantes:**
  - `--agent <ID_DO_AGENTE>`: (Obrigatório) Especifica o meta-agente a ser executado.
  - `--ai-provider <claude|gemini>`: (Opcional) Força o uso de um provedor de IA específico.
  - `--repl`: (Opcional) Inicia uma sessão de console interativa com o agente.
  - `--debug`: (Opcional) Ativa logs detalhados no console.
- **‼️ INCONSISTÊNCIA ENCONTRADA (Ciclo #1):**
  - O `admin.py` **não possui** um parâmetro para execução não-interativa (como `--input` ou `--prompt`). Isso impede a automação da criação de agentes, pois ele depende do modo `--repl`. O primeiro passo do ciclo de avaliação será corrigir isso.

### `genesis_agent_v2.py`

- **Objetivo:** Executar agentes de projeto que operam em bases de código externas.
- **Parâmetros Relevantes:**
  - `--environment <NOME_DO_AMBIENTE>`: (Obrigatório) Ambiente de trabalho (ex: `develop`).
  - `--project <NOME_DO_PROJETO>`: (Obrigatório) Projeto alvo onde o agente irá operar.
  - `--agent <ID_DO_AGENTE>`: (Obrigatório) Agente a ser executado.
  - `--input "<INSTRUCAO>"`: (Opcional) Permite passar uma instrução para o agente de forma não-interativa.
  - `--repl`: (Opcional) Inicia o modo interativo.
  - `--ai-provider <claude|gemini>`: (Opcional) Força o uso de um provedor de IA.
  - `--timeout <SEGUNDOS>`: (Opcional) Define o tempo máximo para a operação da IA.

### `run_agent_evaluation.sh`

- **Objetivo:** Executar o framework de avaliação para um agente específico.
- **Parâmetros Relevantes:**
  - `--agent <NOME_DO_AGENTE>`: (Obrigatório) O nome do agente a ser avaliado, que deve corresponder a um caso de teste em `evaluation_cases/`.

---

## 5. Exemplo Prático: Ciclo de Execução #1

*(Esta seção será preenchida com os comandos concretos utilizados no primeiro ciclo de teste.)*
