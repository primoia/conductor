### Plano de Execução: Estágio 41 - Definição das Capabilities do Executor Agent

#### Contexto Arquitetônico

Estamos na Fase VII da SAGA-017, completando a definição da arquitetura Maestro-Executor. O Executor Agent, criado no estágio anterior, agora precisa ter suas capabilities específicas definidas. Estas capabilities devem focar em escrita de código e execução de comandos shell seguros, conforme especificado no SAGA-017-EXECUTION-PLAN.md. O Executor Agent atua como o componente de execução de baixo nível que recebe tarefas específicas do Maestro Agent e as executa de forma isolada e controlada.

#### Propósito Estratégico

O propósito desta tarefa é definir formalmente as capabilities do Executor Agent como um agente de execução especializado. Estas capabilities devem permitir que o Executor execute código, comandos shell e manipule arquivos de forma segura, sempre sob a coordenação do Maestro Agent. Esta definição completa a arquitetura de três camadas, estabelecendo claramente as responsabilidades de cada componente e garantindo que o Executor tenha as ferramentas necessárias para cumprir seu papel de execução segura e controlada.

#### Checklist de Execução

- [x] Navegar até o diretório do Executor Agent criado no estágio anterior.
- [x] Localizar o arquivo `definition.yaml` do Executor Agent.
- [x] Definir a seção `capabilities` com foco em execução de código e comandos shell.
- [x] Especificar as ferramentas (`allowed_tools`) que implementam essas capabilities.
- [x] Incluir capabilities para execução segura e validação de entradas.
- [x] Documentar cada capability com descrição clara de seu propósito e uso.
- [x] Garantir que as capabilities estejam alinhadas com o papel de execução do agente.
