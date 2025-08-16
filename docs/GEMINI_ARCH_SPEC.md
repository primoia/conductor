# Especificação Arquitetural: Framework de Agentes "Maestro"

**Versão:** 2.0

**Autor:** Gemini (em colaboração com o arquiteto do projeto)

## 1. Visão Geral e Filosofia

Este documento descreve a arquitetura de um framework de agentes de IA de nova geração, codinome "Maestro". O objetivo é superar as limitações de modelos lineares e baseados em templates, criando um ecossistema de desenvolvimento dinâmico, interativo e ciente do contexto.

### Filosofia Central

O framework "Maestro" é projetado para **aumentar a capacidade de um único desenvolvedor (o "Maestro")**, servindo como um parceiro ativo e inteligente no ciclo de vida de desenvolvimento, em vez de tentar simular um time de desenvolvimento completo de forma rígida.

### Princípios Arquiteturais

*   **Interação como Prioridade:** A interação conversacional (chat) é uma funcionalidade de primeira classe, essencial para as fases de análise, planejamento e depuração.
*   **Consciência de Contexto:** Os agentes devem ter a capacidade de acessar e analisar o estado atual do código-fonte para informar suas decisões e diálogos.
*   **Estado Persistente e Evolutivo:** Cada agente possui uma memória persistente (`state.json`) que representa sua compreensão atual do sistema. Este estado evolui à medida que o desenvolvimento progride.
*   **Modelo de Agente Unificado:** Existe uma única maneira de definir um agente através de um arquivo de especificação (`agent.yaml`). Este agente pode, no entanto, ser executado de duas maneiras distintas: interativa ou automatizada.

---

## 2. O Ciclo de Vida de Desenvolvimento "Maestro"

O framework opera em um ciclo de vida contínuo e virtuoso, composto por quatro fases distintas.

> **Metáfora Central:** "O estado é parte do problema, a evolução do estado é o plano, a conclusão do plano é a evolução do estado dentro dos agentes."

### Fase 1: Imersão e Definição do Problema
*   **Entrada:** Uma intenção ou objetivo do Maestro (ex: "Adicionar autenticação via Google").
*   **Processo:** O Maestro inicia uma sessão interativa com um agente especialista (incorporado pelo Agente Mestre). O agente faz perguntas e, crucialmente, acessa o código-fonte para analisar o impacto, as dependências e o contexto técnico. O problema é refinado colaborativamente.
*   **Saída:** Um "Problema Polido", um entendimento profundo e compartilhado do que precisa ser feito.

### Fase 2: Colaboração e Criação do Plano
*   **Entrada:** O "Problema Polido".
*   **Processo:** A sessão interativa continua, focando agora na solução. O agente colabora com o Maestro para definir a abordagem técnica, os passos necessários e as tarefas específicas. O agente pode sugerir a criação de múltiplos agentes especialistas para a fase de execução.
*   **Saída:** Um "Plano Polido", tipicamente na forma de um `implementation_plan.yaml`, pronto para ser executado.

### Fase 3: Execução Orquestrada
*   **Entrada:** O "Plano Polido" (`implementation_plan.yaml`).
*   **Processo:** O Orquestrador `conductor` assume o controle. Ele lê o plano e executa as tarefas de forma não-interativa, chamando os Agentes Especialistas necessários em "Modo Orquestrado" para gerar código, rodar testes, etc.
*   **Saída:** Código novo, testes passando e um Pull Request pronto para revisão.

### Fase 4: Retroalimentação e Evolução do Estado
*   **Entrada:** O Pull Request aprovado e integrado.
*   **Processo:** Um processo (automatizado ou manual) analisa as mudanças e atualiza o `state.json` dos agentes relevantes, informando-os sobre a nova realidade do código-fonte.
*   **Saída:** Agentes com um estado atualizado, prontos para o próximo ciclo de desenvolvimento.

---

## 3. Arquitetura de Componentes

1.  **O Maestro (Humano):** O desenvolvedor. O tomador de decisões final, que guia o processo, valida as sugestões da IA e detém o controle criativo.
2.  **O Agente Mestre ("Gênesis"):** A interface de usuário principal para o modo interativo. É um agente especial cuja única função é **incorporar** outros agentes especialistas para permitir o diálogo, a análise e a depuração.
3.  **Agentes Especialistas:** Os "fazedores". Cada um é um especialista em uma tarefa (ex: `KotlinEntityCreator_Agent`, `TerraformPlanner_Agent`). São definidos por um `agent.yaml`.
4.  **O Orquestrador (`conductor`):** O motor de execução para o modo automático. Ele lê um plano e executa os agentes especialistas de forma eficiente e não-interativa.
5.  **O Artefato de Definição (`agent.yaml`):** O "DNA" de um agente. Um arquivo de especificação que torna um agente compreensível tanto para o Agente Mestre (para incorporação) quanto para o Orquestrador (para execução).

