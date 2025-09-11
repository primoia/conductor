"""
Tests for dependency injection container.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from src.container import DIContainer
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.llm.cli_client import ClaudeCLIClient


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



if __name__ == "__main__":
    pytest.main([__file__])
