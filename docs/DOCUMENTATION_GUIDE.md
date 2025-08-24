# 📖 Guia de Documentação - Projeto Conductor

> **Filosofia:** A documentação deve ser um facilitador, não um obstáculo. Ela precisa ser fácil de encontrar, fácil de entender e, acima de tudo, confiável. Este guia estabelece as diretrizes para alcançar isso.

## 1. Estrutura de Diretórios

A documentação do Conductor é organizada em pastas de alto nível, cada uma com um propósito claro:

-   **/conductor (`root`)**: O `README.md` na raiz é o **ponto de entrada principal**. Ele deve fornecer uma visão geral do projeto, links para os principais executores e direcionar para os documentos mais importantes.
-   `docs/`: Contém a **documentação técnica permanente**. É o conhecimento consolidado sobre a arquitetura, funcionalidades e guias de uso do framework.
-   `project-management/`: Contém **documentos de processo e gestão**. São artefatos temporais como planos de milestones, relatórios de bugs e planejamento de novas funcionalidades.
-   `stories/`: Descrições de funcionalidades sob a perspectiva do usuário ou do sistema, seguindo um formato de "história".
-   `scripts/`: Embora contenha código, pode incluir `README.md` específicos que explicam o propósito e o uso dos executores principais.

## 2. Categorias de Documentos

Para manter a consistência, os documentos dentro de `docs/` devem se enquadrar em uma das seguintes categorias:

#### a. 🏛️ Arquitetura (`docs/architecture/`)
-   **Propósito:** Descrever decisões de alto nível, padrões de design e a estrutura fundamental do framework.
-   **Exemplos:** `GEMINI_ARCH_SPEC.md`, `EXECUTOR_ARCHITECTURE.md`.
-   **Nomenclatura:** Nomes descritivos em MAIÚSCULO_COM_UNDERSCORE.md ou kebab-case.md.

#### b. ✨ Funcionalidades (`docs/features/`)
-   **Propósito:** Documentar funcionalidades específicas e como elas funcionam.
-   **Exemplos:** `interactive-sessions.md`, `multi-provider-ai.md`.
-   **Nomenclatura:** `nome-da-feature.md`.

#### c. 🏁 Guias e Tutoriais (`docs/guides/`)
-   **Propósito:** Fornecer instruções passo a passo para realizar tarefas comuns.
-   **Exemplos:** `ONBOARDING_NEW_PROJECT.md`, `AGENT_DESIGN_PATTERNS.md`.
-   **Nomenclatura:** Nomes descritivos e claros.

#### d. 📜 Decisões Arquiteturais (`docs/adr/`)
-   **Propósito:** Registrar decisões arquiteturais importantes (Architectural Decision Records).
-   **Nomenclatura:** `ADR-XXX-descricao-da-decisao.md`.

## 3. Ciclo de Vida da Documentação

Para evitar a desatualização e o conflito de informações, seguimos um ciclo de vida:

1.  **Criação:**
    -   Sempre que uma nova funcionalidade, decisão arquitetural ou processo é introduzido, um novo documento deve ser criado na categoria apropriada.
    -   Use os templates (a serem definidos) para garantir a consistência.

2.  **Revisão:**
    -   A documentação deve ser revisada como parte do processo de code review. Se um PR altera um comportamento, a documentação correspondente **deve** ser atualizada no mesmo PR.

3.  **Arquivamento (não exclusão):**
    -   Documentos que se tornam obsoletos (por exemplo, planos de milestones concluídos, arquiteturas antigas) não devem ser excluídos.
    -   Eles devem ser movidos para um subdiretório `_archive/` dentro de suas respectivas pastas (ex: `docs/architecture/_archive/`, `project-management/_archive/`).
    -   Isso preserva o histórico sem poluir a estrutura principal.

4.  **Sinalização de Conflito:**
    -   Se você encontrar um documento que contradiz outro mais recente, a prioridade é sempre do mais novo.
    -   O documento antigo deve ser imediatamente marcado para arquivamento e uma issue deve ser aberta para resolver a inconsistência.

## 4. O `README.md` como Mapa
O `README.md` de cada diretório (`docs/README.md`, `project-management/README.md`) deve servir como um índice ou mapa para o conteúdo daquela seção, destacando os documentos mais importantes e explicando brevemente o propósito de cada subpasta.
