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
        self.mock_storage_service = MagicMock()
        self.mock_tool_service = MagicMock()
        self.mock_config_service = MagicMock()
        self.mock_repository = MagicMock()
        self.mock_storage_service.get_repository.return_value = self.mock_repository

    @patch('src.core.services.task_execution_service.AgentExecutor')
    @patch('src.core.services.task_execution_service.PromptEngine')
    @patch('src.core.services.task_execution_service.PlaceholderLLMClient')
    def test_execute_task_success_test_environment(self, mock_llm_client, mock_prompt_engine, mock_agent_executor):
        """Testa execução bem-sucedida em ambiente de teste."""
        # Arrange
        # Mock test environment detection
        with patch.dict(sys.modules, {'pytest': MagicMock()}):
            service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
            
            # Mock agent definition
            definition_data = {
                "name": "Test Agent",
                "version": "1.0",
                "schema_version": "1.0",
                "description": "Test description",
                "author": "Test Author"
            }
            self.mock_repository.load_definition.return_value = definition_data
            
            # Mock session data
            session_data = {
                "agent_home_path": "/test/agent/path",
                "allowed_tools": ["tool1", "tool2"]
            }
            self.mock_repository.load_session.return_value = session_data
            
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
            
            # Mock prompt engine
            mock_prompt_instance = MagicMock()
            mock_prompt_engine.return_value = mock_prompt_instance
            
            # Act
            task = TaskDTO(agent_id="test_agent", user_input="Test task")
            result = service.execute_task(task)
            
            # Assert
            assert result.status == "success"
            assert result.output == "Task completed successfully"
            
            # Verify test environment uses PlaceholderLLMClient
            mock_llm_client.assert_called_once()
            mock_prompt_engine.assert_called_once_with(agent_home_path="/test/agent/path")
            mock_prompt_instance.load_context.assert_called_once()
            mock_agent_executor.assert_called_once()

    def test_load_agent_definition_success(self):
        """Testa carregamento bem-sucedido de definição de agente."""
        # Arrange
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        
        definition_data = {
            "name": "Test Agent",
            "version": "1.0",
            "schema_version": "1.0",
            "description": "Test description", 
            "author": "Test Author",
            "tags": [],
            "capabilities": [],
            "allowed_tools": []
        }
        self.mock_repository.load_definition.return_value = definition_data
        
        # Act
        agent_def = service._load_agent_definition("test_agent")
        
        # Assert
        assert agent_def.name == "Test Agent"
        assert agent_def.version == "1.0"
        self.mock_repository.load_definition.assert_called_once_with("test_agent")

    def test_execute_task_agent_not_found(self):
        """Testa tratamento quando agente não é encontrado."""
        # Arrange
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        self.mock_repository.load_definition.return_value = None
        
        # Act
        task = TaskDTO(agent_id="nonexistent_agent", user_input="Test task")
        result = service.execute_task(task)
        
        # Assert
        assert result.status == "error"
        assert "Definição não encontrada para o agente: nonexistent_agent" in result.output
        self.mock_repository.load_definition.assert_called_once_with("nonexistent_agent")

    def test_execute_task_missing_agent_home_path(self):
        """Testa tratamento quando agent_home_path está ausente da sessão."""
        # Arrange
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        
        # Mock agent definition
        definition_data = {
            "name": "Test Agent",
            "version": "1.0",
            "schema_version": "1.0", 
            "description": "Test description",
            "author": "Test Author"
        }
        self.mock_repository.load_definition.return_value = definition_data
        
        # Mock session without agent_home_path
        session_data = {"allowed_tools": []}
        self.mock_repository.load_session.return_value = session_data
        self.mock_repository.get_agent_home_path.return_value = "/fallback/path"
        
        with patch('src.core.services.task_execution_service.PlaceholderLLMClient'), \
             patch('src.core.services.task_execution_service.PromptEngine'), \
             patch('src.core.services.task_execution_service.AgentExecutor') as mock_executor:
            
            mock_executor_instance = MagicMock()
            mock_executor_instance.run.return_value = TaskResultDTO(status="success", output="OK", metadata={})
            mock_executor.return_value = mock_executor_instance
            
            # Act
            task = TaskDTO(agent_id="test_agent", user_input="Test task")
            result = service.execute_task(task)
            
            # Assert
            assert result.status == "success"
            self.mock_repository.get_agent_home_path.assert_called_once_with("test_agent")
            self.mock_repository.save_session.assert_called_once()

    @patch('src.core.services.task_execution_service.AgentExecutor')
    def test_execute_task_handles_executor_exception(self, mock_agent_executor):
        """Testa tratamento de exceção durante execução."""
        # Arrange
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        
        # Mock successful setup but executor raises exception
        definition_data = {
            "name": "Failing Agent",
            "version": "1.0",
            "schema_version": "1.0",
            "description": "Agent that fails",
            "author": "Test Author"
        }
        self.mock_repository.load_definition.return_value = definition_data
        self.mock_repository.load_session.return_value = {"agent_home_path": "/test", "allowed_tools": []}
        
        # Mock executor to raise exception
        mock_executor_instance = MagicMock()
        mock_executor_instance.run.side_effect = RuntimeError("Execution failed")
        mock_agent_executor.return_value = mock_executor_instance
        
        with patch('src.core.services.task_execution_service.PlaceholderLLMClient'), \
             patch('src.core.services.task_execution_service.PromptEngine'):
            
            # Act
            task = TaskDTO(agent_id="failing_agent", user_input="This will fail")
            result = service.execute_task(task)
            
            # Assert
            assert result.status == "error"
            assert "Execution failed" in result.output

    def test_persist_task_result_all_components(self):
        """Testa persistência completa de resultado bem-sucedido."""
        # Arrange
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        
        # Mock existing data
        existing_session = {"old_session": "data"}
        existing_knowledge = {"old_knowledge": "data"}
        self.mock_repository.load_session.return_value = existing_session
        self.mock_repository.load_knowledge.return_value = existing_knowledge
        
        # Mock complete result
        result = TaskResultDTO(
            status="success",
            output="Success",
            metadata={},
            updated_session={"new_session": "data"},
            updated_knowledge={"new_knowledge": "data"},
            history_entry={"timestamp": "2023-01-01", "interaction": "test"}
        )
        
        # Act
        service._persist_task_result("test_agent", result)
        
        # Assert
        # Verify session merge and save
        expected_session = {"old_session": "data", "new_session": "data"}
        self.mock_repository.save_session.assert_called_once_with("test_agent", expected_session)
        
        # Verify knowledge merge and save
        expected_knowledge = {"old_knowledge": "data", "new_knowledge": "data"}
        self.mock_repository.save_knowledge.assert_called_once_with("test_agent", expected_knowledge)
        
        # Verify history append
        self.mock_repository.append_to_history.assert_called_once_with(
            "test_agent", 
            {"timestamp": "2023-01-01", "interaction": "test"}
        )

    def test_persist_task_result_partial_updates(self):
        """Testa persistência com apenas alguns componentes atualizados."""
        # Arrange
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        
        # Mock result with only session update
        result = TaskResultDTO(
            status="success",
            output="Partial success", 
            metadata={},
            updated_session={"only_session": "update"},
            updated_knowledge=None,  # No knowledge update
            history_entry=None  # No history update
        )
        
        existing_session = {"existing": "session"}
        self.mock_repository.load_session.return_value = existing_session
        
        # Act
        service._persist_task_result("test_agent", result)
        
        # Assert
        # Only session should be updated
        expected_session = {"existing": "session", "only_session": "update"}
        self.mock_repository.save_session.assert_called_once_with("test_agent", expected_session)
        
        # Knowledge and history should not be called
        self.mock_repository.load_knowledge.assert_not_called()
        self.mock_repository.save_knowledge.assert_not_called()
        self.mock_repository.append_to_history.assert_not_called()

    def test_load_agent_definition_cleans_agent_id(self):
        """Testa se agent_id é removido corretamente dos dados da definição."""
        # Arrange  
        service = TaskExecutionService(self.mock_storage_service, self.mock_tool_service, self.mock_config_service)
        
        definition_data = {
            "name": "Clean Test Agent",
            "version": "1.0",
            "schema_version": "1.0",
            "description": "Agent for cleanup test",
            "author": "Test Author",
            "agent_id": "should_be_removed",
            "tags": [],
            "capabilities": [],
            "allowed_tools": []
        }
        self.mock_repository.load_definition.return_value = definition_data
        
        # Act
        agent_def = service._load_agent_definition("test_agent")
        
        # Assert
        assert isinstance(agent_def, AgentDefinition)
        assert agent_def.name == "Clean Test Agent"
        # The agent_id should not be in the AgentDefinition constructor
        # (it's handled separately in the domain model)