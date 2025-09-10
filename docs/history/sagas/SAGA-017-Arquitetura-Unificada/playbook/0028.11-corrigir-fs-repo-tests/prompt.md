# Especificação Técnica e Plano de Execução: 0028.11-corrigir-fs-repo-tests

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa resolver as incompatibilidades de assinatura de método nos testes de `FileStateRepository` e garantir que o `ConductorService` seja inicializado corretamente com o `base_path` para o `FileSystemStateRepository`, permitindo a descoberta de agentes e a validação da Fase VII.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar os arquivos `src/infrastructure/persistence/state_repository.py` e `src/core/conductor_service.py`.

**Arquivo 1 (Modificar): `src/infrastructure/persistence/state_repository.py`**

```python
# src/infrastructure/persistence/state_repository.py
# ... (imports existentes)

class FileStateRepository(StateRepository):
    # ... (manter __init__ e list_agents)

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # ... (manter implementação existente)
        pass

    def save_state(
        self, agent_id: str, state_data: Dict[str, Any]
    ) -> bool:
        # ... (manter implementação existente)
        pass


class MongoStateRepository(StateRepository):
    # ... (manter __init__ e close)

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # Ajustar assinatura para corresponder à IStateRepository
        # O _generate_document_id precisará ser ajustado ou removido se não for mais necessário
        # Implementação real para MongoDB
        document_id = self._generate_document_id(agent_id, "state.json") # Assumindo state.json como nome padrão
        document = self.collection.find_one({"_id": document_id})
        if document:
            document.pop("_id", None)
            return document
        return {"definition": {"name": "", "version": "", "schema_version": "", "description": "", "author": "", "tags": [], "capabilities": [], "allowed_tools": []}}

    def save_state(
        self, agent_id: str, state_data: Dict[str, Any]
    ) -> bool:
        # Ajustar assinatura para corresponder à IStateRepository
        # Implementação real para MongoDB
        document_id = self._generate_document_id(agent_id, "state.json") # Assumindo state.json como nome padrão
        document_data = state_data.copy()
        document_data.update({"_id": document_id, "updated_at": datetime.now().isoformat()})
        result = self.collection.update_one(
            {"_id": document_id}, {"$set": document_data}, upsert=True
        )
        return result.acknowledged

    def list_agents(self) -> List[str]:
        # Implementação real para MongoDB
        # Retorna os agent_ids de todos os documentos na coleção
        return [doc["agent_id"] for doc in self.collection.find({}, {"agent_id": 1})]
```

**Arquivo 2 (Modificar): `src/core/conductor_service.py`**

```python
# src/core/conductor_service.py
# ... (imports existentes)

class ConductorService(IConductorService):
    # ... (manter __init__ e outros métodos)

    def _create_storage_backend(self, storage_config: StorageConfig) -> IStateRepository:
        if storage_config.type == "filesystem":
            # Passar o base_path para o FileSystemStateRepository
            return FileSystemStateRepository(base_path=storage_config.path)
        elif storage_config.type == "mongodb":
            # MongoStateRepository agora também recebe base_path para consistência
            return MongoStateRepository(database_name="conductor_state", collection_name="agent_states")
        else:
            raise ConfigurationError(f"Tipo de armazenamento desconhecido: {storage_config.type}")

    # ... (manter outros métodos)
```

**Arquivo 3 (Modificar): `tests/test_state_management.py`**

