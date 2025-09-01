"""
Testes para o sistema de gerenciamento de estado (StateRepository).

Este arquivo testa as implementações FileStateRepository e MongoStateRepository
conforme especificado no SAGA-008.
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

# Importar as classes que vamos testar
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from src.infrastructure.persistence.state_repository import FileStateRepository, MongoStateRepository
from src.ports.state_repository import StateRepository


class TestFileStateRepository:
    """Testes unitários para FileStateRepository."""

    def setup_method(self):
        """Setup executado antes de cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_home_path = self.temp_dir
        self.state_file_name = "test_state.json"
        self.repo = FileStateRepository()

    def teardown_method(self):
        """Cleanup executado após cada teste."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_state_creates_json_file_with_correct_content(self):
        """Testa se save_state cria um arquivo .json com o conteúdo correto."""
        test_state = {
            "conversation_history": [
                {"role": "user", "message": "test message"},
                {"role": "assistant", "message": "test response"}
            ],
            "agent_id": "test_agent",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        # Salvar o estado
        result = self.repo.save_state(self.agent_home_path, self.state_file_name, test_state)
        
        # Verificar que salvou com sucesso
        assert result is True
        
        # Verificar que o arquivo foi criado
        state_file_path = os.path.join(self.agent_home_path, self.state_file_name)
        assert os.path.exists(state_file_path)
        
        # Verificar o conteúdo do arquivo
        with open(state_file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data == test_state

    def test_load_state_reads_existing_json_file_correctly(self):
        """Testa se load_state lê o conteúdo de um arquivo .json existente corretamente."""
        test_state = {
            "conversation_history": [
                {"role": "user", "message": "test message"}
            ],
            "agent_id": "test_agent"
        }
        
        # Criar arquivo de estado manualmente
        state_file_path = os.path.join(self.agent_home_path, self.state_file_name)
        with open(state_file_path, 'w', encoding='utf-8') as f:
            json.dump(test_state, f)
        
        # Carregar o estado
        loaded_state = self.repo.load_state(self.agent_home_path, self.state_file_name)
        
        # Verificar que carregou corretamente
        assert loaded_state == test_state

    def test_load_state_returns_default_when_file_not_exists(self):
        """Testa se load_state retorna estado padrão quando arquivo não existe."""
        # Tentar carregar estado de arquivo inexistente
        loaded_state = self.repo.load_state(self.agent_home_path, "nonexistent.json")
        
        # Verificar que retornou estado padrão
        assert loaded_state == {"conversation_history": []}

    def test_save_state_creates_directory_if_not_exists(self):
        """Testa se save_state cria diretórios necessários se não existirem."""
        nested_path = os.path.join(self.temp_dir, "nested", "path")
        test_state = {"test": "data"}
        
        # Salvar em caminho que não existe
        result = self.repo.save_state(nested_path, self.state_file_name, test_state)
        
        # Verificar que salvou com sucesso
        assert result is True
        
        # Verificar que o diretório foi criado
        assert os.path.exists(nested_path)
        
        # Verificar que o arquivo foi criado
        state_file_path = os.path.join(nested_path, self.state_file_name)
        assert os.path.exists(state_file_path)


class TestMongoStateRepository:
    """Testes unitários para MongoStateRepository."""

    def test_init_raises_import_error_when_pymongo_not_available(self):
        """Testa se __init__ lança ImportError quando pymongo não está disponível."""
        with patch.dict('sys.modules', {'pymongo': None}):
            with pytest.raises(ImportError) as excinfo:
                MongoStateRepository()
            assert "pymongo is required" in str(excinfo.value)

    def test_init_raises_value_error_when_mongo_uri_not_set(self):
        """Testa se __init__ lança ValueError quando MONGO_URI não está definida."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                MongoStateRepository()
            assert "MONGO_URI environment variable is required" in str(excinfo.value)

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017'})
    def test_init_creates_connection_successfully(self, mock_mongo_client):
        """Testa se __init__ cria conexão com sucesso quando configurado corretamente."""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.admin.command.return_value = True
        
        repo = MongoStateRepository()
        
        # Verificar que o cliente foi criado
        mock_mongo_client.assert_called_once_with('mongodb://localhost:27017')
        
        # Verificar que o ping foi executado
        mock_client.admin.command.assert_called_once_with('ping')
        
        # Verificar propriedades da instância
        assert repo.client == mock_client
        assert repo.database == mock_client['conductor_state']
        assert repo.collection == mock_client['conductor_state']['agent_states']

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017'})
    def test_save_state_creates_or_updates_document_correctly(self, mock_mongo_client):
        """Testa se save_state cria/atualiza documento no MongoDB com os dados corretos."""
        # Setup mock
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.admin.command.return_value = True
        
        mock_collection = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_collection.update_one.return_value = mock_result
        
        # Criar repositório e testar
        repo = MongoStateRepository()
        
        test_state = {
            "conversation_history": [
                {"role": "user", "message": "test message"}
            ],
            "agent_id": "test_agent"
        }
        
        agent_home_path = "/test/path"
        state_file_name = "state.json"
        
        # Salvar estado
        result = repo.save_state(agent_home_path, state_file_name, test_state)
        
        # Verificar que retornou True
        assert result is True
        
        # Verificar que update_one foi chamado com os argumentos corretos
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        
        # Verificar o filtro (primeiro argumento)
        filter_arg = call_args[0][0]
        expected_doc_id = "/test/path_state.json"
        assert filter_arg == {"_id": expected_doc_id}
        
        # Verificar os dados (segundo argumento)
        update_arg = call_args[0][1]
        assert "$set" in update_arg
        
        set_data = update_arg["$set"]
        assert set_data["_id"] == expected_doc_id
        assert set_data["agent_home_path"] == agent_home_path
        assert set_data["state_file_name"] == state_file_name
        assert set_data["repository_type"] == "mongo"
        assert "updated_at" in set_data
        assert set_data["conversation_history"] == test_state["conversation_history"]
        assert set_data["agent_id"] == test_state["agent_id"]
        
        # Verificar que upsert=True foi usado
        kwargs = call_args[1]
        assert kwargs["upsert"] is True

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017'})
    def test_load_state_retrieves_correct_document(self, mock_mongo_client):
        """Testa se load_state recupera o documento correto do MongoDB."""
        # Setup mock
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.admin.command.return_value = True
        
        mock_collection = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        # Simular documento retornado pelo MongoDB
        mock_document = {
            "_id": "/test/path_state.json",
            "conversation_history": [
                {"role": "user", "message": "test message"}
            ],
            "agent_id": "test_agent",
            "repository_type": "mongo",
            "updated_at": "2024-01-01T00:00:00"
        }
        mock_collection.find_one.return_value = mock_document
        
        # Criar repositório e testar
        repo = MongoStateRepository()
        
        agent_home_path = "/test/path"
        state_file_name = "state.json"
        
        # Carregar estado
        loaded_state = repo.load_state(agent_home_path, state_file_name)
        
        # Verificar que find_one foi chamado com ID correto
        expected_doc_id = "/test/path_state.json"
        mock_collection.find_one.assert_called_once_with({"_id": expected_doc_id})
        
        # Verificar que o _id foi removido do resultado
        assert "_id" not in loaded_state
        
        # Verificar que os dados foram retornados corretamente
        assert loaded_state["conversation_history"] == mock_document["conversation_history"]
        assert loaded_state["agent_id"] == mock_document["agent_id"]
        assert loaded_state["repository_type"] == mock_document["repository_type"]

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017'})
    def test_load_state_returns_default_when_document_not_found(self, mock_mongo_client):
        """Testa se load_state retorna estado padrão quando documento não é encontrado."""
        # Setup mock
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.admin.command.return_value = True
        
        mock_collection = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        # Simular documento não encontrado
        mock_collection.find_one.return_value = None
        
        # Criar repositório e testar
        repo = MongoStateRepository()
        
        # Carregar estado de documento inexistente
        loaded_state = repo.load_state("/test/path", "state.json")
        
        # Verificar que retornou estado padrão
        assert loaded_state == {"conversation_history": []}

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017'})
    def test_close_closes_connection(self, mock_mongo_client):
        """Testa se close() fecha a conexão com o MongoDB."""
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.admin.command.return_value = True
        
        repo = MongoStateRepository()
        repo.close()
        
        # Verificar que close foi chamado
        mock_client.close.assert_called_once()


