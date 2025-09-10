### Plano de Execução: Estágio 3 - Definir a Interface do Repositório de Estado

#### Contexto Arquitetônico

Seguindo o Princípio da Inversão de Dependência, o `ConductorService` não deve depender de uma implementação concreta de persistência (seja filesystem ou MongoDB). Ele deve depender de uma abstração. Esta tarefa consiste em definir o "contrato" para qualquer repositório de estado. A interface `IStateRepository` formalizará as operações que o núcleo da aplicação pode realizar (carregar, salvar estado), independentemente da tecnologia de armazenamento subjacente.

#### Propósito Estratégico

O objetivo é criar um ponto de extensibilidade claro para a camada de persistência. Ao definir esta interface em `src/ports/`, nós desacoplamos completamente a lógica de negócios da lógica de acesso a dados. Isso permite que a equipe (ou a comunidade) adicione novos backends de armazenamento no futuro (como PostgreSQL ou um S3 bucket) simplesmente criando uma nova classe que implementa esta interface, sem a necessidade de modificar uma única linha de código no `ConductorService`.

#### Checklist de Execução

- [ ] Navegar até o diretório `src/ports/`.
- [ ] Criar um novo arquivo chamado `state_repository.py`.
- [ ] No arquivo, importar `ABC`, `abstractmethod`, e tipos relevantes de `typing`.
- [ ] Definir a classe `IStateRepository(ABC)`.
- [ ] Adicionar as assinaturas de métodos abstratos essenciais, como `save_state(agent_id: str, state_data: Dict) -> bool` e `load_state(agent_id: str) -> Dict`.
- [ ] Adicionar um método abstrato para a descoberta de agentes, como `list_agents() -> List[str]`, que será crucial para o `ConductorService`.
- [ ] Adicionar docstrings claros a cada método.
