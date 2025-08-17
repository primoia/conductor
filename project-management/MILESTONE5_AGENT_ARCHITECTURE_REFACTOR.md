### **Plano de Engenharia: Arquitetura de Agentes Orientada a Ambientes**

**Versão:** 2.1
**Autor:** Gemini (Staff Engineer)
**Status:** Proposta Final Revisada
**Data:** 16 de agosto de 2025

#### **1. Resumo Executivo**

Este documento detalha um plano de refatoração arquitetural para o Framework Maestro & Conductor. O objetivo é evoluir o sistema para resolver um desafio fundamental: permitir que agentes de IA operem de forma segura e eficaz em bases de código externas, que residem em árvores de diretórios separadas do próprio agente.

A arquitetura atual, embora funcional, apresenta um conflito de "duplo contexto" que gera complexidade e riscos de segurança, especialmente em um cenário com múltiplos projetos e ambientes (desenvolvimento, produção). A solução proposta transformará o framework em um sistema profissional, elegante e seguro, introduzindo os conceitos de **Agentes Residentes em Projeto**, **Gestão de Ambientes** e **Escopo de Escrita Declarativo**.

Esta refatoração simplificará drasticamente a experiência do usuário, aumentará a segurança e fornecerá uma base sólida para a escalabilidade futura do framework.

#### **2. Problemática Atual e Justificativa Técnica**

A necessidade desta evolução surge de três desafios interligados:

1.  **O Conflito do Duplo Contexto:** Um agente precisa ler seu próprio contexto (`persona.md`) e ler/escrever seu estado (`state.json`) em seu diretório "lar", ao mesmo tempo que precisa ler/escrever no código-fonte do projeto alvo, que está em um caminho completamente diferente.
2.  **Risco de Ambiguidade de Ambientes:** O framework não possui um conceito formal de ambientes. Um agente destinado a operar em um microserviço no ambiente de `desenvolvimento` poderia, por um erro de configuração, ser apontado para o mesmo serviço em `produção`, com consequências catastróficas.
3.  **Complexidade na Linha de Comando:** Para contornar os problemas acima, a invocação de um agente requer uma série de parâmetros (`--project-root`, `--output-scope`), tornando a experiência do usuário verbosa, propensa a erros e pouco elegante.

A arquitetura atual não resolve estes problemas de forma sistêmica. A solução proposta o fará, baseada nos seguintes princípios de design: segurança, elegância, convenção sobre configuração e isolamento.

#### **3. A Arquitetura Proposta: Detalhes da Implementação**

A nova arquitetura se baseia em um modelo de **Agente Residente** (cujo diretório de trabalho é o projeto alvo), com mecanismos robustos para gerenciar estado e segurança.

##### **3.1. Estrutura de Diretórios e Gestão de Workspaces**

Para garantir o isolamento entre ambientes, a estrutura de diretórios dos agentes será redefinida para espelhar uma hierarquia lógica.

-   **Nova Estrutura de Agentes:** O caminho para um agente será `conductor/projects/<environment>/<project_name>/agents/<agent_id>/`.
    -   **Exemplo:** `conductor/projects/develop/nex-web-backend/agents/KotlinControllerAgent/`
-   **Arquivo de Configuração de Workspaces:** Para mapear os ambientes lógicos para os caminhos físicos na máquina do desenvolvedor, será criado um arquivo de configuração central.
    -   **Local:** `conductor/config/workspaces.yaml`
    -   **Conteúdo Exemplo:**
        ```yaml
        # Mapeia nomes de ambientes para seus diretórios raiz no sistema de arquivos.
        # É o único arquivo que um novo dev precisa configurar.
        workspaces:
          develop: /mnt/ramdisk/develop
          main: /mnt/ramdisk/main
          primoia-main: /mnt/ramdisk/primoia-main
        ```

##### **3.2. O Manifesto do Agente Evoluído (`agent.yaml`)**

Para eliminar parâmetros da linha de comando, a configuração de alvo e segurança será movida para dentro do `agent.yaml`, tornando o agente "autoconsciente".

