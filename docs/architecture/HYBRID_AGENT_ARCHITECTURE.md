# Arquitetura de Agentes: O Modelo Híbrido de "Cache Local Estabilizado"

**Status:** Proposto e Aceito
**Data:** 24 de agosto de 2025

Este documento descreve a arquitetura de execução de agentes para o Framework Conductor. Ela foi projetada para ser robusta, escalável e para suportar fluxos de trabalho complexos tanto para equipes de desenvolvimento quanto para automação não-interativa.

> Para entender o processo de decisão e a jornada que levou a este design, consulte a [**SAGA-006: A Arquitetura Híbrida Definitiva**](../sagas/SAGA-006-A-Arquitetura-Hibrida-Definitiva/README.md).

## 1. Visão Geral e Princípios

Esta arquitetura resolve o conflito entre a necessidade de um agente ter **acesso ao contexto** de um projeto e, ao mesmo tempo, manter sua **identidade e estado**. Ela se baseia em três princípios:

1.  **Centralização da Inteligência:** Os agentes são projetados e mantidos em um local central (a "Fábrica"), permitindo que a inteligência seja aprimorada e reutilizada.
2.  **Estabilização Local:** A versão de um agente usada por uma equipe no dia-a-dia é versionada junto com o código do projeto, garantindo compatibilidade e estabilidade.
3.  **Execução Contextualizada:** A execução de um agente sempre ocorre com o processo rodando de dentro do diretório do projeto alvo, garantindo acesso total e seguro aos arquivos.

## 2. Componentes da Arquitetura

### a. A "Fábrica de Agentes" (O Repositório Conductor)

-   **Propósito:** É o centro de design, criação e manutenção de todos os agentes.
-   **Componentes Chave:**
    -   `projects/_common/agents/`: Contém os meta-agentes.
    -   `projects/<env>/<proj>/agents/`: Contém as versões "master" dos agentes de projeto.
    -   `scripts/admin.py`: A ferramenta CLI para o "Engenheiro de Agentes", usada para criar, testar e implantar agentes.
    -   `scripts/run_conductor.py`: O orquestrador para execução autônoma baseada em planos.

### b. O Projeto Alvo (ex: `nex-web-backend`)

-   **Propósito:** É o ambiente de produção para os agentes. É autocontido e autônomo.
-   **Componentes Chave:**
    -   `agents/`: Uma pasta versionada pelo Git do projeto, que contém a cópia **estabilizada** dos agentes que foram testados e aprovados para a versão atual do código. Este é o "Cache Local".
    -   `.conductor/client.py`: Um executor leve, também versionado, que a equipe usa para interagir com os agentes no "Cache Local".
    -   `state.json` (dentro de cada pasta de agente): Armazena o histórico de conversas. Recomenda-se adicionar `**/state.json` ao `.gitignore` do projeto.

## 3. Atores e Fluxos de Trabalho

### a. O "Engenheiro/Curador de Agentes" (ex: Tech Lead)

Este é o fluxo de trabalho para atualizar um agente para um projeto.

1.  **Design na Fábrica:** O Engenheiro trabalha no repositório Conductor para criar ou melhorar um agente.
2.  **Teste Remoto:** Usando `admin.py`, ele testa a nova versão do agente (da Fábrica) contra o código do projeto alvo, sem modificar o projeto ainda.
    -   `admin.py test-agent --agent MyAgent-v1.3 --on-project /path/to/nex-web-backend`
3.  **Publicação (Deploy):** Uma vez satisfeito, ele "publica" o agente. O comando copia os arquivos do agente da Fábrica para a pasta `agents/` do projeto alvo.
    -   `admin.py deploy-agent --agent MyAgent-v1.3 --to-project /path/to/nex-web-backend`
4.  **Estabilização e Commit:** O Engenheiro, agora trabalhando no repositório do projeto alvo, roda os testes de regressão do projeto para garantir que o novo agente não quebrou nada. Se tudo estiver OK, ele **commita a nova versão do agente** no repositório do projeto alvo. A nova versão está agora "estabilizada".

### b. O "Consumidor de Agentes" (Desenvolvedor da Equipe)

-   **Fluxo de Trabalho:** Simples e direto.
    1.  `git pull` no projeto alvo.
    2.  Executa `python .conductor/client.py --agent MyAgent --repl` para interagir com a versão do agente que está garantida para funcionar com o código que ele acabou de baixar.
    3.  Ele não precisa saber sobre a "Fábrica" ou o Conductor.

### c. O Orquestrador Autônomo (`run_conductor.py`)

-   **Fluxo de Trabalho:** O orquestrador executa um plano (`.yaml`) que especifica qual agente executar em qual projeto. Ele possui dois modos de operação, definidos no plano:
    -   **`version: stable` (Padrão):** O orquestrador executa o agente que está no "Cache Local" do projeto alvo. Este é o modo seguro, previsível e ideal para automação de produção, pois usa a versão que foi explicitamente testada e commitada com o código.
    -   **`version: latest` (Experimental):** O orquestrador ignora o cache local e usa o "Padrão Lançador" para injetar a versão mais recente do agente diretamente da "Fábrica". Útil para testes de integração contínua da própria Fábrica de Agentes.

## 4. Conclusão

Este modelo híbrido oferece um equilíbrio robusto entre centralização e distribuição. Ele garante que:
-   A **inteligência** dos agentes possa ser desenvolvida e mantida de forma centralizada.
-   A **estabilidade** seja garantida pelo versionamento dos agentes junto com o código que eles manipulam.
-   O **fluxo de trabalho da equipe** seja simples e desacoplado da complexidade do gerenciamento de IA.
-   A **automação** possa operar de forma segura e previsível, com a opção de usar recursos de ponta quando necessário.
