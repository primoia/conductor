### Plano de Execução: Estágio 8 - Criação do `AgentExecutor`

#### Contexto Arquitetônico

O `AgentLogic` legado era "stateful", projetado para ser instanciado e "incorporar" um agente por toda a vida útil de uma sessão de CLI. Em nossa nova arquitetura orientada a serviços e preparada para escalar, precisamos de um componente de execução que seja "stateless". Esta tarefa consiste em criar o `AgentExecutor`, uma nova classe cuja responsabilidade é executar uma única tarefa de agente de ponta a ponta, recebendo todo o contexto necessário para isso, sem depender de um estado interno.

#### Propósito Estratégico

O objetivo é criar um "worker" de execução de agente que seja limpo, reutilizável e, crucialmente, escalável. Por ser stateless, podemos instanciar um `AgentExecutor` para cada chamada de `execute_task` no `ConductorService` sem efeitos colaterais. Este design é o que permitirá, no futuro, que cada tarefa seja executada em um processo, contêiner ou thread separado, formando a base do nosso plano de dados (Data Plane) na arquitetura Maestro-Executor.

#### Checklist de Execução

- [x] Criar um novo arquivo `src/core/agent_executor.py`.
- [x] Definir a classe `AgentExecutor`.
- [x] O `__init__` deve receber as dependências necessárias para a execução: o cliente LLM, a definição do agente, a lista de ferramentas permitidas, etc.
- [x] Criar um método público `run(task: TaskDTO) -> TaskResultDTO`.
- [x] Este método conterá a lógica principal: construir o prompt, invocar o cliente LLM e empacotar a resposta em um `TaskResultDTO`.
- [x] Diferente do `AgentLogic`, ele não deve manter um estado de "incorporação" (`self.embodied`). Cada chamada a `run` é uma operação atômica e independente.