-   **Nova Seção `target_context`:**
    ```yaml
    id: KotlinControllerAgent
    description: "Cria e modifica arquivos de Controller para a aplicação nex-web-backend."
    version: 2.0 # Versão incrementada para refletir a nova arquitetura
    execution_mode: project_resident # Modo padrão para agentes de codificação

    target_context:
      # Chave que referencia o nome do projeto no workspaces.yaml
      project_key: "nex-web-backend"
      
      # Política de segurança de escrita: declarativa e versionável.
      output_scope: "src/main/kotlin/br/com/nextar/controller/*Controller.kt"
    ```

##### **3.3. O Orquestrador Inteligente (`genesis_agent.py`)**

O orquestrador será o cérebro da operação, usando as novas configurações para criar uma experiência de usuário simples e segura.

-   **Comando Simplificado:** A invocação de um agente será reduzida a:
    ```bash
    python scripts/genesis_agent.py --environment develop --project nex-web-backend --agent KotlinControllerAgent
    ```
-   **Lógica de Inicialização do Orquestrador:**
    1.  Recebe os argumentos `environment`, `project`, `agent`.
    2.  **Resolve o "Lar" do Agente:** Constrói o caminho `conductor/projects/develop/nex-web-backend/agents/KotlinControllerAgent/`.
    3.  **Resolve o "Workspace" do Projeto Alvo:** Carrega `conductor/config/workspaces.yaml`, encontra a chave `develop` e obtém o caminho base `/mnt/ramdisk/develop`. Junta com o nome do projeto para obter o caminho final do projeto alvo.
    4.  **Muda o Diretório de Trabalho:** Executa `os.chdir()` para o caminho do projeto alvo. O agente agora "vive" no projeto que irá modificar.
    5.  **Carrega o Manifesto:** Lê o `agent.yaml` do "lar" do agente para obter o `output_scope` e outras configurações.
-   **Gestão de Estado Explícita:**
    -   O orquestrador mantém o caminho absoluto para o `state.json` do agente em memória.
    -   Após cada turno da conversa, ele salva o estado da sessão escrevendo diretamente no caminho absoluto, garantindo que o `state.json` seja sempre salvo no lugar certo, independentemente do CWD do processo.
-   **Aplicação do Escopo de Escrita:**
    -   A ferramenta `Write` será interceptada. Antes de executar, ela validará o caminho do arquivo solicitado contra o padrão `glob` do `output_scope` carregado do `agent.yaml`.
    -   Se a validação falhar, a operação é bloqueada. Se passar, o fluxo de confirmação do usuário (`diff/patch`) é acionado.

##### **3.4. A Fábrica de Agentes Aprimorada (`AgentCreator_Agent`)**

A complexidade de configuração se move para a criação do agente, que é o lugar certo. O `AgentCreator_Agent` será atualizado para gerenciar isso.

-   **Novo Fluxo de Diálogo:** O `AgentCreator` irá incluir novas perguntas em seu diálogo de criação:
    1.  "Em qual **ambiente** este agente irá operar? (develop, main, etc.)"
    2.  "Qual o **nome do projeto** alvo?"
    3.  "Este agente irá modificar código? Se sim, por favor, forneça o **padrão glob para o escopo de escrita** (output_scope)."
-   Com estas respostas, ele irá gerar a nova estrutura de diretórios e o `agent.yaml` com a seção `target_context` preenchida corretamente.

##### **3.5. Estratégia de Testes (Revisada e Expandida)**

Para garantir a robustez e a corretude da nova arquitetura, a implementação **deve** seguir uma abordagem de **Test-Driven Development (TDD)**. Nenhum código de orquestração ou segurança deve ser escrito antes que um teste correspondente que falhe seja criado.

**Cenários de Teste Detalhados:**

1.  **Teste Unitário (`test_orchestrator_resolution.py`):**
    -   Testar a função de resolução de caminhos do orquestrador.
    -   Deve validar que, dados um `environment` e `project`, ele consegue montar corretamente o `agent_home_path` e o `project_root_path` usando um `workspaces.yaml` de mock.

