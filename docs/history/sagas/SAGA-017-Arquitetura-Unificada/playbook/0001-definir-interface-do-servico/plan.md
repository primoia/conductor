### Plano de Execução: Estágio 1 - Definição do Contrato do Serviço (`IConductorService`)

#### Contexto Arquitetônico

Estamos no marco zero da construção do novo núcleo do Conductor. Antes de escrever uma única linha de lógica de implementação, é imperativo definir o "contrato" formal que governará o comportamento do nosso novo cérebro, o `ConductorService`. A criação de uma interface abstrata em `src/ports/` é um ato arquitetônico deliberado que adota o Princípio da Inversão de Dependência. Isso garante que qualquer componente futuro, incluindo os CLIs refatorados, dependerá desta abstração estável, e não de uma implementação concreta e volátil. Este arquivo será a "Constituição" da nossa nova arquitetura, o documento fundamental a partir do qual toda a lógica de serviços será derivada e validada.

#### Propósito Estratégico

O propósito desta tarefa é criar uma barreira clara entre a definição do "o quê" (o que o serviço deve fazer) e o "como" (como ele o fará). Ao definir a interface `IConductorService`, estabelecemos um contrato público e explícito. Isso nos permite desenvolver componentes em paralelo (por exemplo, a implementação do serviço e os testes que o consomem) e facilita enormemente a testabilidade, permitindo a criação de mocks e stubs baseados em uma interface compartilhada e confiável. Este estágio garante que a nova arquitetura seja modular e coesa desde a sua primeira linha de código.

#### Checklist de Execução

- [x] Navegar até o diretório `src/ports/`.
- [x] Criar um novo arquivo chamado `conductor_service.py`.
- [x] No arquivo, importar `ABC` e `abstractmethod` do módulo `abc`.
- [x] Definir a classe `IConductorService(ABC)`.
- [x] Adicionar as assinaturas de métodos abstratos essenciais, incluindo `discover_agents() -> List['AgentDefinition']`, `execute_task(task: 'TaskDTO') -> 'TaskResultDTO'`, e `load_tools() -> None`.
- [x] Adicionar type hints claros e docstrings a cada método, explicando seu propósito e seus parâmetros.
