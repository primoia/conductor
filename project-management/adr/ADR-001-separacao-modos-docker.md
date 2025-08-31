# ADR-001: Separação dos Modos de Execução Docker (Dev vs. Runtime)

**Status:** Proposto
**Data:** 2025-08-31
**Autores:** Gemini (Planejador)

---

## 1. Contexto

Atualmente, o projeto Conductor utiliza uma única configuração de Docker para todas as finalidades, seja para o desenvolvimento do próprio framework ou para a sua aplicação em projetos de terceiros. O modelo de execução atual, definido no `docker-compose.yml`, baseia-se no uso de **volumes (`-v`)** para montar o diretório de código-fonte completo do Conductor (`/mnt/ramdisk/.../conductor`) para dentro do contêiner (em `/app/projects`).

Este modelo nos serviu bem durante a fase inicial de prototipação, pois oferece um ciclo de feedback rápido. No entanto, à medida que o Conductor amadurece, este design único apresenta ambiguidades e riscos significativos, pois mistura dois casos de uso fundamentalmente diferentes:

1.  **Desenvolvimento do Framework:** A necessidade de modificar, depurar e evoluir o próprio Conductor. Este caso de uso requer acesso a ferramentas de meta-programação (como `src/cli/admin.py`) e acesso direto de escrita ao código-fonte do framework.
2.  **Uso do Framework:** A necessidade de aplicar agentes estáveis e seguros do Conductor em um projeto de um "usuário final", que não deve ter acesso ou conhecimento sobre os componentes internos do framework.

A manutenção de um único modelo para ambos os cenários resulta nos seguintes problemas:

*   **Risco de Segurança:** Expor ferramentas de administração (`admin.py`) e a capacidade de auto-edição a um ambiente de usuário final é perigoso. Um usuário poderia, acidentalmente ou não, corromper a sua própria instalação do Conductor.
*   **Falta de Estabilidade e Versionamento:** Os usuários sempre executam a versão mais recente dos agentes disponíveis no código-fonte montado, que pode estar em um estado instável de desenvolvimento. Não há como garantir um ambiente de execução reprodutível e estável para terceiros.
*   **Alta Barreira de Entrada:** O usuário final é forçado a entender a estrutura interna do Conductor, incluindo a distinção entre `admin` e `agent`, para poder utilizá-lo, o que complica desnecessariamente a experiência de onboarding.

**Documentos Relevantes para Contexto:**
*   [Guia de Documentação (`docs/DOCUMENTATION_GUIDE.md`)](docs/DOCUMENTATION_GUIDE.md)
*   [Arquitetura do Executor (`docs/architecture/EXECUTOR_ARCHITECTURE.md`)](docs/architecture/EXECUTOR_ARCHITECTURE.md)

---

## 2. Decisão

Fica decidido que a estratégia de empacotamento e distribuição do Conductor será dividida em **duas imagens Docker distintas e com propósitos claros**, para separar formalmente o ambiente de desenvolvimento do ambiente de execução para o usuário final.

#### **Imagem 1: `conductor-dev`**

*   **Propósito:** Exclusivamente para o desenvolvimento e manutenção do framework Conductor.
*   **Mecanismo:** Continuará a usar **`volumes`** para montar o código-fonte local, garantindo um ciclo de desenvolvimento rápido.
*   **Conteúdo:** Acesso total ao código-fonte, incluindo `src/cli/admin.py` e `src/cli/agent.py`.
*   **Dockerfile:** O `Dockerfile` existente na raiz do projeto.

#### **Imagem 2: `conductor-runtime`**

*   **Propósito:** Para ser distribuída a usuários finais que aplicarão os agentes do Conductor em seus próprios projetos.
*   **Mecanismo:** Usará a instrução **`COPY`** em um novo `Dockerfile.runtime` para embutir os componentes na imagem durante o build. Isso garante que a imagem seja um artefato autocontido e imutável.
*   **Conteúdo:**
    *   Apenas o código essencial para a execução de agentes.
    *   O entrypoint será exclusivamente `src/cli/agent.py`. O `src/cli/admin.py` será **excluído** da imagem.
    *   Um conjunto selecionado e versionado de agentes "oficiais" e estáveis será copiado para dentro da imagem, tornando-os "read-only".
*   **Dockerfile:** Um novo `Dockerfile.runtime` a ser criado.

---

## 3. Consequências

A adoção desta decisão terá as seguintes implicações:

#### Positivas

1.  **Segurança Aprimorada:** Isola completamente os usuários finais dos riscos da meta-programação e da modificação acidental do framework. O `runtime` se torna uma "caixa-preta" segura.
2.  **Estabilidade e Reprodutibilidade:** A imagem `conductor-runtime` será versionada (ex: `conductor-runtime:1.0.0`). Todos os usuários de uma versão específica terão exatamente o mesmo conjunto de agentes e comportamento, garantindo resultados consistentes.
3.  **Experiência do Usuário Simplificada:** O usuário final não precisa mais se preocupar com a estrutura interna do Conductor. Ele apenas precisa saber como executar a imagem `runtime`, montar seu próprio projeto e usar os agentes disponíveis.
4.  **Clareza Arquitetural:** A separação formaliza a distinção entre "construir o motor" e "dirigir o carro", tornando o projeto mais fácil de entender, manter e escalar.

#### Negativas ou a Gerenciar

1.  **Complexidade no Processo de Build:** O sistema de build precisará ser capaz de gerar, testar e gerenciar duas imagens diferentes em vez de uma.
2.  **Necessidade de um Processo de Release:** Deixa de ser possível simplesmente usar o `latest`. Será necessário um processo deliberado para decidir quando um conjunto de agentes está estável o suficiente para ser "promovido" para uma nova versão da imagem `conductor-runtime`. Isso introduz uma sobrecarga de gerenciamento de releases.

---
