### Plano de Execução: Estágio 7 - Definir o Contrato de Dados da Tarefa

#### Contexto Arquitetônico

O `ConductorService` tem um método central, `execute_task`, que atua como o principal ponto de entrada para a execução de agentes. Para evitar passar múltiplos parâmetros e para criar um contrato de dados claro, precisamos de uma estrutura que encapsule todas as informações necessárias para executar uma tarefa. Esta tarefa consiste em definir os Data Transfer Objects (DTOs) para a tarefa em si (`TaskDTO`) e para o seu resultado (`TaskResultDTO`).

#### Propósito Estratégico

O objetivo é criar um "pacote de trabalho" padronizado e fortemente tipado. Ao usar DTOs, nós estabelecemos uma API interna clara e estável. Isso torna o código mais legível e refatorável. Mais importante, esses mesmos DTOs formarão a base para a futura camada de API REST ou para as mensagens em uma fila (SQS), garantindo consistência desde o núcleo da aplicação até suas fronteiras externas.

#### Checklist de Execução

- [x] Navegar até o arquivo `src/core/domain.py`.
- [x] Definir uma nova `@dataclass` chamada `TaskDTO`.
- [x] A `TaskDTO` deve conter campos essenciais como `agent_id: str`, `user_input: str`, e opcionalmente `context: Dict`.
- [x] Definir uma nova `@dataclass` chamada `TaskResultDTO`.
- [x] A `TaskResultDTO` deve conter campos como `status: str` (ex: 'success', 'error'), `output: str`, e opcionalmente `metadata: Dict`.
- [x] Garantir que todas as novas classes e campos tenham type hints explícitos.
