## SAGA-013: Consistência e Controle de Ferramentas

**Objetivo:** Garantir que o controle de ferramentas seja consistente e seguro para todos os provedores de IA (Claude, Gemini) e que a configuração via `agent.yaml` seja a fonte de verdade para as permissões de ferramentas.

**Contexto:** A necessidade de permitir que agentes de IA acessem ferramentas do sistema (como `write_file`) de forma controlada, evitando o uso de `--approval-mode yolo` e garantindo que `agent.yaml` defina as permissões de forma granular.

**Passos:**

1.  **Análise e Confirmação da Configuração de Ferramentas:**
    *   **Revisar:** Analisar a estrutura atual de como as ferramentas são definidas em `agent.yaml` (ou configuração similar).
    *   **Confirmar:** Verificar se o método `get_available_tools()` no `genesis_agent` (ou no agente pai) lê essa configuração corretamente e retorna a lista de nomes de ferramentas internas (ex: `write_file`, `read_file`, `run_shell_command`).
    *   **Documentar:** Registrar os nomes exatos das ferramentas internas que o framework `conductor` expõe.

2.  **Implementação do `GeminiCLIClient` para `--allowed-tools`:**
    *   **Modificar:** Editar `src/infrastructure/llm/cli_client.py`.
    *   **Lógica:** Dentro de `GeminiCLIClient.invoke`, adicionar a lógica para chamar `self.genesis_agent.get_available_tools()` e estender o comando `cmd` com `"--allowed-tools"` seguido da lista de ferramentas.
    *   **Formato:** Garantir que o formato da lista de ferramentas seja compatível com o `gemini` CLI (ex: múltiplos argumentos separados por espaço, como `cmd.extend(["--allowed-tools"]); cmd.extend(available_tools)`).
    *   **Diferenciação de Permissões por Tipo de Agente:**
        *   **Agentes de Administração (`admin`):** Para agentes invocados pelo `src/cli/admin.py`, considerar a possibilidade de conceder acesso irrestrito a todas as ferramentas (ex: via `--approval-mode yolo` no Gemini CLI), dada sua natureza de gerenciamento de framework.
        *   **Agentes de Projeto (`agent`):** Manter o controle granular de ferramentas via `agent.yaml` e `--allowed-tools`, conforme planejado, para agentes invocados pelo `src/cli/agent.agent`.

3.  **Teste de Permissões de Ferramentas (Claude):**
    *   **Configurar:** Criar um `agent.yaml` de teste para um agente Claude que permita apenas um subconjunto de ferramentas (ex: `read_file`).
    *   **Verificar Bloqueio:** Tentar fazer o agente Claude usar uma ferramenta não permitida (ex: `write_file`) e verificar se ele é bloqueado.
    *   **Verificar Funcionamento:** Tentar fazer o agente Claude usar uma ferramenta permitida (ex: `read_file`) e verificar se ele funciona corretamente.

4.  **Teste de Permissões de Ferramentas (Gemini):**
    *   **Configurar:** Criar um `agent.yaml` de teste para um agente Gemini que permita apenas um subconjunto de ferramentas (ex: `read_file`).
    *   **Verificar Bloqueio:** Tentar fazer o agente Gemini usar uma ferramenta não permitida (ex: `write_file`) e verificar se ele é bloqueado.
    *   **Verificar Funcionamento:** Tentar fazer o agente Gemini usar uma ferramenta permitida (ex: `read_file`) e verificar se ele funciona corretamente.

5.  **Refinamento e Documentação:**
    *   **Ajustar:** Refinar a implementação e a configuração conforme necessário, com base nos resultados dos testes.
    *   **Atualizar Documentação:** Adicionar ou atualizar a documentação interna sobre como adicionar novas ferramentas ao framework e como gerenciar suas permissões via `agent.yaml` para ambos os provedores de IA.