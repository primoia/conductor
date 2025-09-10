# SAGA-017: Resultados Esperados da Fase I - A Fundação

## 1. Visão Geral do Resultado

Ao concluir a **Fase I: A Fundação - Forjando o Novo Núcleo de Serviços**, teremos construído com sucesso o **"motor" completo e funcional da nova arquitetura Conductor**. Este motor, no entanto, estará "na bancada" — totalmente testável e operacional em isolamento, mas ainda não instalado no "chassi" do veículo (os CLIs `admin.py` e `agent.py`).

O resultado principal é um **núcleo de serviços desacoplado, robusto e alinhado com a SAGA-016**, que existe inteiramente dentro do diretório `src/core/` e `src/ports/`, sem ter modificado nenhuma das lógicas de UI legadas.

## 2. Artefatos e Capacidades Concretas Entregues

Ao final dos 10 estágios da Fase I, teremos os seguintes entregáveis concretos no código-fonte:

1.  **O Cérebro Central (`ConductorService`):**
    *   Existirá uma classe `ConductorService` em `src/core/conductor_service.py` que implementa a interface `IConductorService`.
    *   Ela será o ponto de entrada único para toda a lógica de negócios da nova arquitetura.

2.  **Contratos Arquitetônicos Claros (`Interfaces`):**
    *   O arquivo `src/ports/conductor_service.py` definirá a interface `IConductorService`.
    *   O arquivo `src/ports/state_repository.py` definirá a interface `IStateRepository`.
    *   Estes contratos estabelecem as fronteiras e as regras da nossa arquitetura limpa.

3.  **Sistema de Configuração Centralizado:**
    *   O `ConductorService` será inicializado lendo e validando um `config.yaml` global através de schemas Pydantic definidos em `src/core/config_schema.py`.

4.  **Persistência Agnóstica e Extensível:**
    *   O serviço conterá uma `StorageFactory` que pode instanciar diferentes backends de armazenamento (`FileSystemStateRepository`, `MongoStateRepository`) com base na configuração, sem que o serviço conheça os detalhes de cada um.

5.  **Sistema de Ferramentas Híbrido e Dinâmico:**
    *   O serviço terá a capacidade de carregar as `Core Tools` e, mais importante, escanear, importar e registrar dinamicamente `Tool Plugins` de diretórios customizados especificados no `config.yaml`.

6.  **Executor de Agentes Moderno (`AgentExecutor`):**
    *   Existirá uma classe `AgentExecutor` em `src/core/agent_executor.py`, projetada para ser **stateless**, recebendo todo o contexto necessário para executar uma tarefa de forma isolada.
    *   Ele estará totalmente integrado com o `PromptEngine` para garantir a engenharia de prompt de alta qualidade do legado.

7.  **Contratos de Dados Padronizados (`DTOs`):**
    *   O arquivo `src/core/domain.py` conterá as definições para `TaskDTO` e `TaskResultDTO`, padronizando como o trabalho é requisitado e como os resultados são retornados através do sistema.

## 3. O Que Este Resultado Nos Permite Fazer

*   **Testar o Núcleo de Forma Isolada:** Poderemos escrever testes unitários e de integração que exercitam o `ConductorService` diretamente, validando toda a nova funcionalidade (descoberta de agentes, carregamento de plugins, execução de tarefas) sem a complexidade da camada de CLI.
*   **Validar a Visão da SAGA-016:** Teremos uma implementação tangível e funcional da arquitetura planejada, provando que o design é sólido e executável.
*   **Iniciar a "Cirurgia" com Confiança:** Com um motor novo, testado e funcionando, teremos uma base sólida e de baixo risco para iniciar a Fase II, que é a refatoração dos CLIs legados para usar este novo serviço.

## 4. O Que **NÃO** Teremos ao Final da Fase I

É crucial entender os limites desta fase para gerenciar as expectativas:

*   **Nenhuma Mudança Visível para o Usuário:** Os comandos `poetry run python src/cli/admin.py` e `poetry run python src/cli/agent.py` continuarão a funcionar **exatamente como antes**, utilizando a lógica antiga do `AgentLogic`. A Fase I não toca nesses arquivos.
*   **O Código Legado Ainda Existe:** O `AgentLogic` ainda estará presente no código-fonte, pois a sua remoção só acontecerá em uma fase posterior, após a migração bem-sucedida dos CLIs.
*   **Sem CLI Unificado:** O novo `conductor.py` ainda não terá sido criado.

Em resumo, a Fase I é puramente sobre **construir a nova fundação** ao lado da casa antiga, sem conectar as duas. A conexão só acontecerá na Fase II.
