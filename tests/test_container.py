"""
Tests for dependency injection container.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from src.container import DIContainer
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.llm.cli_client import ClaudeCLIClient
from src.core.services.configuration_service import ConfigurationService
from src.core.services.storage_service import StorageService
from src.core.services.agent_discovery_service import AgentDiscoveryService
from src.core.services.tool_management_service import ToolManagementService
from src.core.services.task_execution_service import TaskExecutionService
from src.core.services.session_management_service import SessionManagementService
from src.core.conductor_service import ConductorService


class TestDIContainer:
    """Test cases for DIContainer."""

    def setup_method(self):
        """Setup for each test."""
        self.container = DIContainer()

    def test_get_file_state_repository(self):
        """Test getting file state repository."""
        repo = self.container.get_state_repository("file")
        assert isinstance(repo, FileSystemStateRepository)

    def test_get_llm_client(self):
        """Test getting LLM client."""
        client = self.container.get_llm_client("claude", "/test/dir", 60)
        assert isinstance(client, ClaudeCLIClient)
        assert client.timeout == 60


    def test_load_default_ai_providers_config(self):
        """Test loading default AI providers config."""
        config = self.container.load_ai_providers_config()

        assert "default_providers" in config
        assert "fallback_provider" in config
        assert config["default_providers"]["chat"] == "gemini"
        assert config["fallback_provider"] == "claude"

    def test_get_configuration_service_singleton(self):
        """Test that ConfigurationService is singleton."""
        service1 = self.container.get_configuration_service()
        service2 = self.container.get_configuration_service()
        
        assert isinstance(service1, ConfigurationService)
        assert service1 is service2  # Same instance

    def test_get_storage_service_singleton(self):
        """Test that StorageService is singleton."""
        service1 = self.container.get_storage_service()
        service2 = self.container.get_storage_service()
        
        assert isinstance(service1, StorageService)
        assert service1 is service2  # Same instance

    def test_get_agent_discovery_service_singleton(self):
        """Test that AgentDiscoveryService is singleton."""
        service1 = self.container.get_agent_discovery_service()
        service2 = self.container.get_agent_discovery_service()
        
        assert isinstance(service1, AgentDiscoveryService)
        assert service1 is service2  # Same instance

    def test_get_session_management_service_singleton(self):
        """Test that SessionManagementService is singleton."""
        service1 = self.container.get_session_management_service()
        service2 = self.container.get_session_management_service()
        
        assert isinstance(service1, SessionManagementService)
        assert service1 is service2  # Same instance

    def test_get_conductor_service_singleton(self):
        """Test that ConductorService is singleton."""
        service1 = self.container.get_conductor_service()
        service2 = self.container.get_conductor_service()
        
        assert isinstance(service1, ConductorService)
        assert service1 is service2  # Same instance

    def test_service_dependency_injection(self):
        """Test that services receive correct dependencies."""
        storage_service = self.container.get_storage_service()
        agent_service = self.container.get_agent_discovery_service()
        
        # AgentDiscoveryService should have StorageService as dependency
        assert hasattr(agent_service, '_storage')
        
        # Both should be properly configured
        assert isinstance(storage_service, StorageService)
        assert isinstance(agent_service, AgentDiscoveryService)



if __name__ == "__main__":
    pytest.main([__file__])
