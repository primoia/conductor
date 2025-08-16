# Plano Técnico: Onboarding "Conductor Teams"

**Versão:** 1.0

**Para:** Staff Sênior (Claude)

**De:** CTO

**Assunto:** Implementação da Estratégia de Onboarding "Conductor Teams"

## 1. Visão Geral e Alinhamento Estratégico

O objetivo é transformar a experiência de primeiro contato com o Conductor, passando de uma configuração manual de ferramentas para uma ativação contextual de "times" de agentes. Isso visa aumentar drasticamente a adoção e a produtividade inicial, alinhando-se à nossa filosofia "Maestro".

## 2. Arquitetura Conceitual: "Team Templates"

Introduziremos um novo artefato de configuração: o **"Team Template"**.

*   **Localização:** Proponho uma nova pasta `config/teams/` na raiz do projeto para armazenar esses templates.
*   **Estrutura de um Team Template (`team_template.yaml`):**
    ```yaml
    id: backend-kotlin-dev-team
    name: "Time de Desenvolvimento Backend Kotlin"
    description: "Um time otimizado para criar entidades, serviços e testes em Kotlin/Spring."
    persona_type: "Desenvolvedor Backend" # Para a fase de Descoberta
    inherits_from: "base-dev-team" # Opcional: para herança de configurações

    # Lista de agentes a serem incluídos neste time
    agents:
      - id: KotlinEntityCreator_Agent
        config_overrides: # Opcional: configurações específicas para este time
          ai_provider: 'claude'
      - id: KotlinRepositoryCreator_Agent
      - id: KotlinTestCreator_Agent
        config_overrides:
          test_framework: 'junit5'

    # Lista de workflows padrão a serem configurados para este time
    workflows:
      - id: create-new-feature-workflow
        path: "workflows/create_new_feature.yaml" # Caminho para o workflow

    # Exemplos de uso específicos para este time
    usage_examples:
      - name: "Criar nova entidade Product"
        command: "python scripts/genesis_agent.py --embody KotlinEntityCreator_Agent --project-root ./my-kotlin-project --repl"
    ```
*   **Sistema de Herança:** O campo `inherits_from` permitirá a criação de uma hierarquia de times, evitando duplicação e facilitando a manutenção. A lógica de carregamento de templates precisará resolver essa herança.

## 3. O Agente de Onboarding (`Onboarding_Agent`)

Este será um novo Agente Especialista, o coração da experiência "3 Clicks to Productivity".

*   **ID:** `Onboarding_Agent`
*   **Persona:** Guiará o usuário através das fases de Descoberta, Personalização e Ativação.
*   **Ferramentas (`available_tools`):**
    *   `list_team_templates()`: Lista os `team_template.yaml` disponíveis em `config/teams/`.
    *   `apply_team_template(team_id: str, project_root: str, env: str)`: Ferramenta complexa que:
        *   Lê o `team_template.yaml` selecionado (resolvendo herança).
        *   Cria a estrutura de pastas `projects/<env>/<project_name>/agents/`.
        *   Copia/cria os `agent.yaml`, `persona.md`, `state.json` para os agentes do time, aplicando `config_overrides`.
        *   Copia/cria os arquivos de workflow padrão.
        *   Gera um `README.md` inicial no projeto do usuário com exemplos de uso.
    *   `run_shell_command`, `write_file`, `mkdir`: Para operações de sistema de arquivos.

## 4. Refatoração do `genesis_agent.py` (Integração)

*   **Novo Comando Interno:** Adicione um comando `/onboard` ao REPL do Gênesis.
*   **Fluxo:** Quando `/onboard` é chamado, o Gênesis incorpora o `Onboarding_Agent` e inicia o diálogo de 3 cliques.

## 5. Estratégia de Implementação (Phased Rollout - Marcos Técnicos)

**Fase 1: MVP (Mês 1-2)**
*   **Milestone 4.1: Definição de Team Template:**
    *   Crie a pasta `config/teams/`.
    *   Defina a estrutura do `team_template.yaml`.
    *   Crie 2-3 templates básicos (ex: `backend-kotlin-dev-team`, `frontend-react-dev-team`).
*   **Milestone 4.2: `Onboarding_Agent` Básico:**
    *   Defina `Onboarding_Agent` (`agent.yaml`, `persona.md`).
    *   Implemente a ferramenta `list_team_templates`.
    *   Implemente a ferramenta `apply_team_template` (apenas cópia básica, sem herança ainda).
    *   Integre o `/onboard` no `genesis_agent.py`.
*   **Milestone 4.3: Experiência "3 Clicks" (CLI):**
    *   Implemente o diálogo interativo na `persona.md` do `Onboarding_Agent` para guiar o usuário pelas 3 fases.

**Fase 2: Expansão (Mês 3-4)**
*   **Milestone 4.4: Herança de Team Templates:**
    *   Implemente a lógica de resolução de herança para `team_template.yaml`.
    *   Crie templates mais complexos usando herança.
*   **Milestone 4.5: Personalização Avançada:**
    *   Permita que o `Onboarding_Agent` pergunte sobre agentes adicionais/remoções durante a personalização.

**Fase 3: Maturidade (Mês 5-6)**
*   **Milestone 4.6: Otimização e Monitoramento:**
    *   Integre métricas de uso e funil de onboarding.
*   **Milestone 4.7: Interface Web (Opcional):**
    *   Comece o design de uma interface web para o onboarding (projeto separado).
