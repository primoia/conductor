### Plano de Execução: Estágio 39 - Definição das Capabilities do Maestro Agent

#### Contexto Arquitetônico

Estamos na Fase VII da SAGA-017, preparando a arquitetura Maestro-Executor. O Maestro Agent é o componente orquestrador de alto nível que coordena tarefas complexas, divide-as em subtarefas menores e delega-as ao Executor Agent. Este estágio define as capabilities específicas que o Maestro Agent deve possuir para cumprir seu papel na hierarquia de agentes. As capabilities definidas aqui serão implementadas como ferramentas (tools) no arquivo `agent.yaml` do Maestro Agent, estabelecendo sua capacidade de manipular arquivos, gerenciar estado e coordenar execuções.

#### Propósito Estratégico

O propósito desta tarefa é estabelecer formalmente as capabilities do Maestro Agent como um agente de coordenação e planejamento. Estas capabilities devem focar em manipulação de arquivos, gerenciamento de estado e coordenação de tarefas, permitindo que o Maestro atue como um "gerente de projeto" que quebra tarefas complexas em subtarefas executáveis. Esta definição é crucial para a arquitetura de três camadas (Orquestrador -> Maestro -> Executor) e garante que o Maestro tenha as ferramentas necessárias para cumprir seu papel de coordenação.

#### Checklist de Execução

- [x] Navegar até o diretório de agentes do sistema (a ser criado em estágio anterior).
- [x] Localizar o arquivo `definition.yaml` do Maestro Agent.
- [x] Definir a seção `capabilities` com foco em manipulação de arquivos e estado.
- [x] Especificar as ferramentas (`allowed_tools`) que implementam essas capabilities.
- [x] Incluir capabilities para coordenação de tarefas e comunicação com Executor Agent.
- [x] Documentar cada capability com descrição clara de seu propósito e uso.
