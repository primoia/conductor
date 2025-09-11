# tests/core/services/test_agent_discovery_service.py
import pytest
from unittest.mock import MagicMock, Mock, patch, mock_open

from src.core.services.agent_discovery_service import AgentDiscoveryService
from src.core.services.storage_service import StorageService
from src.core.domain import AgentDefinition


class TestAgentDiscoveryService:
    """Tests for AgentDiscoveryService."""

    def test_discover_agents_success_multiple_agents(self):
        """Testa descoberta bem-sucedida de múltiplos agentes."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        # Mock agent IDs and definitions
        mock_repository.list_agents.return_value = ["agent1", "agent2", "agent3"]
        mock_repository.load_definition.side_effect = [
            {
                "name": "Agent 1",
                "version": "1.0",
                "schema_version": "1.0",
                "description": "First agent",
                "author": "Test Author",
                "agent_id": "agent1"  # This should be removed
            },
            {
                "name": "Agent 2", 
                "version": "2.0",
                "schema_version": "1.0",
                "description": "Second agent",
                "author": "Test Author"
            },
            {
                "name": "Agent 3",
                "version": "1.5",
                "schema_version": "1.0", 
                "description": "Third agent",
                "author": "Test Author"
            }
        ]
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        agents = service.discover_agents()
        
        # Assert
        assert len(agents) == 3
        assert agents[0].name == "Agent 1"
        assert agents[0].agent_id == "agent1"
        assert agents[1].name == "Agent 2"
        assert agents[1].agent_id == "agent2"
        assert agents[2].name == "Agent 3"
        assert agents[2].agent_id == "agent3"
        
        mock_repository.list_agents.assert_called_once()
        assert mock_repository.load_definition.call_count == 3

    def test_discover_agents_empty_list(self):
        """Testa descoberta quando não há agentes."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        mock_repository.list_agents.return_value = []
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        agents = service.discover_agents()
        
        # Assert
        assert len(agents) == 0
        mock_repository.list_agents.assert_called_once()
        mock_repository.load_definition.assert_not_called()

    def test_discover_agents_skips_invalid_definitions(self):
        """Testa se agentes com definições inválidas são pulados."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.list_agents.return_value = ["valid_agent", "invalid_agent"]
        mock_repository.load_definition.side_effect = [
            {
                "name": "Valid Agent",
                "version": "1.0", 
                "schema_version": "1.0",
                "description": "Valid agent",
                "author": "Test Author"
            },
            None  # Invalid/missing definition
        ]
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        agents = service.discover_agents()
        
        # Assert
        assert len(agents) == 1
        assert agents[0].name == "Valid Agent"
        assert agents[0].agent_id == "valid_agent"

    def test_get_agent_definition_success(self):
        """Testa carregamento bem-sucedido de definição específica."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_definition_data = {
            "name": "Test Agent",
            "version": "2.0",
            "schema_version": "1.0",
            "description": "Test description",
            "author": "Test Author",
            "agent_id": "should_be_removed"  # Should be stripped
        }
        mock_repository.load_definition.return_value = mock_definition_data
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        agent_def = service.get_agent_definition("test_agent")
        
        # Assert
        assert agent_def is not None
        assert isinstance(agent_def, AgentDefinition)
        assert agent_def.name == "Test Agent"
        assert agent_def.agent_id == "test_agent"
        assert not hasattr(agent_def, 'agent_id') or agent_def.agent_id == "test_agent"
        mock_repository.load_definition.assert_called_once_with("test_agent")

    def test_get_agent_definition_not_found(self):
        """Testa comportamento quando definição não é encontrada."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        mock_repository.load_definition.return_value = None
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        agent_def = service.get_agent_definition("nonexistent_agent")
        
        # Assert
        assert agent_def is None
        mock_repository.load_definition.assert_called_once_with("nonexistent_agent")

    def test_storage_service_integration(self):
        """Testa integração correta com StorageService."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        
        # Assert
        mock_storage_service.get_repository.assert_called_once()
        assert service._storage == mock_repository

    def test_discover_agents_handles_agent_id_cleanup(self):
        """Testa se agent_id é corretamente removido dos dados da definição."""
        # Arrange
        mock_storage_service = MagicMock()
        mock_repository = MagicMock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.list_agents.return_value = ["clean_test"]
        mock_repository.load_definition.return_value = {
            "name": "Clean Agent",
            "version": "1.0",
            "schema_version": "1.0", 
            "description": "Agent for cleanup test",
            "author": "Test Author",
            "agent_id": "this_should_be_removed",
            "tags": [],
            "capabilities": [],
            "allowed_tools": []
        }
        
        # Act
        service = AgentDiscoveryService(mock_storage_service)
        agents = service.discover_agents()
        
        # Assert
        assert len(agents) == 1
        agent = agents[0]
        assert agent.agent_id == "clean_test"  # Set by the service, not from data
        assert agent.name == "Clean Agent"
        # The original data should not be modified (copy is used)
        mock_repository.load_definition.assert_called_once_with("clean_test")

    def test_get_conversation_history_success(self):
        """Test successful retrieval of conversation history."""
        # Setup mock repository
        mock_repository = Mock()
        mock_history = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T00:01:00"}
        ]
        mock_repository.load_history.return_value = mock_history
        
        # Setup mock storage service
        mock_storage_service = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Call method
        result = service.get_conversation_history("test_agent")
        
        # Verify
        mock_repository.load_history.assert_called_once_with("test_agent")
        assert result == mock_history

    def test_clear_conversation_history_success(self):
        """Test successful clearing of conversation history."""
        # Setup mock repository
        mock_repository = Mock()
        mock_repository.get_agent_home_path.return_value = "/test/path/agents/test_agent"
        mock_repository.load_session.return_value = {"conversation_history": ["old_data"]}
        mock_repository.save_session.return_value = True
        
        # Setup mock storage service
        mock_storage_service = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Mock file operations
        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.path.join", return_value="/test/path/agents/test_agent/history.log"):
                # Call method
                result = service.clear_conversation_history("test_agent")
        
        # Verify
        assert result is True
        mock_repository.get_agent_home_path.assert_called_once_with("test_agent")
        mock_file.assert_called_once_with("/test/path/agents/test_agent/history.log", 'w', encoding='utf-8')
        mock_repository.load_session.assert_called_once_with("test_agent")
        mock_repository.save_session.assert_called_once_with("test_agent", {})

    def test_clear_conversation_history_handles_exceptions(self):
        """Test that clear_conversation_history handles exceptions gracefully."""
        # Setup mock repository that raises exception
        mock_repository = Mock()
        mock_repository.get_agent_home_path.side_effect = Exception("File system error")
        
        # Setup mock storage service
        mock_storage_service = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Call method
        result = service.clear_conversation_history("test_agent")
        
        # Verify exception was handled
        assert result is False

    def test_agent_exists_returns_true_when_agent_found(self):
        """Test that agent_exists returns True when agent is found."""
        # Setup mock
        mock_storage_service = Mock()
        mock_repository = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.list_agents.return_value = ["agent1", "agent2"]
        mock_repository.load_definition.side_effect = [
            {"name": "Agent 1", "version": "1.0", "schema_version": "1.0", "description": "Test", "author": "Test"},
            {"name": "Agent 2", "version": "1.0", "schema_version": "1.0", "description": "Test", "author": "Test"}
        ]
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.agent_exists("agent1")
        
        # Verify
        assert result is True

    def test_agent_exists_returns_false_when_agent_not_found(self):
        """Test that agent_exists returns False when agent is not found."""
        # Setup mock
        mock_storage_service = Mock()
        mock_repository = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.list_agents.return_value = ["agent1", "agent2"]
        mock_repository.load_definition.side_effect = [
            {"name": "Agent 1", "version": "1.0", "schema_version": "1.0", "description": "Test", "author": "Test"},
            {"name": "Agent 2", "version": "1.0", "schema_version": "1.0", "description": "Test", "author": "Test"}
        ]
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.agent_exists("nonexistent_agent")
        
        # Verify
        assert result is False

    def test_build_meta_agent_context_with_meta_and_new_agent_id(self):
        """Test building meta agent context with all parameters."""
        # Setup
        mock_storage_service = Mock()
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.build_meta_agent_context(
            "Test message", meta=True, new_agent_id="new_agent"
        )
        
        # Verify
        expected = "NEW_AGENT_ID=new_agent\nAGENT_TYPE=meta\n\nTest message"
        assert result == expected

    def test_build_meta_agent_context_project_type_with_new_agent_id(self):
        """Test building meta agent context for project type with new agent ID."""
        # Setup
        mock_storage_service = Mock()
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.build_meta_agent_context("Test message", meta=False, new_agent_id="new_agent")
        
        # Verify
        expected = "NEW_AGENT_ID=new_agent\nAGENT_TYPE=project\n\nTest message"
        assert result == expected

    def test_build_meta_agent_context_no_context(self):
        """Test building meta agent context with no additional context."""
        # Setup
        mock_storage_service = Mock()
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.build_meta_agent_context("Test message")
        
        # Verify
        assert result == "Test message"

    def test_get_agent_output_scope_with_capabilities(self):
        """Test getting agent output scope from capabilities."""
        # Setup mock
        mock_storage_service = Mock()
        mock_repository = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.load_definition.return_value = {
            "name": "Test Agent",
            "version": "1.0",
            "schema_version": "1.0",
            "description": "Test",
            "author": "Test",
            "capabilities": [{"output_scope": ["file1.py", "file2.py"]}]
        }
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.get_agent_output_scope("test_agent")
        
        # Verify
        assert result == ["file1.py", "file2.py"]

    def test_get_agent_output_scope_no_restrictions(self):
        """Test getting agent output scope when no restrictions exist."""
        # Setup mock
        mock_storage_service = Mock()
        mock_repository = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.load_definition.return_value = {
            "name": "Test Agent",
            "version": "1.0",
            "schema_version": "1.0",
            "description": "Test",
            "author": "Test",
            "capabilities": []
        }
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.get_agent_output_scope("test_agent")
        
        # Verify
        assert result == []

    def test_save_agent_state_success(self):
        """Test successful agent state saving."""
        # Setup mock
        mock_storage_service = Mock()
        mock_repository = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        mock_repository.get_agent_home_path.return_value = "/test/path/agents/test_agent"
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Mock os.makedirs
        with patch("os.makedirs") as mock_makedirs:
            # Test
            result = service.save_agent_state("test_agent")
        
        # Verify
        assert result is True
        mock_repository.get_agent_home_path.assert_called_once_with("test_agent")
        mock_makedirs.assert_called_once_with("/test/path/agents/test_agent", exist_ok=True)

    def test_list_all_agent_definitions_compatibility(self):
        """Test compatibility method for legacy AgentService API."""
        # Setup mock
        mock_storage_service = Mock()
        mock_repository = Mock()
        mock_storage_service.get_repository.return_value = mock_repository
        
        mock_repository.list_agents.return_value = ["agent1"]
        mock_repository.load_definition.return_value = {
            "name": "Test Agent",
            "version": "1.0",
            "schema_version": "1.0",
            "description": "Test",
            "author": "Test"
        }
        
        service = AgentDiscoveryService(mock_storage_service)
        
        # Test
        result = service.list_all_agent_definitions()
        
        # Verify
        assert len(result) == 1
        assert result[0].name == "Test Agent"