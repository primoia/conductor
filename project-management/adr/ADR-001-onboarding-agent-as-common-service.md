# ADR-001: Promoção do OnboardingGuide_Agent para Meta-Agente Comum

**Status:** Implementado
**Data:** 2025-08-17

## Contexto

O `OnboardingGuide_Agent` foi inicialmente concebido como um agente específico de projeto, residindo em `projects/develop/<project-name>/agents/`. Esta implementação gerou um conflito arquitetural e uma experiência de usuário (DX) subótima. A tarefa de guiar um novo usuário na configuração do framework e na seleção de uma equipe inicial de agentes (`Team Template`) é uma responsabilidade do **framework**, e não de um **projeto** específico que o consome.

A invocação do agente via `genesis_agent.py` exigia que o usuário fornecesse um contexto de projeto (`--environment` e `--project`) antes mesmo de ter um projeto devidamente configurado, criando um paradoxo no fluxo de primeiro uso.

## Decisão

Para alinhar o agente à sua real função e aos princípios arquiteturais do Conductor, foi decidido:

1.  **Reclassificar o `OnboardingGuide_Agent` como um Meta-Agente.**
2.  **Mover fisicamente** o diretório do agente de sua localização específica de projeto para o diretório de agentes comuns: `projects/_common/agents/`.
3.  **Remover a configuração `target_context`** do `agent.yaml` do agente, desvinculando-o de qualquer projeto ou escopo de escrita específico.
4.  **Estabelecer o `admin.py` como o único ponto de invocação** para o `OnboardingGuide_Agent`, consolidando-o como uma ferramenta administrativa do framework.

## Justificativa (Rationale)

Esta decisão se baseia em quatro pilares fundamentais de engenharia de software:

1.  **Princípio da Responsabilidade Única (SRP):** A responsabilidade de onboarding é do framework. A refatoração aloca o agente ao seu domínio lógico correto.

2.  **Melhora da Experiência do Desenvolvedor (DX):** Simplifica drasticamente o primeiro contato do usuário. O ponto de entrada torna-se um comando único e sem pré-requisitos: `python scripts/admin.py --agent OnboardingGuide_Agent --repl`.

3.  **Consistência Arquitetural:** Reforça a distinção clara entre meta-agentes (que gerenciam o framework) e agentes de projeto (que operam em código de projeto). A localização e o método de invocação do `OnboardingGuide_Agent` agora são consistentes com os de outros meta-agentes, como o `AgentCreator_Agent`.

4.  **Manutenibilidade e Escalabilidade:** Centralizar este componente crítico em `_common` facilita sua manutenção e garante que uma única versão aprimorada beneficie todos os usuários e projetos futuros, em vez de manter cópias potencialmente divergentes.

## Consequências

- **Positivas:**
    - O fluxo de trabalho para novos usuários está mais limpo, lógico e documentado no `README.md`.
    - A arquitetura do projeto está mais coesa e fácil de entender.
    - Reduz a carga cognitiva para iniciar o uso do framework.

- **Negativas/Impacto:**
    - Qualquer documentação ou script de teste que se referia ao método de invocação antigo (`genesis_agent.py`) tornou-se obsoleto e precisou ser atualizado. Esta atualização já foi realizada no `README.md` principal.

## Detalhes da Implementação (Registro Histórico)

A transição foi executada através dos seguintes comandos:

1.  **Movimentação do diretório:**
    ```bash
    mv projects/develop/your-project-name/agents/OnboardingGuide_Agent projects/_common/agents/OnboardingGuide_Agent
    ```
2.  **Atualização da configuração (`agent.yaml`):
    - A seção `target_context` foi removida do arquivo de configuração do agente para dessassociá-lo de um projeto específico.
