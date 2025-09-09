# Plano: 0005-E - Infra: Persistência de Artefatos (MongoDB)

## Contexto

Com a fábrica de repositórios pronta, podemos implementar a estratégia de persistência para o backend `mongodb`. O objetivo é criar uma classe `MongoDbStorage` que implementa a mesma interface implícita que `FileSystemStorage`, permitindo que a fábrica os troque de forma transparente.

A lógica aqui envolverá a conexão com o MongoDB e a tradução das nossas `dataclasses` de domínio para documentos BSON e vice-versa.

## Checklist de Verificação

- [x] Criar um novo arquivo `src/infrastructure/mongodb_storage.py`.
- [x] Adicionar `pymongo` como uma dependência do projeto.
- [x] Em `mongodb_storage.py`, criar a classe `MongoDbStorage`.
- [x] O construtor deve receber a string de conexão e o nome do banco de dados, e inicializar o cliente do MongoDB.
- [x] Implementar o método `load_definition() -> AgentDefinition`, que buscará o documento correspondente na coleção `agents`.
- [x] Implementar o método `save_definition(definition: AgentDefinition)`, que salvará o documento na coleção `agents`.
- [x] Implementar os métodos de `load` e `save` (ou `update`) para `persona`, `playbook` e `knowledge` como campos dentro do documento principal do agente.
- [x] Implementar `append_to_history(entry: HistoryEntry)`, que insere um novo documento na coleção `history`.
- [x] Implementar `load_history() -> List[HistoryEntry]`, que busca todos os documentos de histórico para um agente.
- [x] Implementar `save_session` e `load_session` usando uma coleção `sessions` com um índice TTL para expiração automática.
- [x] Em `src/infrastructure/repository_factory.py`, modificar `get_repository` para retornar uma instância de `MongoDbStorage` quando o tipo de configuração for `mongodb`.
