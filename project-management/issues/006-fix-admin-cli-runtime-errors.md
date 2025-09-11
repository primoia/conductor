# Plano 006: Tornar o AdminCLI Funcional para Interação Básica

## 1. Meta

Resolver os erros de execução restantes no `AdminCLI` para permitir que um usuário inicie uma sessão, execute uma tarefa simples (como um "olá") e use comandos básicos do REPL (como `clear`) sem encontrar erros.

## 2. Problemas Conhecidos

## 3. Contexto Adicional para o Executor

Para garantir que a solução esteja alinhada com a arquitetura de artefatos do agente (definida na SAGA-16 e detalhada em `AGENT_ARTIFACTS_REFERENCE.md`), o executor deve entender o propósito de cada arquivo dentro do diretório de um agente (`.conductor_workspace/agents/<agent_id>/`):

-   **`definition.yaml`**: A identidade estática do agente (nome, versão, descrição, capacidades, ferramentas permitidas). É o blueprint.
-   **`persona.md`**: O guia de comportamento para o LLM (instruções, diretivas).
-   **`session.json`**: O estado volátil da tarefa atual do agente (ex: `last_task_id`, `conversation_count`, `agent_home_path`). Não armazena histórico de conversa completo.
-   **`knowledge.json`**: A memória semântica do agente (o que ele sabe sobre os artefatos que gerencia ou sobre suas próprias ações passadas). Armazena metadados estruturados sobre execuções de tarefas ou informações do domínio.
-   **`playbook.yaml`**: O manual de conhecimento prescritivo (regras, melhores práticas, anti-padrões).
-   **`history.log`**: A memória episódica do agente (log imutável de todas as tarefas executadas, em formato JSON Lines).

**Anti-Padrão a Ser Evitado:**

O `AdminCLI` ainda exibe `Target: _common/agents/` durante a inicialização. Isso é um resquício de lógica legada. O `AdminCLI` não deve ter nenhum conhecimento sobre caminhos de agentes; ele deve apenas passar o `agent_id` para o `ConductorService` e confiar que o serviço o encontrará no local correto (`.conductor_workspace`).

## 4. Resultado Esperado

Após a refatoração da persistência, a execução do `AdminCLI` revelou dois novos erros de tempo de execução:

1.  **`Erro na execução da tarefa: agent_home_path não encontrado na sessão do agente`**: O `ConductorService` depende de uma chave `agent_home_path` nos dados da sessão para localizar os artefatos de um agente. Os agentes existentes, migrados de uma estrutura antiga, podem não ter essa chave em seu arquivo `session.json` inicial.
2.  **`Erro na sessão REPL: 'AdminCLI' object has no attribute 'clear_conversation_history'`**: O comando `clear` do REPL falha porque o método `clear_conversation_history` não foi implementado na classe `AdminCLI` em `src/cli/admin.py` durante a refatoração.

## 3. Resultado Esperado

O executor tem autonomia para investigar e implementar as melhores soluções para os problemas descritos. O resultado final deve atender aos seguintes critérios:

1.  **Resolução do `agent_home_path`:** O sistema deve se tornar robusto à ausência inicial do `agent_home_path`. A solução pode envolver:
    *   Um script de migração de dados para adicionar o caminho aos agentes existentes.
    *   Tornar o `ConductorService` mais inteligente, talvez construindo o caminho dinamicamente se ele não for encontrado na sessão.
    *   Ou outra solução que o executor julgue mais apropriada.
2.  **Implementação do Comando `clear`:** O método `clear_conversation_history` deve ser adicionado à classe `AdminCLI`. Este método deve delegar a limpeza do histórico para o `ConductorService`, que por sua vez usará o `IStateRepository` para limpar o `history.log` ou o `session.json` do agente, conforme a lógica de negócio.

## 4. Regras e Restrições (Guardrails)

Para garantir a coesão arquitetônica, a solução deve seguir estritamente as seguintes regras:

-   **PROIBIDO O USO DE `_common`:** Toda a lógica deve operar exclusivamente dentro do workspace configurado (`.conductor_workspace`). Nenhuma referência ao diretório legado `projects/_common` deve ser usada no código.
-   **NOME DE ARQUIVO `definition.yaml`:** A nomenclatura de arquivos deve seguir estritamente a SAGA-16. O arquivo de definição é `definition.yaml`. O código não deve, em hipótese alguma, procurar por `agent.yaml`.
-   **SEM LÓGICA LEGADA:** A solução não deve reativar ou depender de nenhuma lógica das classes que foram removidas ou depreciadas.

## 5. Critério de Aceitação Final

- Um usuário pode iniciar o `AdminCLI` (`python -m src.cli.admin --meta --agent AgentCreator_Agent --repl`).
- Digitar um comando de chat (ex: "olá") resulta em uma resposta bem-sucedida do agente, sem o erro `agent_home_path`.
- Digitar o comando `clear` no REPL executa com sucesso, sem erros.
