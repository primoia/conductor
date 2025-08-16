# Guia de Design de Agentes: Padrões e Melhores Práticas

**Versão:** 1.0

**Público-alvo:** Desenvolvedores, Arquitetos, Designers de Agentes

## 1. Introdução

Este documento estabelece os padrões e as melhores práticas para o design e a criação de Agentes Especialistas dentro do Framework Maestro. Aderir a estes padrões é crucial para garantir que o ecossistema seja manutenível, seguro e escalável.

## 2. A Filosofia do Agente Especialista

Um Agente Especialista não é uma IA de propósito geral. Ele é uma **ferramenta de precisão**. Cada agente deve ser projetado com uma **única e clara responsabilidade**. Evite criar agentes "faz-tudo".

*   **Bom:** `KotlinEntityCreator_Agent` (cria entidades), `TerraformPlanValidator_Agent` (valida planos Terraform).
*   **Ruim:** `Development_Agent` (muito genérico), `CodeAndDocs_Agent` (duas responsabilidades distintas).

## 3. Anatomia de um Agente

Cada agente é definido por três arquivos principais. Entender o papel de cada um é o primeiro passo para um bom design.

*   `agent.yaml`: O **DNA**. Define os metadados, as capacidades e o provedor de IA. É a ficha técnica do agente.
*   `persona.md`: A **Alma**. Define a personalidade, o comportamento, a filosofia e os comandos específicos do agente. É como o agente "pensa".
*   `state.json`: A **Memória**. Armazena o estado da sessão, o histórico de conversas e o conhecimento adquirido. É a memória de curto e longo prazo do agente.

## 4. Padrões de Design de Persona

A `persona.md` é o componente mais crítico para o sucesso de um agente.

*   **Seja Específico e Dê um Papel Claro:** Em vez de "Você é um assistente de IA", use "Você é um Engenheiro de QA Sênior especialista em testes de regressão".
*   **Dê um Nome:** Ajuda a IA a manter o personagem. Ex: "Seu nome é 'Contexto'", "Seu nome é 'Estrategista'".
*   **Defina uma Filosofia:** Dê ao agente 2-3 princípios que guiarão suas decisões. Ex: "Princípio 1: Segurança em primeiro lugar. Sempre questione o impacto de uma mudança."
*   **Estruture o Comportamento:** Use seções claras (`## Identidade`, `## Filosofia`, `## Comportamento no Diálogo`) para organizar as instruções.

## 5. Padrões de Uso de Ferramentas (Poderes Especiais)

As ferramentas são as "mãos" do agente. Use-as com sabedoria.

*   **Princípio do Menor Privilégio:** No `agent.yaml`, na seção `available_tools`, liste **apenas** as ferramentas que o agente absolutamente precisa para sua função. Um agente que apenas lê código não precisa de `write_file` ou `run_shell_command`.
*   **Segurança com `run_shell_command`:** Esta é a ferramenta mais poderosa e perigosa. Aderir à `allowlist` de comandos seguros definida no motor Gênesis é mandatório. A persona de um agente que usa esta ferramenta deve ser instruída a ser extremamente cautelosa.
*   **Idempotência:** Sempre que possível, projete tarefas para serem idempotentes. Se uma tarefa for executada duas vezes, o resultado deve ser o mesmo. Isso torna o sistema mais resiliente.

## 6. Escolhendo o Provedor de IA (`ai_provider`)

A escolha da IA no `agent.yaml` deve ser uma decisão de design consciente, baseada na tarefa do agente.

*   **Use `claude` (Claude 3.5 Sonnet ou superior) para:**
    *   Tarefas de raciocínio complexo e multi-passo.
    *   Geração de código de alta qualidade e complexidade.
    *   Análise de segurança e arquitetura.
    *   Agentes que precisam seguir instruções longas e detalhadas (como o `AgentCreator_Agent`).

*   **Use `gemini` (Gemini 1.5 Flash/Pro) para:**
    *   Tarefas de extração de dados e sumarização.
    *   Geração de documentação a partir de código.
    *   Tradução de conteúdo.
    *   Tarefas que exigem um custo menor e uma resposta mais rápida, com um raciocínio ligeiramente menos complexo.

## 7. Gestão de Estado (`state.json`)

O `state.json` é a memória do agente. Use-o para dar continuidade e contexto entre as sessões.

*   **Defina um Esquema:** Use a chave opcional `state_schema` no `agent.yaml` para documentar a estrutura esperada do seu `state.json`. Isso ajuda na manutenção.
*   **Não Armazene Segredos:** O estado é salvo em disco como texto puro. Nunca armazene senhas, chaves de API ou outras informações sensíveis no estado.
*   **Mantenha-o Enxuto:** Evite salvar dados massivos (como o conteúdo de arquivos inteiros) no estado. Salve referências (caminhos de arquivo) ou resumos. A gestão de memória do Gênesis (sliding window) ajuda no histórico da conversa, mas o estado estruturado é responsabilidade do designer do agente.