2.  **Teste de Integração (`test_scoped_write_session.py`):**
    -   Este teste é crítico e deve simular uma sessão interativa completa.
    -   **Setup:** Iniciar uma sessão com um agente de teste com `--output-scope "src/service/*.kt"`.
    -   **Cenário 1 (Leitura Livre):** O agente tenta ler `src/controller/MyController.kt`. **Assert:** A operação deve ser bem-sucedida.
    -   **Cenário 2 (Escrita Fora do Escopo):** O agente tenta escrever em `src/controller/MyController.kt`. **Assert:** A operação deve falhar com uma mensagem de erro clara sobre violação de escopo.
    -   **Cenário 3 (Escrita Dentro do Escopo):** O agente tenta escrever em `src/service/MyService.kt`. **Assert:** O orquestrador deve apresentar um prompt de confirmação ao usuário.
    -   **Cenário 4 (Confirmação e Verificação):** Simular a aprovação do usuário. **Assert:** O arquivo `src/service/MyService.kt` no projeto alvo deve ter seu conteúdo alterado.
    -   **Cenário 5 (Integridade do Estado):** Ao final da sessão. **Assert:** O arquivo `state.json` no diretório original do agente deve ser atualizado corretamente.

3.  **Teste End-to-End (`test_agent_creator_flow.py`):**
    -   Executar o `AgentCreator_Agent` com um script de input.
    -   **Assert:** Verificar se a estrutura de diretórios `projects/<env>/<proj>/agents/<id>` foi criada e se o `agent.yaml` gerado contém a seção `target_context` com os valores corretos.

##### **3.7. Plano de Migração para Agentes Existentes**

Para garantir uma transição suave, os agentes legados (v1.x) devem ser migrados para a nova estrutura (v2.0). Este processo será semi-automatizado para minimizar o trabalho manual.

-   **Ferramenta de Migração:** Será criado um novo script: `scripts/migrate_agents_v2.py`.
-   **Lógica do Script:**
    1.  O script irá varrer a estrutura de diretórios antiga (ex: `projects/develop/agents/`).
    2.  Para cada agente encontrado, ele iniciará um prompt interativo para coletar as novas informações necessárias:
        -   `Qual o ambiente de destino para este agente? [padrão: develop]`
        -   `Qual a chave de projeto (project_key) associada?`
        -   `Qual o escopo de escrita (output_scope) para este agente?`
    3.  Com as informações, o script irá automaticamente:
        a. Criar a nova estrutura de diretórios: `projects/<env>/<proj>/agents/<id>/`.
        b. Mover os arquivos existentes (`persona.md`, `state.json`, etc.) para o novo local.
        c. Ler o `agent.yaml` antigo, adicionar a seção `target_context` com os dados coletados, e incrementar o campo `version` para `2.0`.
        d. Salvar o novo `agent.yaml` no diretório de destino.
-   **Benefício:** Este processo garante que todos os agentes sejam atualizados para a nova arquitetura de forma consistente e com o mínimo de esforço, mantendo a integridade de seus dados.

##### **3.8. Implicações para Modos de Execução (Detalhado)**

A distinção entre os executores e seus modos é fundamental para o executor do plano entender.

-   **`genesis_agent.py` (O Ateliê):** Este executor é sempre focado na interação com **um único agente**. Ele possui dois sub-modos:
    -   **Modo Conversacional (`--repl`):** Para sessões de chat interativas, de múltiplos turnos. Ideal para design, depuração e desenvolvimento supervisionado.
    -   **Modo Comando Único (sem `--repl`):** Para execuções "one-shot", não-interativas. Recebe um input, executa um único turno com o agente, imprime o resultado e encerra. Ideal para scripting e consultas rápidas.

-   **`run_conductor.py` (A Fábrica):** Este executor nunca é interativo. Seu único propósito é ler um arquivo de workflow (`.yaml`) e orquestrar uma **sequência de múltiplas tarefas**, que podem envolver múltiplos agentes. É o motor para automação e CI/CD.

**Tabela Comparativa para o Executor:**

