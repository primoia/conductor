"""
Tests for dependency injection container.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from src.container import DIContainer
from src.infrastructure.persistence.state_repository import FileStateRepository
from src.infrastructure.llm.cli_client import ClaudeCLIClient


class TestDIContainer:
    """Test cases for DIContainer."""
    
    def setup_method(self):
        """Setup for each test."""
        self.container = DIContainer()
    
    def test_get_file_state_repository(self):
        """Test getting file state repository."""
        repo = self.container.get_state_repository('file')
        assert isinstance(repo, FileStateRepository)
    
    def test_get_llm_client(self):
        """Test getting LLM client."""
        client = self.container.get_llm_client('claude', '/test/dir', 60)
        assert isinstance(client, ClaudeCLIClient)
        assert client.timeout == 60
    
    def test_create_agent_logic(self):
        """Test creating agent logic with dependencies."""
        agent_logic = self.container.create_agent_logic(
            state_provider='file',
            ai_provider='claude'
        )
        
        assert agent_logic is not None
        assert hasattr(agent_logic, 'state_repository')
        assert hasattr(agent_logic, 'llm_client')
    
    def test_load_default_ai_providers_config(self):
        """Test loading default AI providers config."""
        config = self.container.load_ai_providers_config()
        
        assert 'default_providers' in config
        assert 'fallback_provider' in config
        assert config['default_providers']['chat'] == 'gemini'
        assert config['fallback_provider'] == 'claude'
    
    @patch('pathlib.Path.exists')
    def test_load_workspaces_config_missing_file(self, mock_exists):
        """Test loading workspaces config with missing file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            self.container.load_workspaces_config()
    
    def test_resolve_agent_paths_common(self):
        """Test resolving paths for common/meta agents."""
        # This will fail in real execution due to missing directories
        # but tests the path construction logic
        from src.core.exceptions import AgentNotFoundError
        with pytest.raises((FileNotFoundError, AgentNotFoundError)):
            self.container.resolve_agent_paths("_common", "_common", "TestAgent")


if __name__ == '__main__':
    pytest.main([__file__])