### Plano de Implementação: Conductor - Fase 1A (Invocação Real de Agentes)

**1. Objetivo Principal**

Substituir a execução simulada de agentes (`mock`) no script `run_conductor.py` por um mecanismo de invocação real e dinâmico. O novo sistema deverá ser capaz de orquestrar qualquer tarefa definida em um arquivo `implementation-plan.yaml`, invocando o agente correto com o contexto apropriado.

**2. Princípios de Arquitetura**

*   **Genérico e Orientado pelo Plano:** O código não deve conter nomes de agentes ou tarefas hardcoded. Toda a execução deve ser controlada pelo conteúdo do plano YAML.
*   **Modularidade:** A lógica de invocação do agente será encapsulada na função `_invoke_agent` e suas funções auxiliares. Isso garantirá que o código seja fácil de manter e evoluir (em direção à Opção B, se necessário).
*   **Inspiração em Padrões Existentes:** A lógica de construção de prompt e execução de IA será fortemente baseada no padrão já validado do `focused_claude_orchestrator.py`.

**3. Plano de Execução Detalhado**

#### Passo 1: Refatorar a Assinatura de `_invoke_agent`
-   **Ação:** Modificar a função `_invoke_agent` em `run_conductor.py`.
-   **Detalhes:** A função, que hoje recebe `(self, agent_name, context_file, task)`, será simplificada para receber apenas `(self, task: Dict[str, Any])`. Toda a informação necessária já está no dicionário da tarefa.
-   **Resultado:** Uma função com uma interface mais limpa e pronta para a nova lógica.

#### Passo 2: Implementar o Carregamento Dinâmico do "Cérebro" do Agente
-   **Ação:** Criar uma função auxiliar `_load_agent_brain(self, agent_name: str)`.
-   **Detalhes:**
    -   Esta função receberá o nome do agente (ex: `KotlinEntityCreator_Agent`) extraído de `task['agent']`.
    -   Ela seguirá uma convenção de diretórios para encontrar os arquivos do agente: `projects/develop/agents/{agent_name}/`.
    -   Ela lerá `persona.md` e `memory/context.md` para construir o "cérebro" do agente.
-   **Resultado:** Uma função que pode carregar o contexto de qualquer agente dinamicamente.

#### Passo 3: Construir o Prompt de Forma Dinâmica
-   **Ação:** Criar uma função auxiliar `_build_agent_prompt(self, agent_brain: Dict, task: Dict)`.
-   **Detalhes:**
    -   Esta função irá montar o prompt final para a IA.
    -   Ela combinará o `agent_brain` (Passo 2) com as informações da tarefa do YAML: `description`, `inputs` e `outputs`.
    -   Para os `inputs`, a função lerá o conteúdo dos arquivos especificados para fornecer o contexto do código existente à IA.
-   **Resultado:** Uma função que gera um prompt completo e focado para cada tarefa específica do plano.

#### Passo 4: Executar a Chamada Real à IA
-   **Ação:** Dentro de `_invoke_agent`, usar o módulo `subprocess` do Python para executar a ferramenta de linha de comando da IA (ex: `claude`).
-   **Detalhes:**
    -   A chamada passará o prompt gerado no Passo 3 como argumento.
    -   O `stdout` e `stderr` do processo serão capturados para obter a resposta da IA e tratar possíveis erros.
-   **Resultado:** A simulação (`time.sleep`) é substituída por uma chamada real a um modelo de linguagem.

#### Passo 5: Processar e Salvar a Resposta da IA
-   **Ação:** Implementar a lógica para tratar a saída do `subprocess`.
-   **Detalhes:**
    -   Extrair o bloco de código gerado da resposta da IA.
    -   Salvar o código extraído no(s) arquivo(s) especificado(s) em `task['outputs']`.
    -   A lógica deve criar os diretórios pais (`os.makedirs`) caso eles não existam.
-   **Resultado:** O resultado do trabalho do agente é persistido no sistema de arquivos, concluindo a tarefa.

#### Passo 6: Implementar a Validação da Tarefa
-   **Ação:** Criar uma função `_validate_task(self, task: Dict) -> bool`.
-   **Detalhes:**
    -   Após a execução do agente, `_invoke_agent` chamará esta função.
    -   Inicialmente, a validação será simples: verificar se os arquivos de `outputs` foram criados e não estão vazios.
    -   **Nota:** Este é um ponto de extensão futuro. A validação poderá evoluir para rodar linters, testes ou outras checagens complexas.
-   **Resultado:** Um mecanismo básico de verificação que confirma se o agente produziu um artefato.

**4. Critérios de Conclusão (Definition of Done)**

-   O script `run_conductor.py` executa o plano `example-implementation-plan.yaml` de ponta a ponta com sucesso.
-   A lógica de simulação (mock) em `_invoke_agent` foi completamente removida e substituída pela lógica real.
-   Arquivos são efetivamente criados ou modificados no disco conforme especificado na seção `outputs` das tarefas.
-   O código da refatoração está limpo, comentado e segue os princípios de modularidade definidos.
