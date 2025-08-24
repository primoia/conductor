# SAGA-006: A Jornada para a Arquitetura Híbrida Definitiva

**Data:** 24 de agosto de 2025
**Autores:** Primo (Gemini), Arquiteto do Projeto
**Status:** Concluído

## 1. Contexto Inicial

Esta saga documenta o processo de descoberta e decisão que levou à refatoração da arquitetura de execução de agentes do Framework Conductor. A investigação começou com uma questão simples: "Por que existem dois scripts de execução, `admin.py` e `genesis_agent_v2.py`, e essa separação é realmente necessária?"

A análise inicial revelou que a separação era intencional, baseada no Princípio da Responsabilidade Única:
-   `admin.py`: Para meta-agentes que gerenciam o próprio framework, operando sem um "sandbox" de segurança.
-   `genesis_agent_v2.py`: Para agentes de projeto que operam em código externo, com um "sandbox" de segurança forte para prevenir acesso fora do diretório do projeto alvo.

Esta explicação, embora tecnicamente correta, foi considerada insuficiente, pois não resolvia um paradoxo fundamental na operação de agentes de IA.

## 2. O Paradoxo Central: Contexto vs. Estado

A discussão aprofundada revelou um conflito inerente e insolúvel no modelo original:

1.  **A Necessidade de Contexto:** Um agente de IA eficaz precisa de acesso irrestrito ao sistema de arquivos do projeto em que atua. Ele deve ser capaz de explorar dinamicamente o código, ler múltiplos arquivos e entender a base de código de forma holística. Isso exige que o processo do agente seja executado **de dentro** do diretório do projeto alvo.

2.  **A Necessidade de Estado:** Um agente interativo e inteligente precisa de sua "alma": seus arquivos de definição (`agent.yaml`, `persona.md`) e seu histórico de conversas (`state.json`). No modelo original, esses arquivos residiam permanentemente no repositório central do Conductor.

Isso criou um impasse:
-   Executar o agente a partir do Conductor dava-lhe **Estado**, mas não **Contexto**.
-   Executar o agente a partir do Projeto Alvo dava-lhe **Contexto**, mas não **Estado**.

## 3. A Exploração de Modelos Arquiteturais

Para resolver o paradoxo, dois modelos principais foram propostos e analisados.

### Modelo A: O "Lançador Centralizado"

A primeira solução proposta foi a criação de um "Lançador" que tentava unir os dois mundos em tempo de execução.

-   **Fluxo:** Um script no Conductor (o Lançador) copiaria temporariamente os arquivos de estado do agente para uma pasta oculta no projeto alvo, executaria o agente de dentro do projeto alvo e, ao final, copiaria o estado modificado de volta para o Conductor.
-   **Vantagens:** Mantinha a inteligência (definições de agente) centralizada, permitindo atualizações instantâneas para todos os projetos.
-   **Desvantagens (Apontadas pelo Arquiteto):** O modelo se mostrou frágil. O que aconteceria se a versão mais recente de um agente centralizado fosse incompatível com o código de um projeto específico? Isso forçaria um ciclo de testes em todos os projetos a cada atualização de agente, um fardo insustentável.

### Modelo B: A "Implantação Distribuída"

A segunda proposta, vinda do Arquiteto, foi uma mudança de paradigma: tratar os agentes como artefatos de software que são implantados e versionados com o projeto alvo.

-   **Fluxo:** O Conductor se tornaria uma "Fábrica" de agentes. Um "Curador" (ex: Tech Lead) no projeto alvo importaria uma versão específica de um agente da Fábrica, testaria contra o código do projeto e, uma vez estabilizado, commitaria os arquivos do agente no repositório do próprio projeto.
-   **Vantagens:** Resolvia o problema de compatibilidade, atrelando a versão do agente à versão do código. Facilitava o fluxo de trabalho em equipe, onde desenvolvedores apenas consomem a versão do agente já estabilizada pelo Curador.
-   **Desvantagens:** A propagação de melhorias nos agentes se tornaria um processo de deploy lento e manual para cada projeto. A complexidade mudaria do "tempo de execução" (com o Lançador) para o "tempo de implantação".

## 4. A Síntese: A Arquitetura Híbrida de "Cache Local Estabilizado"

A discussão sobre os trade-offs do Modelo B levou à solução final, que combina o melhor de ambos os mundos. A percepção chave foi que o fluxo de trabalho interativo da equipe e o fluxo de trabalho autônomo do `run_conductor.py` tinham necessidades diferentes.

A arquitetura final, documentada em detalhes no documento de arquitetura principal, adota o Modelo B ("Implantação Distribuída") como base, mas com uma adição crucial para a execução autônoma.

-   **Para Times (Desenvolvimento Interativo):** As equipes usam a versão do agente que está "em cache" e commitada em seu repositório local. É estável e previsível.
-   **Para Automação (`run_conductor.py`):** O orquestrador ganha a flexibilidade de escolher qual versão do agente executar, via um parâmetro no plano de execução:
    -   `version: stable`: Executa a versão do "cache local" do projeto alvo. (Modo seguro e padrão).
    -   `version: latest`: Ignora o cache local e usa o "Padrão Lançador" para injetar a versão mais recente da Fábrica. (Modo experimental/avançado).

Esta solução híbrida foi adotada por ser a única que satisfaz todos os requisitos identificados: estabilidade para a equipe, poder para a automação, compatibilidade de versão e manutenção centralizada da inteligência dos agentes.

---
**Decisão Final:** Adotar o modelo de "Cache Local Estabilizado".

➡️ **[Ver a Arquitetura Final Detalhada](../../architecture/HYBRID_AGENT_ARCHITECTURE.md)**
