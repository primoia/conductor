### Plano de Execução: Estágio 36 - Definir os DTOs da API

#### Contexto Arquitetônico

Enquanto nos preparamos para a futura arquitetura escalável, que inclui um ponto de entrada de API, é crucial definir os "contratos de dados" que essa API usará. Esta tarefa consiste em definir os Data Transfer Objects (DTOs) para as requisições e respostas da API, como `ExecuteTaskRequest` e `TaskStatusResponse`. Embora a API em si não seja implementada nesta saga, definir seus DTOs agora estabelece um contrato claro.

#### Propósito Estratégico

O objetivo é projetar a API "de fora para dentro". Ao definir os DTOs primeiro, nós estabelecemos uma fronteira clara e estável para o nosso sistema. Isso permite que futuras equipes de frontend ou outros serviços comecem a desenvolver contra um contrato bem definido, mesmo antes da lógica da API estar pronta. Usar Pydantic para isso também nos dá validação de dados automática e documentação (via OpenAPI) "de graça" quando implementarmos o framework da API (como FastAPI).

#### Checklist de Execução

- [x] Abrir o arquivo `src/core/domain.py`.
- [x] Definir uma nova classe Pydantic (ou `@dataclass`) chamada `ExecuteTaskRequest`.
- [x] Ela deve conter os campos que um cliente externo precisaria para iniciar uma tarefa (ex: `agent_id: str`, `user_input: str`).
- [x] Definir uma nova classe Pydantic chamada `TaskStatusResponse`.
- [x] Ela deve conter os campos para que um cliente possa consultar o status de uma tarefa (ex: `task_id: str`, `status: str`, `output: Optional[str]`).
- [x] Adicionar validações (se necessário) e documentação clara (docstrings) para cada campo e classe.
