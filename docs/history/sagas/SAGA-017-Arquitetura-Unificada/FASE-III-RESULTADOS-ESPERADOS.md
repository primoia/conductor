# SAGA-017: Resultados Esperados da Fase III - A Cirurgia

## 1. Visão Geral do Resultado

Ao concluir a **Fase III: A Cirurgia - O Transplante do Núcleo**, teremos alcançado o objetivo central da SAGA-017. Teremos migrado com sucesso os pontos de entrada legados (`admin.py`, `agent.py`) para operar inteiramente sobre o novo `ConductorService`. A "casa antiga" foi efetivamente movida para a "nova fundação".

O resultado principal é um **sistema internamente unificado**. Embora ainda existam duas interfaces de linha de comando por razões de retrocompatibilidade, ambas agora executam a mesma lógica de negócios centralizada, coesa e alinhada com a SAGA-016. O cisma arquitetônico foi resolvido.

## 2. Artefatos e Capacidades Concretas Entregues

Ao final dos estágios 15 a 18 da Fase III, teremos os seguintes entregáveis concretos:

1.  **Container de DI Atualizado (`container.py`):**
    *   O container de injeção de dependência agora sabe como construir e fornecer uma instância singleton do `ConductorService` para qualquer parte da aplicação que a solicite.

2.  **CLIs Refatorados (`admin.py`, `agent.py`):**
    *   As classes `AdminCLI` e `AgentCLI` foram transformadas em "cascas finas".
    *   Elas não contêm mais nenhuma lógica de descoberta de agentes ou de instanciação de `AgentLogic`.
    *   Sua única responsabilidade é traduzir os argumentos da linha de comando em um `TaskDTO` e delegar a execução para o `ConductorService`.

3.  **Preservação da Experiência do Usuário:**
    *   Os comandos de CLI existentes continuam a funcionar com os mesmos argumentos de antes.
    *   O modo interativo (`--repl`), incluindo seus comandos customizados, permanece totalmente funcional para ambos os CLIs, agora operando sobre o novo serviço.

## 3. O Que Este Resultado Nos Permite Fazer

*   **Operar um Sistema Coeso:** Podemos agora usar os CLIs existentes para interagir com um sistema que respeita o `config.yaml` para seleção de backend de armazenamento e carregamento de plugins de ferramentas. A visão da SAGA-016 agora é a realidade operacional.
*   **Iniciar a Validação de Ponta a Ponta:** Com os CLIs conectados ao novo núcleo, podemos começar a Fase IV, que é escrever testes de integração rigorosos que validam o comportamento do sistema desde a entrada do usuário até a persistência dos dados.
*   **Aposentar a Lógica Legada:** O `AgentLogic` não é mais chamado por nenhum código de produção, abrindo o caminho para sua depreciação e eventual remoção nas fases seguintes.

## 4. O Que **NÃO** Teremos ao Final da Fase III

*   **Código Legado Removido:** O arquivo `src/core/agent_logic.py` ainda existirá, embora não seja mais utilizado. Sua remoção é uma tarefa explícita da fase de consolidação.
*   **Testes Abrangentes:** A Fase III foca na cirurgia em si. A escrita de testes unitários e de integração para a nova arquitetura é o foco principal da Fase IV.

Em resumo, a Fase III completa a unificação funcional do sistema. As fases seguintes focarão em validar, consolidar e construir sobre esta nova e coesa fundação.
