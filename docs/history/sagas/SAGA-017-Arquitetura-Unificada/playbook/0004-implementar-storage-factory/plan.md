### Plano de Execução: Estágio 4 - Implementação da `StorageFactory`

#### Contexto Arquitetônico

Temos o `ConductorService` que sabe ler a configuração e a interface `IStateRepository` que define o contrato de persistência. Agora, precisamos de uma ponte entre os dois. Esta tarefa consiste em criar uma `StorageFactory`, um componente interno do `ConductorService` cuja única responsabilidade é inspecionar a configuração de `storage` e instanciar a implementação correta do `IStateRepository`.

#### Propósito Estratégico

O objetivo é centralizar a lógica de seleção de backend em um único lugar, aderindo ao padrão de design Factory. Isso mantém o resto do `ConductorService` limpo e agnóstico em relação às implementações concretas de repositório. O serviço principal não precisará conter uma série de `if/else` para decidir qual repositório usar; ele simplesmente pedirá à fábrica para "me dê o repositório configurado". Isso torna a adição de novos backends no futuro trivial: basta registrar a nova classe na fábrica.

#### Checklist de Execução

- [x] Modificar o `ConductorService` em `src/core/conductor_service.py`.
- [x] Criar um método privado `_create_storage_backend(self, storage_config: StorageConfig) -> IStateRepository`.
- [x] Dentro deste método, implementar a lógica que retorna uma instância de `FileSystemStateRepository` se `storage_config.type == 'filesystem'` e `MongoStateRepository` se for `'mongodb'`.
- [x] Garantir que uma `ConfigurationError` seja lançada se o tipo for desconhecido.
- [x] Chamar este método no `__init__` e armazenar a instância do repositório em um atributo (ex: `self.repository`).
- [x] Serão necessárias importações das futuras classes concretas de repositório, que podem ser criadas com um `pass` básico por enquanto.