| Característica | `genesis_agent.py --repl` | `genesis_agent.py` (sem `--repl`) | `run_conductor.py` |
| :--- | :--- | :--- | :--- |
| **Tipo de Interação** | Conversa Contínua | Comando Único (One-Shot) | Workflow Completo |
| **Escopo** | 1 Agente, N turnos | 1 Agente, 1 turno | N Agentes, N tarefas |
| **Input** | Comandos do usuário (stdin) | Argumento de input (`--input`) | Arquivo de plano (`.yaml`) |
| **Caso de Uso** | Debug, Design, Análise | Scripting, Consultas Rápidas | Automação, CI/CD |

##### **4. Plano de Execução Faseado**

1.  **Fase 1 - Fundação (Baixo Risco):**
    -   Implementar a nova estrutura de diretórios.
    -   Criar o `workspaces.yaml` e a lógica de leitura no orquestrador.
    -   Implementar a lógica de resolução de caminhos e o `os.chdir()`.
    -   Implementar a gestão de estado explícita para o `state.json`.
    -   *Meta:* Ao final desta fase, um agente já pode operar no diretório alvo, mas ainda sem a segurança de escrita.
2.  **Fase 2 - Implementação da Segurança e Funcionalidade Principal (Médio Risco):**
    -   Adicionar o campo `target_context` ao `agent.yaml`.
    -   Implementar a lógica de `output_scope` na ferramenta `Write`.
    -   Definir o comportamento para os modos de execução (`--repl` vs. automatizado) e as políticas de escrita.
    -   Criar os testes de integração (`test_scoped_write_session.py`).
    -   *Meta:* A arquitetura principal está completa e segura.
3.  **Fase 3 - Ferramentas e Testes (Alto Valor):**
    -   Atualizar o `AgentCreator_Agent` com o novo fluxo de diálogo.
    -   Criar o script de migração (`scripts/migrate_agents_v2.py`).
    -   Criar os testes restantes.
    -   *Meta:* O projeto está pronto para ser usado por outros desenvolvedores com a nova arquitetura.

#### **5. Conclusão**

Este plano de engenharia aborda de forma abrangente os desafios atuais do framework. Ao adotar o modelo de **Agente Residente com Escopo de Escrita, Orientado a Ambientes**, o sistema se tornará drasticamente mais simples de usar, mais seguro em sua operação e mais escalável para um futuro com dezenas de projetos e ambientes. A execução deste plano elevará o Framework Maestro & Conductor a um novo patamar de profissionalismo e capacidade técnica.

#### **6. Análise de Riscos e Mitigações (Novo)**

Uma refatoração desta magnitude introduz riscos que devem ser gerenciados.

1.  **Risco: Complexidade da Implementação.**
    -   **Descrição:** A lógica do orquestrador para gerenciar caminhos, estado e segurança é complexa e pode conter bugs.
    -   **Mitigação:** Aderência estrita ao TDD (Seção 3.5). A implementação faseada (Seção 4) garante que as fundações sejam testadas antes de construir sobre elas.

2.  **Risco: Segurança.**
    -   **Descrição:** O modo `project_resident` é inerentemente mais arriscado. Bugs na validação de `output_scope` ou na interceptação da ferramenta `Write` podem levar a modificações de arquivo indesejadas.
    -   **Mitigação:** O `output_scope` é a principal mitigação. A confirmação humana obrigatória no modo `--repl` é uma salvaguarda crítica. No modo automatizado, a política padrão `on_write: fail` garante segurança por padrão.

3.  **Risco: Migração de Agentes.**
    -   **Descrição:** O script de migração pode falhar no meio do processo, deixando os agentes em um estado inconsistente.
    -   **Mitigação:** O script `migrate_agents_v2.py` deve ser construído com robustez, incluindo a criação de backups dos diretórios dos agentes originais antes de qualquer modificação e um modo "dry-run" para simular a migração sem fazer alterações.

4.  **Risco: Performance.**
    -   **Descrição:** A nova lógica de I/O para gestão de estado pode introduzir latência.
    -   **Mitigação:** Baixo risco, pois se trata de uma única escrita de arquivo por turno. Estratégias de cache podem ser consideradas no futuro, se necessário.