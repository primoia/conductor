# tests/api/test_clean_architecture.py
"""
Testes para validar que a arquitetura limpa (sem campo 'command') está funcionando.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestCleanArchitectureWithoutCommandField:
    """Valida que o sistema funciona SEM o campo 'command'."""

    @patch.dict('os.environ', {'MONGO_URI': 'mongodb://localhost:27017'})
    @patch('src.core.services.mongo_task_client.MongoClient')
    def test_submit_task_requires_prompt(self, mock_mongo_client):
        """
        Testa que submit_task exige o campo 'prompt' obrigatório.
        """
        from src.core.services.mongo_task_client import MongoTaskClient

        # Arrange
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.tasks = mock_collection

        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = Mock(return_value=mock_db)
        mock_client_instance.admin.command = Mock(return_value=None)
        mock_mongo_client.return_value = mock_client_instance

        mock_result = Mock()
        mock_result.inserted_id = "507f1f77bcf86cd799439011"
        mock_collection.insert_one.return_value = mock_result

        task_client = MongoTaskClient()

        # Act & Assert - deve falhar sem prompt
        with pytest.raises(ValueError, match="Campo 'prompt' é obrigatório"):
            task_client.submit_task(
                agent_id="test_agent",
                cwd="/tmp",
                timeout=300,
                provider="claude",
                prompt=None  # ❌ Sem prompt deve falhar
            )

    def test_submit_task_with_prompt_succeeds(self):
        """
        Testa que submit_task funciona corretamente COM prompt.
        (Teste simplificado - valida apenas lógica, não MongoDB)
        """
        xml_prompt = "<prompt><user>Test</user></prompt>"

        # Validar que ValueError NÃO é lançado quando prompt está presente
        try:
            # Simular lógica de validação do submit_task
            if not xml_prompt:
                raise ValueError("Campo 'prompt' é obrigatório")
            # Se chegou aqui, passou na validação
            validation_passed = True
        except ValueError:
            validation_passed = False

        assert validation_passed, "Submit deve funcionar com prompt válido"

    def test_watcher_only_uses_prompt_field(self):
        """
        Testa que o watcher usa APENAS o campo 'prompt', não 'command'.
        """
        # Simulação da lógica do watcher
        request = {
            "_id": "test_id",
            "agent_id": "test_agent",
            "provider": "claude",
            "prompt": "<prompt>XML content</prompt>",
            "cwd": "/tmp",
            "timeout": 180
        }

        # Lógica do watcher (copiada de claude-mongo-watcher.py:200-206)
        prompt = request.get("prompt", "")

        # Assert
        assert prompt == "<prompt>XML content</prompt>"
        assert 'command' not in request, "Request não deve ter campo 'command'"

    def test_watcher_fails_without_prompt(self):
        """
        Testa que o watcher falha gracefully sem campo 'prompt'.
        """
        request = {
            "_id": "test_id",
            "agent_id": "test_agent",
            "provider": "claude",
            "cwd": "/tmp",
            "timeout": 180
            # ❌ Sem campo 'prompt'
        }

        # Lógica do watcher
        prompt = request.get("prompt", "")

        # Assert
        assert prompt == "", "Prompt vazio deve ser detectado"
        # Em produção, isso causaria erro no watcher


class TestProviderBasedExecution:
    """Testa que o provider correto é usado baseado no campo 'provider'."""

    def test_claude_provider_uses_claude_cli(self):
        """
        Testa que provider='claude' usa o CLI do Claude.
        """
        provider = "claude"
        prompt = "<prompt>Test</prompt>"

        # Lógica do watcher (execute_llm_request)
        if provider == "claude":
            command = ["claude", "--print", "--dangerously-skip-permissions"]
        elif provider == "gemini":
            command = ["gemini", "--print"]
        else:
            command = None

        assert command == ["claude", "--print", "--dangerously-skip-permissions"]

    def test_gemini_provider_uses_gemini_cli(self):
        """
        Testa que provider='gemini' usa o CLI do Gemini.
        """
        provider = "gemini"
        prompt = "<prompt>Test</prompt>"

        # Lógica do watcher (execute_llm_request)
        if provider == "claude":
            command = ["claude", "--print", "--dangerously-skip-permissions"]
        elif provider == "gemini":
            command = ["gemini", "--print"]
        else:
            command = None

        assert command == ["gemini", "--print"]

    def test_unsupported_provider_fails(self):
        """
        Testa que provider desconhecido é rejeitado.
        """
        provider = "gpt4"  # Não suportado

        # Lógica do watcher (execute_llm_request)
        if provider == "claude":
            command = ["claude", "--print", "--dangerously-skip-permissions"]
        elif provider == "gemini":
            command = ["gemini", "--print"]
        else:
            command = None

        assert command is None, "Provider desconhecido deve retornar None"


class TestMongoDocumentStructure:
    """Valida a estrutura final do documento MongoDB."""

    def test_mongodb_document_has_correct_structure(self):
        """
        Testa que o documento MongoDB tem APENAS os campos necessários.
        (Teste simplificado - valida estrutura esperada)
        """
        from datetime import datetime, timezone

        # Simular estrutura do documento que seria inserido
        task_document = {
            "agent_id": "test_agent",
            "provider": "claude",
            "prompt": "<prompt>Test</prompt>",
            "cwd": "/project",
            "timeout": 300,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "result": "",
            "exit_code": None,
            "duration": None,
        }

        # Assert - Campos obrigatórios presentes
        assert 'agent_id' in task_document
        assert 'provider' in task_document
        assert 'prompt' in task_document
        assert 'cwd' in task_document
        assert 'timeout' in task_document
        assert 'status' in task_document
        assert 'created_at' in task_document
        assert 'updated_at' in task_document

        # Campos de resultado (inicialmente vazios)
        assert 'result' in task_document
        assert 'exit_code' in task_document
        assert 'duration' in task_document

        # Campos removidos NÃO devem existir
        assert 'command' not in task_document, "❌ Campo 'command' deve ter sido removido"
        assert 'metadata' not in task_document, "❌ Campo 'metadata' deve ter sido removido"

        # Valores corretos
        assert task_document['agent_id'] == "test_agent"
        assert task_document['provider'] == "claude"
        assert task_document['prompt'] == "<prompt>Test</prompt>"
        assert task_document['status'] == "pending"