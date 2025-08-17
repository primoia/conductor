# Plano de Refatoração: OnboardingGuide_Agent para Common Agent

**Autor:** Gemini
**Status:** Proposto

## 1. Resumo Executivo

Este plano detalha a refatoração do `OnboardingGuide_Agent`, movendo-o de um agente específico de projeto para um agente comum (`common`). Esta mudança o tornará um componente central do framework, acessível globalmente para guiar novos usuários, em vez de estar atrelado a um projeto particular.

## 2. Justificativa

A função do `OnboardingGuide_Agent` é guiar os usuários através da configuração inicial do framework e da estrutura de um novo projeto. Esta é uma tarefa de nível de framework, não de nível de projeto. 

- **Alinhamento Arquitetural:** A arquitetura atual separa claramente os "meta-agentes" (em `_common`) que gerenciam o framework, dos "agentes de projeto". O `OnboardingGuide_Agent` se encaixa perfeitamente na definição de um meta-agente.
- **Acessibilidade:** Como um agente comum, ele poderá ser invocado de forma simples através do `admin.py`, sem a necessidade de especificar um `--environment` ou `--project`, o que simplifica a experiência do novo usuário.
- **Manutenção:** Centralizar o agente em `_common` facilita sua manutenção e garante que todos os usuários utilizem a mesma versão do guia de onboarding.

## 3. Plano de Execução

O processo será executado em duas etapas principais:

### 3.1. Mover o Diretório do Agente

A primeira etapa é mover fisicamente os arquivos do agente para o diretório de agentes comuns.

- **Comando:**
  ```bash
  mv projects/develop/your-project-name/agents/OnboardingGuide_Agent projects/_common/agents/OnboardingGuide_Agent
  ```

### 3.2. Atualizar a Configuração do Agente

Agentes comuns não devem ter um `project_key` em sua configuração, pois não estão associados a nenhum projeto específico.

- **Ação:** Remover a linha `project_key: your-project-name` do arquivo `projects/_common/agents/OnboardingGuide_Agent/agent.yaml`.

## 4. Verificação

Após a execução do plano, a refatoração será verificada da seguinte forma:

1.  **Acesso via `admin.py`:** O agente deve ser executável com sucesso através do executor administrativo.
    - **Comando de Teste:** `python scripts/admin.py --agent OnboardingGuide_Agent --repl`
2.  **Falha no Acesso via `genesis_agent.py`:** Uma tentativa de executar o agente através do executor de projeto deve falhar, pois ele não existirá mais naquele contexto.

## 5. Análise de Impacto

- **Positivo:** A experiência do usuário para o primeiro contato com o framework será simplificada.
- **Negativo:** Nenhum impacto negativo é esperado. Quaisquer referências antigas ao agente em documentos ou scripts de teste (como em `test_onboarding_manual.py`) precisarão ser atualizadas para refletir o novo método de invocação via `admin.py`.