---

## 4. O Artefato de Definição do Agente (`agent.yaml`)

Este arquivo é o coração da arquitetura. Ele define tudo o que o sistema precisa saber sobre um agente.

```yaml
# Exemplo: agent.yaml para um criador de entidades

id: KotlinEntityCreator_Agent
version: 1.0
description: "Cria uma entidade de dados Kotlin com anotações JPA a partir de uma especificação."

# (NOVO) Define qual motor de IA usar para este agente.
# Valores válidos: 'claude' ou 'gemini'.
ai_provider: 'claude'

# Caminho para o prompt que define a personalidade e o comportamento
persona_prompt_path: "persona.md"

# Caminho para o arquivo de estado (memória) do agente
state_file_path: "state.json"

# Tarefa a ser executada no modo automático (pelo Conductor)
# A instrução pode ser um prompt direto ou um caminho para um arquivo de tarefa
execution_task: |
  Com base no `input_file` fornecido no plano, gere a entidade Kotlin.
  O `input_file` contém a especificação dos campos.
  Salve o resultado no `output_file` especificado no plano.

# Ferramentas disponíveis no modo interativo (pelo Agente Mestre)
available_tools:
  - read_file
  - list_directory
  - run_shell_command

# Esquema esperado para o state.json (opcional, para validação)
state_schema:
  last_entity_created: string
  common_field_patterns: array
```

---

## 5. Modos de Execução

Um agente, definido por um único `agent.yaml`, pode operar de duas maneiras:

### Modo Incorporado (Interativo)
*   **Invocação:** `python genesis_agent.py --embody <agent_id> --project-root <caminho_para_o_projeto>`
*   **Processo:** O Agente Mestre lê o `agent.yaml` do agente alvo. Ele carrega a persona, o estado e as ferramentas (`available_tools`) em uma sessão de chat. O Gênesis usa o `--project-root` para contextualizar todas as chamadas de ferramentas (ex: `read_file`), garantindo que o agente opere apenas dentro do projeto alvo.
*   **Casos de Uso:** Análise de problemas, criação de planos, depuração interativa de um agente que falhou no modo automático, refatoração guiada.

### Modo Orquestrado (Automático)
*   **Invocação:** `python conductor.py --plan <plan.yaml>`
*   **Processo:** O Orquestrador `conductor` lê o plano, identifica o `agent_id` para uma tarefa, carrega seu `agent.yaml` e usa a diretiva `execution_task` para executar a tarefa de forma não-interativa, passando os parâmetros definidos no plano (como `input_file` e `output_file`).
*   **Casos de Uso:** Geração de código em massa, execução de testes, tarefas de CI/CD, automação de refatoração.

---

## 6. Exemplo de Fluxo de Trabalho

1.  **Criação do Agente (se necessário):** O Maestro usa o `AgentCreator_Agent` para criar um novo agente especialista dentro do caminho de contexto correto, ex: `projects/develop/my-app/agents/MyNewTaskAgent`.
2.  **Intenção:** O Maestro quer adicionar um campo `tags` à entidade `Product` no projeto `my-app`.
3.  **Fase 1 (Análise):**
    *   O Maestro inicia: `python genesis_agent.py --embody KotlinEntityCreator_Agent --project-root /path/to/my-app --repl`
    *   Na sessão de chat, ele diz: "Preciso adicionar um campo `tags` à entidade `Product`. Pode analisar o arquivo `src/Product.kt` e me dizer o impacto?"
    *   O agente (incorporado) usa sua ferramenta `read_file` (contextualizada pelo Gênesis para `/path/to/my-app/src/Product.kt`) e responde com os detalhes.
4.  **Fase 2 (Planejamento):**
    *   Eles colaboram e definem a abordagem. O resultado é um `implementation_plan.yaml`.
5.  **Fase 3 (Execução):**
    *   O Maestro executa: `python conductor.py --plan a_plan.yaml`
    *   O `conductor` executa as tarefas, gerando o código dentro do projeto `my-app`.
6.  **Fase 4 (Feedback):**
    *   Após o PR ser aprovado, o `state.json` do `KotlinEntityCreator_Agent` é atualizado.