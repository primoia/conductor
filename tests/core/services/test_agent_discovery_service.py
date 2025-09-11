# tests/core/services/test_agent_discovery_service.py
import pytest
from unittest.mock import MagicMock

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