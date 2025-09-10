import os
import yaml
from pathlib import Path
from typing import Dict, Any

from src.config import settings, ConfigManager
from src.core.agent_logic import AgentLogic
from src.core.agent_service import AgentService
from src.core.conductor_service import ConductorService
from src.core.exceptions import AgentNotFoundError
from src.ports.state_repository import IStateRepository as StateRepository
from src.ports.llm_client import LLMClient
from src.infrastructure.persistence.state_repository import (
    FileStateRepository,
    MongoStateRepository,
)
from src.infrastructure.llm.cli_client import create_llm_client
from src.infrastructure.repository_factory import RepositoryFactory


class DIContainer:
    """
    Dependency Injection Container for the Conductor framework.

    This container is responsible for:
    1. Reading configuration
    2. Instantiating concrete adapters
    3. Connecting all dependencies
    4. Providing ready-to-use AgentLogic instances
    """

    def __init__(self):
        self.settings = settings
        self.config_manager = ConfigManager()
        self._state_repository = None
        self._ai_providers_config = None
        self._conductor_service = None

    def get_state_repository(self, provider: str = "file") -> StateRepository:
        """Get state repository instance based on provider."""
        if provider == "mongo":
            return MongoStateRepository(
                database_name=self.settings.mongo_database,
                collection_name=self.settings.mongo_collection,
            )
        else:
            return FileStateRepository()

    def get_llm_client(
        self,
        ai_provider: str,
        working_directory: str = None,
        timeout: int = None,
        is_admin_agent: bool = False,
    ) -> LLMClient:
        """Get LLM client instance for the specified provider."""
        if timeout is None:
            timeout = self.settings.default_timeout

        return create_llm_client(
            ai_provider, working_directory, timeout, is_admin_agent
        )

    def create_agent_logic(
        self,
        state_provider: str = "file",
        ai_provider: str = "claude",
        working_directory: str = None,
        timeout: int = None,
        is_admin_agent: bool = False,
    ) -> AgentLogic:
        """
        Create a fully configured AgentLogic instance.

        Args:
            state_provider: State persistence provider ('file' or 'mongo')
            ai_provider: AI provider ('claude' or 'gemini')
            working_directory: Working directory for the LLM client
            timeout: Timeout for LLM operations
            is_admin_agent: Whether this is an admin agent (gets unrestricted access)

        Returns:
            Configured AgentLogic instance with injected dependencies
        """
        # Get dependencies
        state_repository = self.get_state_repository(state_provider)
        llm_client = self.get_llm_client(
            ai_provider, working_directory, timeout, is_admin_agent
        )

        # Create and return AgentLogic with injected dependencies
        return AgentLogic(state_repository, llm_client)

    def create_agent_service(self) -> AgentService:
        """
        Create a fully configured AgentService instance using the repository factory.
        
        Returns:
            Configured AgentService instance with the appropriate storage backend
        """
        # Load storage configuration from config.yaml
        storage_config = self.config_manager.load_storage_config()
        
        # Use RepositoryFactory to create the appropriate repository
        storage_repository = RepositoryFactory.get_repository(storage_config)
        
        # Create and return AgentService with injected repository
        return AgentService(storage_repository)

    def get_conductor_service(self) -> ConductorService:
        """
        Get a singleton instance of ConductorService.
        
        Returns:
            Singleton ConductorService instance
        """
        if self._conductor_service is None:
            self._conductor_service = ConductorService()
        return self._conductor_service

    def load_ai_providers_config(self) -> Dict[str, Any]:
        """Load AI providers configuration."""
        if self._ai_providers_config is None:
            config_path = Path("config") / "ai_providers.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    self._ai_providers_config = yaml.safe_load(f)
            else:
                # Default configuration
                self._ai_providers_config = {
                    "default_providers": {"chat": "claude", "generation": "claude"},
                    "fallback_provider": "claude",
                }
        return self._ai_providers_config




# Global container instance
container = DIContainer()
