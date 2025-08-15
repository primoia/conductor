# Plano de Execução e Design: Agente Mestre (Gênesis)

**Versão do Documento:** 2.1

**Status:** Proposta Final para Implementação (com mecanismo de comandos)

**Autor:** CTO

**Referência:** Este documento é o design de implementação para o **"Modo Incorporado"** descrito na [Especificação Arquitetural "Maestro"](./GEMINI_ARCH_SPEC.md) e incorpora as capacidades metaprogramáticas de criação de agentes.

---

### 1. Objetivo e Filosofia

O `genesis_agent.py` é o núcleo interativo do framework Maestro. Sua função é ser uma aplicação de linha de comando (CLI) stateful que **incorpora** um Agente Especialista, servindo como a principal interface para o Maestro (desenvolvedor) nas fases de análise, planejamento e depuração.

### 2. Lógica de Inicialização e "Embodiment"

**2.1. Análise de Argumentos de Linha de Comando:**
*   `--embody <agent_id>`: **(Obrigatório)** O ID do Agente Especialista a ser incorporado.
*   `--state <caminho_para_state>`: **(Opcional)** Carrega um arquivo de estado de uma sessão anterior.
*   `--verbose`: **(Opcional)** Ativa logging detalhado.

**2.2. Processo de Carregamento do Agente:**
1.  **Localização:** Encontra o diretório `projects/develop/agents/<agent_id>/`.
2.  **Leitura do DNA:** Faz o parse do `agent.yaml` para obter a configuração da sessão.
3.  **Leitura da Persona:** Carrega o conteúdo do `persona.md`.
4.  **Leitura da Memória:** Carrega o `state.json`.

**2.3. Preparação do Motor de IA (Claude):**
1.  **Construção do Prompt do Sistema:** O prompt do sistema será composto por:
    *   **Instrução Mestre:** Define o papel do Gênesis como um incorporador de agentes.
    *   **Persona do Agente:** O conteúdo do `persona.md` do agente incorporado.
    *   **Instruções de Ferramentas e Comandos:** Descreve as ferramentas e os comandos de agente disponíveis e a sintaxe para usá-los (ver Seção 4).
2.  **Inicialização do Cliente da API:** Prepara a conexão com a API do Claude.

### 3. O Loop de Conversação Interativo (REPL)

O coração da aplicação, um ciclo Read-Eval-Print-Loop.

1.  **READ:** Exibe um prompt dinâmico (ex: `[ProblemRefiner_Agent] > `) e aguarda o input do Maestro.
2.  **EVAL:** Processa o input:
    *   **Comandos Internos (Gênesis):** Verifica se o input começa com `/`.
        *   `/exit`: Encerra a sessão (com confirmação para salvar o estado).
        *   `/save`: Força a persistência do `state.json` atual.
        *   `/help`: Mostra os comandos internos do Gênesis.
        *   `/agent_help`: Mostra os comandos específicos do agente incorporado (ver Seção 4.1).
        *   `/new_agent`: Atalho para `genesis_agent.py --embody AgentCreator_Agent` (ver Seção 7).
    *   **Comandos de Agente:** Verifica se o input começa com `*`. Se sim, tenta executar o comando específico do agente (ver Seção 4.1).
    *   **Chamada de IA (Chat):** Se não for um comando, o input é tratado como uma mensagem de chat.
        a. A mensagem é adicionada ao histórico da conversa no `state.json`.
        b. O histórico completo é enviado ao Claude junto com o prompt do sistema.
    *   **Análise da Resposta da IA:** A resposta do Claude é analisada em busca de uma chamada de ferramenta (`[TOOL_CALL: ...]`).
        a. **Se encontrar uma ferramenta:** O Gênesis executa a ferramenta, adiciona o resultado ao histórico e faz uma nova chamada à IA com o resultado para interpretação.
        b. **Se não encontrar:** A resposta é tratada como texto puro.
3.  **PRINT:** Exibe a resposta final da IA para o Maestro.
4.  **LOOP:** Retorna ao passo 1.

### 4. Ferramentas e Comandos ("Poderes Especiais")

**4.1. Ferramentas do Sistema (Invocadas pela IA):**
*   **Definição:** Funções Python no Gênesis (ex: `_tool_read_file`), registradas em um `TOOL_REGISTRY`.
*   **Disponibilidade:** O `agent.yaml` define quais ferramentas um agente pode solicitar via `available_tools`.
*   **Execução:** A IA solicita a execução via `[TOOL_CALL: ...]`. O Gênesis valida e executa.

**4.2. Comandos de Agente (Invocados pelo Usuário):**
*   **Definição:** A `persona.md` de um agente pode conter uma seção `## Comandos` que lista ações específicas (iniciadas por `*`). Ex: `*create-prd: Inicia o processo de criação de um PRD.`.
*   **Parse e Descoberta:** Ao incorporar um agente, o Gênesis deve fazer o parse da seção `## Comandos` da persona para saber quais comandos o agente oferece.
*   **Execução:** Quando o Maestro digita um comando como `*create-prd`, o Gênesis adiciona uma instrução ao histórico da conversa antes de chamar a IA: `[USER_COMMAND: O usuário invocou o comando '*create-prd'. Prossiga com a lógica definida para este comando.]`. Isso instrui a IA a executar a tarefa associada ao comando.
*   **Ajuda:** O comando `/agent_help` do Gênesis deve listar os comandos (`*`) encontrados na persona do agente atualmente incorporado.

### 5. Gestão de Estado e Persistência

O `state.json` é a memória da sessão, carregado no início e salvo via `/save` ou ao sair.

### 6. Estrutura de Código Sugerida

Uma estrutura de classes clara para guiar a implementação:

*   `GenesisAgent`: A classe principal.
*   `Toolbelt`: Módulo com as funções das ferramentas.
*   `CommandParser`: Módulo para extrair comandos da `persona.md`.
*   `LLMClient`: Wrapper para a API do Claude.

---

### 7. Capacidades Metaprogramáticas: Criação de Agentes

**7.1. Filosofia:** A criação de agentes é uma tarefa especializada, delegada a um agente específico, o `AgentCreator_Agent` ("Agente Zero").

**7.2. Fluxo de Trabalho de Criação:**
1.  **Invocação:** O Maestro executa `python genesis_agent.py --embody AgentCreator_Agent` (ou o atalho `/new_agent`).
2.  **Diálogo de Design:** O `AgentCreator_Agent` (incorporado) guia o Maestro na definição da `id`, `description`, `persona`, `tools`, e `execution_task` do novo agente.
3.  **Geração dos Artefatos:** Ao final, o `AgentCreator_Agent` usa suas ferramentas (`write_file`, `mkdir`) para gerar a estrutura de pastas e os arquivos do novo agente.