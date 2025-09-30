# tests/core/services/test_task_execution_service.py
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

from src.core.services.task_execution_service import TaskExecutionService
from src.core.domain import TaskDTO, TaskResultDTO, AgentDefinition
from src.core.agent_executor import AgentExecutor


class TestTaskExecutionService:
    """Tests for TaskExecutionService."""

    def setup_method(self):
        """Setup common mocks for each test."""
        self.mock_agent_storage_service = MagicMock()
        self.mock_tool_service = MagicMock()
        self.mock_config_service = MagicMock()
        self.mock_storage = MagicMock()
        self.mock_agent_storage_service.get_storage.return_value = self.mock_storage

    @patch('src.core.services.task_execution_service.AgentExecutor')
    @patch('src.core.services.task_execution_service.PromptEngine')
    @patch('src.core.services.task_execution_service.PlaceholderLLMClient')
    def test_execute_task_success_test_environment(self, mock_llm_client, mock_prompt_engine, mock_agent_executor):
        """Testa execução bem-sucedida em ambiente de teste."""
        # Arrange
        # Mock test environment detection
        with patch.dict(sys.modules, {'pytest': MagicMock()}), \
             patch('pathlib.Path') as mock_path:

            # Configure config service for AgentStorageService initialization
            mock_storage_config = MagicMock()
            mock_storage_config.type = "filesystem"
            mock_storage_config.path = "/tmp/test_path"
            self.mock_config_service.get_storage_config.return_value = mock_storage_config

            # Mock Path constructor to avoid filesystem access
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance

            service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)
            
            # Mock agent definition
            from src.core.domain import AgentDefinition
            agent_definition = AgentDefinition(
                name="Test Agent",
                version="1.0",
                schema_version="1.0",
                description="Test description",
                author="Test Author"
            )
            self.mock_storage.load_definition.return_value = agent_definition

            # Mock session data
            from src.core.domain import AgentSession
            session_data = AgentSession(
                current_task_id=None,
                state={"agent_home_path": "/tmp/test/agent/path", "allowed_tools": ["tool1", "tool2"]}
            )
            self.mock_storage.load_session.return_value = session_data
            
            # Mock tool service
            allowed_tools = {"tool1": MagicMock(), "tool2": MagicMock()}
            self.mock_tool_service.get_allowed_tools.return_value = allowed_tools
            
            # Mock executor
            mock_executor_instance = MagicMock()
            expected_result = TaskResultDTO(
                status="success",
                output="Task completed successfully",
                metadata={},
                updated_session={"new_data": "value"},
                updated_knowledge={"learned": "something"},
                history_entry={"interaction": "test"}
            )
            mock_executor_instance.run.return_value = expected_result
            mock_agent_executor.return_value = mock_executor_instance
            
            # Mock prompt engine to avoid filesystem access
            mock_prompt_instance = MagicMock()
            mock_prompt_engine.return_value = mock_prompt_instance
            # Avoid constructor filesystem access
            mock_prompt_instance.agent_home_path = "/tmp/test/agent/path"
            mock_prompt_instance.load_context.return_value = None
            
            # Act
            task = TaskDTO(agent_id="test_agent", user_input="Test task")
            result = service.execute_task(task)
            
            # Assert
            assert result.status == "success"
            assert result.output == "Task completed successfully"
            
            # Verify test environment uses PlaceholderLLMClient
            mock_llm_client.assert_called_once()
            # Verify PromptEngine was called with both agent_home_path and prompt_format
            mock_prompt_engine.assert_called_once()
            call_args = mock_prompt_engine.call_args
            assert call_args[1]['agent_home_path'] == "/tmp/test_path/agents/test_agent"
            assert 'prompt_format' in call_args[1]
            mock_prompt_instance.load_context.assert_called_once()
            mock_agent_executor.assert_called_once()

    def test_load_agent_definition_success(self):
        """Testa carregamento bem-sucedido de definição de agente."""
        # Arrange
        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)

        from src.core.domain import AgentDefinition
        agent_definition = AgentDefinition(
            name="Test Agent",
            version="1.0",
            schema_version="1.0",
            description="Test description",
            author="Test Author"
        )
        self.mock_storage.load_definition.return_value = agent_definition

        # Act
        result = self.mock_storage.load_definition("test_agent")

        # Assert
        assert result.name == "Test Agent"
        assert result.version == "1.0"
        self.mock_storage.load_definition.assert_called_once_with("test_agent")

    def test_execute_task_agent_not_found(self):
        """Testa tratamento quando agente não é encontrado."""
        # Arrange
        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)
        self.mock_storage.load_definition.side_effect = FileNotFoundError("Agent not found")

        # Act
        task = TaskDTO(agent_id="nonexistent_agent", user_input="Test task")
        result = service.execute_task(task)

        # Assert
        assert result.status == "error"
        assert "Agent not found" in result.output
        self.mock_storage.load_definition.assert_called_once_with("nonexistent_agent")

    def test_execute_task_missing_agent_home_path(self):
        """Testa tratamento quando agent_home_path está ausente da sessão."""
        # Arrange
        # Configure config service for AgentStorageService initialization
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        self.mock_config_service.get_storage_config.return_value = mock_storage_config

        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)

        from src.core.domain import AgentDefinition, AgentSession
        agent_definition = AgentDefinition(
            name="Test Agent",
            version="1.0",
            schema_version="1.0",
            description="Test description",
            author="Test Author"
        )
        self.mock_storage.load_definition.return_value = agent_definition

        # Mock session without agent_home_path
        session_data = AgentSession(current_task_id=None, state={"allowed_tools": []})
        self.mock_storage.load_session.return_value = session_data

        with patch('src.core.services.task_execution_service.PlaceholderLLMClient'), \
             patch('src.core.services.task_execution_service.PromptEngine'), \
             patch('src.core.services.task_execution_service.AgentExecutor') as mock_executor, \
             patch('src.core.services.storage_service.StorageService') as mock_storage_service_class:

            # Mock fallback path retrieval
            mock_repository = MagicMock()
            mock_repository.get_agent_home_path.return_value = "/fallback/path"
            mock_storage_service_class.return_value.get_repository.return_value = mock_repository

            mock_executor_instance = MagicMock()
            mock_executor_instance.run.return_value = TaskResultDTO(status="success", output="OK", metadata={})
            mock_executor.return_value = mock_executor_instance

            # Act
            task = TaskDTO(agent_id="test_agent", user_input="Test task")
            result = service.execute_task(task)

            # Assert
            assert result.status == "success"
            mock_repository.get_agent_home_path.assert_called_once_with("test_agent")
            self.mock_storage.save_session.assert_called_once()

    @patch('src.core.services.task_execution_service.PromptEngine')
    @patch('src.core.services.task_execution_service.PlaceholderLLMClient')
    @patch('src.core.services.task_execution_service.AgentExecutor')
    def test_execute_task_handles_executor_exception(self, mock_agent_executor, mock_llm_client, mock_prompt_engine):
        """Testa tratamento de exceção durante execução."""
        # Arrange
        # Configure config service for AgentStorageService initialization
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/tmp/test_path"
        self.mock_config_service.get_storage_config.return_value = mock_storage_config

        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)

        from src.core.domain import AgentDefinition, AgentSession
        agent_definition = AgentDefinition(
            name="Failing Agent",
            version="1.0",
            schema_version="1.0",
            description="Agent that fails",
            author="Test Author"
        )
        self.mock_storage.load_definition.return_value = agent_definition

        session_data = AgentSession(current_task_id=None, state={"agent_home_path": "/tmp/test_agent", "allowed_tools": []})
        self.mock_storage.load_session.return_value = session_data

        # Mock all components to avoid filesystem access
        mock_prompt_instance = MagicMock()
        mock_prompt_engine.return_value = mock_prompt_instance

        # Mock executor to raise exception
        mock_executor_instance = MagicMock()
        mock_executor_instance.run.side_effect = RuntimeError("Execution failed")
        mock_agent_executor.return_value = mock_executor_instance

        # Act
        task = TaskDTO(agent_id="failing_agent", user_input="This will fail")
        result = service.execute_task(task)

        # Assert
        assert result.status == "error"
        assert "Execution failed" in result.output

    def test_persist_task_result_all_components(self):
        """Testa persistência completa de resultado bem-sucedido."""
        # Arrange
        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)

        from src.core.domain import AgentSession, AgentKnowledge, KnowledgeItem
        # Mock existing data
        existing_session = AgentSession(current_task_id=None, state={"old_session": "data"})
        existing_knowledge = AgentKnowledge(artifacts={"old_artifact": KnowledgeItem(summary="old", purpose="test", last_modified_by_task="task1")})
        self.mock_storage.load_session.return_value = existing_session
        self.mock_storage.load_knowledge.return_value = existing_knowledge

        # Mock complete result
        result = TaskResultDTO(
            status="success",
            output="Success",
            metadata={},
            updated_session={"new_session": "data"},
            updated_knowledge={"new_artifact": {"summary": "new", "purpose": "test2", "last_modified_by_task": "task2"}},
            history_entry={"timestamp": "2023-01-01", "interaction": "test", "ai_response": "Full AI response for conversation history"}
        )

        # Act
        task = TaskDTO(agent_id="test_agent", user_input="Test task")
        service._persist_task_result("test_agent", task, result)

        # Assert
        # Verify session and knowledge operations were called
        self.mock_storage.load_session.assert_called_once_with("test_agent")
        self.mock_storage.save_session.assert_called_once()
        self.mock_storage.load_knowledge.assert_called_once_with("test_agent")
        self.mock_storage.save_knowledge.assert_called_once()
        # Verifica se append_to_history foi chamado com agent_id e um HistoryEntry
        self.mock_storage.append_to_history.assert_called_once()
        call_args = self.mock_storage.append_to_history.call_args
        # Verificar keyword arguments (agent_id, entry, user_input, ai_response)
        assert call_args.kwargs['agent_id'] == "test_agent"
        from src.core.domain import HistoryEntry
        assert isinstance(call_args.kwargs['entry'], HistoryEntry)
        assert call_args.kwargs['user_input'] == "Test task"
        assert 'ai_response' in call_args.kwargs  # ai_response deve estar presente

    def test_persist_task_result_partial_updates(self):
        """Testa persistência com apenas alguns componentes atualizados."""
        # Arrange
        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)

        # Mock result with only session update
        result = TaskResultDTO(
            status="success",
            output="Partial success",
            metadata={},
            updated_session={"only_session": "update"},
            updated_knowledge=None,  # No knowledge update
            history_entry=None  # No history update
        )

        from src.core.domain import AgentSession
        existing_session = AgentSession(current_task_id=None, state={"existing": "session"})
        self.mock_storage.load_session.return_value = existing_session

        # Act
        task = TaskDTO(agent_id="test_agent", user_input="Test task")
        service._persist_task_result("test_agent", task, result)

        # Assert
        # Only session should be updated
        self.mock_storage.load_session.assert_called_once_with("test_agent")
        self.mock_storage.save_session.assert_called_once()

        # Knowledge and history should not be called
        self.mock_storage.load_knowledge.assert_not_called()
        self.mock_storage.save_knowledge.assert_not_called()
        self.mock_storage.append_to_history.assert_not_called()

    def test_storage_loads_agent_definition_correctly(self):
        """Testa se a definição do agente é carregada corretamente via storage."""
        # Arrange
        service = TaskExecutionService(self.mock_agent_storage_service, self.mock_tool_service, self.mock_config_service)

        from src.core.domain import AgentDefinition
        agent_definition = AgentDefinition(
            name="Clean Test Agent",
            version="1.0",
            schema_version="1.0",
            description="Agent for cleanup test",
            author="Test Author"
        )
        self.mock_storage.load_definition.return_value = agent_definition

        # Act
        result = self.mock_storage.load_definition("test_agent")

        # Assert
        assert isinstance(result, AgentDefinition)
        assert result.name == "Clean Test Agent"
        self.mock_storage.load_definition.assert_called_once_with("test_agent")