```python
# tests/test_state_management.py
# ... (imports existentes)

class TestFileStateRepository:
    # ... (manter setup_method e teardown_method)

    def test_save_state_creates_json_file_with_correct_content(self):
        # ... (manter test_state)
        # Salvar o estado
        result = self.repo.save_state(
            test_state["agent_id"], test_state # Passar apenas agent_id e state_data
        )
        # ... (restante do teste)

    def test_load_state_reads_existing_json_file_correctly(self):
        # ... (manter test_state e criação do arquivo)
        # Carregar o estado
        loaded_state = self.repo.load_state(test_state["agent_id"]) # Passar apenas agent_id
        # ... (restante do teste)

    def test_load_state_returns_default_when_file_not_exists(self):
        # Tentar carregar estado de arquivo inexistente
        loaded_state = self.repo.load_state("nonexistent_agent") # Passar apenas agent_id
        # ... (restante do teste)

    def test_save_state_creates_directory_if_not_exists(self):
        # ... (manter nested_path e test_state)
        # Salvar em caminho que não existe
        # O FileStateRepository agora gerencia o caminho base internamente
        # Este teste pode precisar ser reavaliado ou removido se a lógica de path for totalmente interna
        # Por enquanto, vamos ajustar a chamada para a nova assinatura
        result = self.repo.save_state("new_agent_id", test_state) # Passar apenas agent_id e state_data
        # ... (restante do teste)


class TestMongoStateRepository:
    # ... (manter testes existentes)

    @patch("pymongo.MongoClient")
    @patch.dict(os.environ, {"MONGO_URI": "mongodb://localhost:27017"})
    def test_save_state_creates_or_updates_document_correctly(self, mock_mongo_client):
        # ... (manter setup mock)
        # Criar repositório e testar
        repo = MongoStateRepository()

        test_state = {
            "conversation_history": [{"role": "user", "message": "test message"}],
            "agent_id": "test_agent",
        }

        # Salvar estado
        result = repo.save_state(test_state["agent_id"], test_state) # Ajustar assinatura
        # ... (restante do teste)

    @patch("pymongo.MongoClient")
    @patch.dict(os.environ, {"MONGO_URI": "mongodb://localhost:27017"})
    def test_load_state_retrieves_correct_document(self, mock_mongo_client):
        # ... (manter setup mock)
        # Simular documento retornado pelo MongoDB
        mock_document = {
            "_id": "test_agent", # ID do documento agora é o agent_id
            "conversation_history": [{"role": "user", "message": "test message"}],
            "agent_id": "test_agent",
            "repository_type": "mongo",
            "updated_at": "2024-01-01T00:00:00",
        }
        mock_collection.find_one.return_value = mock_document

        # Criar repositório e testar
        repo = MongoStateRepository()

        # Carregar estado
        loaded_state = repo.load_state("test_agent") # Ajustar assinatura
        # ... (restante do teste)

    @patch("pymongo.MongoClient")
    @patch.dict(os.environ, {"MONGO_URI": "mongodb://localhost:27017"})
    def test_load_state_returns_default_when_document_not_found(self, mock_mongo_client):
        # ... (manter setup mock)
        # Carregar estado de documento inexistente
        loaded_state = repo.load_state("nonexistent_agent") # Ajustar assinatura
        # ... (restante do teste)


class TestStateRepositoryIntegration:
    # ... (manter setup_method e teardown_method)

    def test_file_repository_roundtrip(self):
        # ... (manter original_state)
        # Salvar estado
        save_result = self.repo.save_state(original_state["agent_id"], original_state) # Ajustar assinatura
        # ... (restante do teste)

    @pytest.mark.mongo
    @patch("pymongo.MongoClient")
    @patch.dict(os.environ, {"MONGO_URI": "mongodb://localhost:27017"})
    def test_mongo_repository_roundtrip(self, mock_mongo_client):
        # ... (manter setup mocks e original_state)
        # Salvar estado
        save_result = repo.save_state(original_state["agent_id"], original_state) # Ajustar assinatura
        # ... (restante do teste)

        # Preparar mock para load_state
        # Simular documento com dados salvos + metadados do MongoDB
        mock_document = original_state.copy()
        mock_document.update(
            {
                "_id": original_state["agent_id"], # ID do documento agora é o agent_id
                "repository_type": "mongo",
                "updated_at": datetime.now().isoformat(),
            }
        )
        mock_collection.find_one.return_value = mock_document

        # Carregar estado
        loaded_state = repo.load_state(original_state["agent_id"]) # Ajustar assinatura
        # ... (restante do teste)
```

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
