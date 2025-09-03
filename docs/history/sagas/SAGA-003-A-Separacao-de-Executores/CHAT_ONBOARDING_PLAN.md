# Plano Técnico: Agente Chat Onboarding

**Versão:** 1.0

**Para:** Staff Sênior (Claude)

**De:** CTO

**Assunto:** Implementação da Estratégia de Onboarding Conversacional

## 1. Visão Geral e Alinhamento Estratégico

O objetivo é criar uma experiência de onboarding guiada por um agente de IA, transformando a configuração inicial do Conductor em um diálogo intuitivo e personalizado. Isso visa aumentar drasticamente a taxa de sucesso no primeiro contato, a retenção e a satisfação do usuário, alinhando-se à nossa filosofia "Maestro".

## 2. O Agente de Onboarding (`OnboardingGuide_Agent`)

Este será um novo Agente Especialista, o coração da experiência "3 Clicks to Productivity".

*   **ID:** `OnboardingGuide_Agent`
*   **Persona:** Será o "Conductor Guide" ou "Mentor Amigável", com personalidade paciente, didática e encorajadora. Sua `persona.md` guiará o diálogo através das 5 fases do onboarding.
*   **Ferramentas (`available_tools`):**
    *   `collect_user_profile()`: Ferramenta para coletar informações do usuário (nome, papel, linguagem, etc.).
    *   `suggest_team_template(user_profile: dict)`: Ferramenta para recomendar `team_template.yaml` com base no perfil do usuário.
    *   `apply_team_template(team_id: str, project_root: str, env: str)`: Ferramenta complexa já definida no `ONBOARDING_TEAMS_PLAN.md` para aplicar o template selecionado.
    *   `create_example_project(project_root: str, team_id: str)`: Ferramenta para criar um projeto de exemplo básico para o "Primeiro Uso Guiado".
    *   `run_shell_command`, `write_file`, `mkdir`, `list_team_templates`: Ferramentas padrão para operações de sistema de arquivos e listagem de templates.

## 3. Refatoração do `genesis_agent.py` (Integração)

*   **Comando Simplificado de Entrada:** Implementar um alias `conductor start` que, internamente, executa `python scripts/genesis_agent.py --embody OnboardingGuide_Agent --repl`. Isso pode ser feito com um pequeno script shell ou um wrapper Python.
*   **Comando Interno `/onboard`:** O Gênesis deve reconhecer `/onboard` no REPL para iniciar o processo de onboarding se o usuário não tiver começado com `conductor start`.

## 4. Estratégia de Implementação (Phased Rollout - Marcos Técnicos)

**Fase 1: Onboarding Básico (MVP - Conversacional Core)**
*   **Milestone 5.1: Definição do `OnboardingGuide_Agent`:**
    *   Crie o `agent.yaml` e a `persona.md` para o `OnboardingGuide_Agent`.
    *   Defina o `state.json` inicial.
*   **Milestone 5.2: Ferramentas de Coleta e Sugestão:**
    *   Implemente `collect_user_profile()` (ferramenta que interage com o usuário para coletar dados).
    *   Implemente `suggest_team_template()` (ferramenta que usa o perfil para recomendar templates).
*   **Milestone 5.3: Fluxo Conversacional Básico:**
    *   Implemente as Fases 1, 2 e 3 do fluxo de onboarding na `persona.md` do `OnboardingGuide_Agent`, utilizando as ferramentas implementadas.
    *   Integre a chamada à `apply_team_template` (já existente) na Fase 4.
*   **Milestone 5.4: Alias `conductor start`:**
    *   Crie o script wrapper para o comando `conductor start`.

**Fase 2: Onboarding Inteligente (Contextualização & Personalização)**
*   **Milestone 5.5: Primeiro Uso Guiado:**
    *   Implemente a ferramenta `create_example_project`.
    *   Implemente a Fase 5 do fluxo de onboarding na `persona.md`.
*   **Milestone 5.6: Personalização Avançada:**
    *   Permita que o `OnboardingGuide_Agent` guie o usuário na adição/remoção de agentes do time sugerido.

**Fase 3: Onboarding Contextual (Analytics & Melhoria Contínua)**
*   **Milestone 5.7: Métricas e Feedback:**
    *   Integre a coleta de métricas do funil de onboarding.
    *   Implemente mecanismos de feedback para o `OnboardingGuide_Agent` aprender e melhorar.
