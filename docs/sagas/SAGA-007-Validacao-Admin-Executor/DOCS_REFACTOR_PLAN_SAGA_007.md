# Plano Mestre de Refatoração da Documentação (SAGA-007)

**Autor:** Primo (Gemini)
**Saga:** SAGA-007-Validacao-Admin-Executor
**Status:** Proposto

## 1. Objetivo

Refatorar a documentação do projeto para adotar um modelo robusto e escalável, separando a documentação canônica (em `/docs`) dos registros históricos (em `/sagas`). Esta saga e seu plano resultante substituem o processo de avaliação descrito na `SAGA-004`.

## 2. Princípios Arquiteturais da Documentação

1.  **`/docs` é a Biblioteca:** Contém a documentação canônica, estável e que reflete o estado **atual** do projeto.
2.  **`/sagas` é o Diário de Bordo:** Contém o registro cronológico e imutável de como o projeto evoluiu. Uma saga registra uma mudança.
3.  **Links Unidirecionais:** Sagas podem (e devem) apontar para a documentação permanente que elas criaram ou modificaram. O inverso é proibido: documentos permanentes não devem apontar para dentro de sagas.
4.  **Arquivamento:** Sagas que foram completamente substituídas por uma nova saga ou cujas contribuições foram totalmente integradas à documentação permanente devem ser movidas para um diretório `_archive/`.
5.  **Resumo da Saga (Novo Padrão):** Cada saga pode conter um script `summary.sh` que descreve de forma programática o seu resultado.

## 3. Fases de Execução da Refatoração

---

### Fase 1: Promover e Corrigir o Guia de Avaliação

-   **Ação:** Criar um novo guia permanente para o processo de avaliação de agentes.
-   **Localização do Novo Arquivo:** `projects/conductor/docs/guides/AGENT_EVALUATION_PROCESS.md`
-   **Conteúdo:** O conteúdo será uma cópia completa do `SAGA-004/360_EVALUATION_SOP.md`, mas com as seguintes correções:
    1.  Remover a nota incorreta sobre a ausência de um modo não-interativo no `admin.py`.
    2.  Adicionar uma nota sobre o problema conhecido com a gestão de `state` no modo não-interativo do `admin.py`.

---

### Fase 2: Registrar a Mudança na SAGA-007

-   **Ação:** Criar os artefatos que registram a execução desta saga.
-   **Arquivos a Criar:**
    1.  `projects/conductor/sagas/SAGA-007-Validacao-Admin-Executor/README.md`
        -   **Conteúdo:** Descreverá que esta saga executou a refatoração da documentação de avaliação, que o novo guia oficial está em `../../docs/guides/AGENT_EVALUATION_PROCESS.md`, e que a `SAGA-004` foi arquivada.
    2.  `projects/conductor/sagas/SAGA-007-Validacao-Admin-Executor/summary.sh`
        -   **Conteúdo:** Um script simples que executa `echo "SAGA-007: Refactored the agent evaluation documentation. New guide is at projects/conductor/docs/guides/AGENT_EVALUATION_PROCESS.md"`.

---

### Fase 3: Refatorar Links Existentes no Projeto

-   **Ação:** Atualizar todos os documentos que apontam para sagas de forma incorreta.
-   **Arquivos a Modificar:**
    1.  `projects/conductor/README.md`: Atualizar o link que aponta para a `SAGA-003` para que aponte para um guia permanente (a ser criado ou já existente em `/docs/guides/`).
    2.  `projects/conductor/docs/architecture/HYBRID_AGENT_ARCHITECTURE.md`: Atualizar o link que aponta para a `SAGA-006` para que aponte para o documento de arquitetura relevante em `/docs/architecture/`.

---

### Fase 4: Arquivar a Saga Obsoleta

-   **Ação:** Mover a saga antiga para o arquivo morto para evitar consultas futuras.
-   **Comando:**
    ```bash
    mv projects/conductor/sagas/SAGA-004-A-Avaliacao projects/conductor/sagas/_archive/
    ```

## 4. Próximos Passos

A execução da **Fase 1** deste plano será o próximo passo após a sua aprovação.