class TestStateRepositoryIntegration:
    """Testes de integração para o sistema StateRepository."""
    
    def setup_method(self):
        """Setup executado antes de cada teste."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup executado após cada teste."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_file_repository_roundtrip(self):
        """Testa ciclo completo de save/load com FileStateRepository."""
        repo = FileStateRepository()
        agent_home_path = self.temp_dir
        state_file_name = "integration_test.json"
        
        original_state = {
            "conversation_history": [
                {"role": "user", "message": "Hello"},
                {"role": "assistant", "message": "Hi there!"}
            ],
            "agent_id": "IntegrationTestAgent",
            "custom_data": {"test": True, "number": 42}
        }
        
        # Salvar estado
        save_result = repo.save_state(agent_home_path, state_file_name, original_state)
        assert save_result is True
        
        # Carregar estado
        loaded_state = repo.load_state(agent_home_path, state_file_name)
        
        # Verificar que o estado foi preservado
        assert loaded_state == original_state

    @patch('pymongo.MongoClient')
    @patch.dict(os.environ, {'MONGO_URI': 'mongodb://localhost:27017'})
    def test_mongo_repository_roundtrip(self, mock_mongo_client):
        """Testa ciclo completo de save/load com MongoStateRepository."""
        # Setup mocks para simular MongoDB
        mock_client = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.admin.command.return_value = True
        
        mock_collection = MagicMock()
        mock_client.__getitem__.return_value.__getitem__.return_value = mock_collection
        
        # Mock para save_state
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_collection.update_one.return_value = mock_result
        
        # Estado para teste
        original_state = {
            "conversation_history": [
                {"role": "user", "message": "Hello MongoDB"},
                {"role": "assistant", "message": "Hi from Mongo!"}
            ],
            "agent_id": "MongoIntegrationTestAgent"
        }
        
        repo = MongoStateRepository()
        agent_home_path = "/integration/test"
        state_file_name = "mongo_test.json"
        
        # Salvar estado
        save_result = repo.save_state(agent_home_path, state_file_name, original_state)
        assert save_result is True
        
        # Preparar mock para load_state
        # Simular documento com dados salvos + metadados do MongoDB
        mock_document = original_state.copy()
        mock_document.update({
            "_id": "/integration/test_mongo_test.json",
            "agent_home_path": agent_home_path,
            "state_file_name": state_file_name,
            "repository_type": "mongo",
            "updated_at": datetime.now().isoformat()
        })
        mock_collection.find_one.return_value = mock_document
        
        # Carregar estado
        loaded_state = repo.load_state(agent_home_path, state_file_name)
        
        # Verificar que os dados originais foram preservados
        assert loaded_state["conversation_history"] == original_state["conversation_history"]
        assert loaded_state["agent_id"] == original_state["agent_id"]
        
        # Verificar que metadados foram adicionados mas _id foi removido
        assert "_id" not in loaded_state
        assert loaded_state["repository_type"] == "mongo"
        assert "updated_at" in loaded_state


if __name__ == "__main__":
    # Permitir execução direta do arquivo de teste
    pytest.main([__file__, "-v"])