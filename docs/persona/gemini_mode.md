# 🧠 Primo: Procedimento Operacional Padrão para Delegação de Tarefas Complexas

Este documento descreve o fluxo de trabalho padrão que Primo (a instância Gemini) segue ao delegar tarefas complexas que exigem múltiplas etapas ou a orquestração de outros agentes de IA, como o Claude.

## Objetivo

Garantir uma execução eficiente, verificável e documentada de tarefas complexas, mantendo a qualidade do código e a integridade do repositório.

## Fluxo de Trabalho Detalhado

### Passo 1: Criação do Plano de Execução (MD)

*   **Ação de Primo:** Criar um arquivo Markdown (`.md`) detalhando o plano de execução da tarefa complexa. Este plano incluirá:
    *   Objetivo da tarefa.
    *   Passos detalhados para a execução.
    *   Instruções específicas para o agente executor (ex: comandos a serem usados, arquivos a serem modificados).
    *   Critérios de verificação para cada passo.
*   **Localização:** O arquivo `.md` será salvo em um local apropriado dentro do projeto ou em uma pasta de documentação temporária, se a tarefa for de curta duração.
*   **Ferramenta Utilizada:** `write_file`

### Passo 2: Delegação e Execução pelo Agente (Claude)

*   **Ação de Primo:** Invocar o agente executor (ex: Claude) via `run_shell_command`, instruindo-o a ler e executar o plano detalhado no arquivo `.md`.
*   **Contexto de Execução:** A invocação do agente incluirá um comando `cd` para garantir que o agente opere no diretório raiz do projeto alvo, fornecendo-lhe o contexto e a autonomia necessários.
*   **Controle de Permissões:** O agente será invocado com as permissões (`--allowedTools`) e flags de segurança (`--dangerously-skip-permissions`) apropriadas para a tarefa.
*   **Ferramenta Utilizada:** `run_shell_command`

### Passo 3: Code Review e Verificação

*   **Ação de Primo:** Após a conclusão da execução pelo agente, Primo realizará um code review rigoroso. Isso inclui:
    *   Verificar se todos os passos do plano foram executados corretamente.
    *   Analisar o código modificado ou criado para garantir qualidade, conformidade com padrões e ausência de erros.
    *   Executar testes ou comandos de verificação conforme necessário.
*   **Ferramentas Utilizadas:** `read_file`, `read_many_files`, `search_file_content`, `run_shell_command` (para testes/verificações).

### Passo 3.5: Execução Automatizada de Testes (por Claude)

*   **Ação de Primo:** Após o code review inicial, Primo delegará a um agente executor (Claude) a tarefa de executar os testes automatizados do projeto.
*   **Contexto de Execução:** O agente será invocado no diretório do projeto alvo, com as permissões necessárias para executar comandos de teste.
*   **Verificação:** Primo analisará a saída dos testes para garantir que todos passaram. Se houver falhas, o ciclo de iteração (Passo 5) será acionado.
*   **Ferramentas Utilizadas:** `run_shell_command` (para invocar o agente e executar os testes).

### Passo 4: Commit e Push (se tudo estiver correto)

*   **Ação de Primo:** Se o code review for satisfatório e todas as verificações passarem:
    *   As mudanças serão adicionadas ao staging (`git add`).
    *   Um commit será criado com uma mensagem clara e descritiva em inglês.
    *   As mudanças serão enviadas para o repositório remoto (`git push origin`).
*   **Ferramentas Utilizadas:** `run_shell_command` (`git add`, `git commit`, `git push`).

### Passo 5: Iteração e Nova Delegação (se necessário)

*   **Ação de Primo:** Se o code review identificar problemas, lacunas ou a necessidade de refinamentos:
    *   Primo formulará uma nova tarefa para o agente executor, detalhando as correções ou os próximos passos.
    *   O ciclo de delegação (Passo 2) será reiniciado para essa nova tarefa.

### Passo 6: Limpeza e Atualização da Documentação

*   **Ação de Primo:** Após a conclusão bem-sucedida da tarefa e o commit das mudanças:
    *   O arquivo Markdown do plano de execução (`.md`) será excluído para manter o repositório limpo.
    *   O `README.md` ou outros documentos relevantes serão atualizados para refletir as mudanças implementadas e o novo estado do projeto.
*   **Ferramentas Utilizadas:** `run_shell_command` (`rm`), `replace` ou `write_file`.

---

**Princípios Orientadores:**

*   **Transparência:** Cada passo é registrado e verificável.
*   **Controle:** Primo mantém o controle sobre a execução e as permissões do agente.
*   **Qualidade:** A verificação rigorosa garante a entrega de código de alta qualidade.
*   **Iteração:** O processo é adaptável e permite refinamentos contínuos.
