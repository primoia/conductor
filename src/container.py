import os
import yaml
from pathlib import Path
from typing import Dict, Any

from src.config import settings, ConfigManager
from src.core.conductor_service import ConductorService
from src.core.services.configuration_service import ConfigurationService
from src.core.services.storage_service import StorageService
from src.core.services.agent_storage_service import AgentStorageService
from src.core.services.agent_discovery_service import AgentDiscoveryService
from src.core.services.tool_management_service import ToolManagementService
from src.core.services.task_execution_service import TaskExecutionService
from src.core.services.session_management_service import SessionManagementService
from src.core.exceptions import AgentNotFoundError
from src.ports.state_repository import IStateRepository as StateRepository
from src.ports.llm_client import LLMClient
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository
from src.infrastructure.llm.cli_client import create_llm_client
from src.infrastructure.repository_factory import RepositoryFactory


class DIContainer:
    """
    Dependency Injection Container for the Conductor framework.

    This container is responsible for:
    1. Reading configuration
    2. Instantiating concrete adapters
    3. Connecting all dependencies
    4. Providing ready-to-use service instances
    """

    def __init__(self):
        self.settings = settings
        self.config_manager = ConfigManager()
        self._state_repository = None
        self._ai_providers_config = None
        self._conductor_service = None
        self._configuration_service = None
        self._storage_service = None
        self._agent_storage_service = None
        self._agent_discovery_service = None
        self._tool_management_service = None
        self._task_execution_service = None
        self._session_management_service = None

    def get_state_repository(self, provider: str = "file") -> StateRepository:
        """Get state repository instance based on provider."""
        if provider == "mongo":
            return MongoStateRepository(
                connection_string=self.settings.mongo_uri,
                db_name=self.settings.mongo_database,
            )
        else:
            return FileSystemStateRepository()

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


    def get_configuration_service(self, config_path: str = "config.yaml") -> ConfigurationService:
        """Get singleton ConfigurationService instance."""
        if self._configuration_service is None:
            self._configuration_service = ConfigurationService(config_path)
        return self._configuration_service

    def get_storage_service(self) -> StorageService:
        """Get singleton StorageService instance."""
        if self._storage_service is None:
            config_service = self.get_configuration_service()
            self._storage_service = StorageService(config_service)
        return self._storage_service

    def get_agent_storage_service(self) -> AgentStorageService:
        """Get singleton AgentStorageService instance."""
        if self._agent_storage_service is None:
            config_service = self.get_configuration_service()
            self._agent_storage_service = AgentStorageService(config_service)
        return self._agent_storage_service

    def get_agent_discovery_service(self) -> AgentDiscoveryService:
        """Get singleton AgentDiscoveryService instance."""
        if self._agent_discovery_service is None:
            storage_service = self.get_storage_service()
            self._agent_discovery_service = AgentDiscoveryService(storage_service)
        return self._agent_discovery_service

    def get_tool_management_service(self) -> ToolManagementService:
        """Get singleton ToolManagementService instance."""
        if self._tool_management_service is None:
            config_service = self.get_configuration_service()
            self._tool_management_service = ToolManagementService(config_service)
        return self._tool_management_service

    def get_task_execution_service(self) -> TaskExecutionService:
        """Get singleton TaskExecutionService instance."""
        if self._task_execution_service is None:
            config_service = self.get_configuration_service()
            agent_storage_service = self.get_agent_storage_service()
            tool_service = self.get_tool_management_service()
            self._task_execution_service = TaskExecutionService(
                agent_storage_service, tool_service, config_service
            )
        return self._task_execution_service

    def get_session_management_service(self) -> SessionManagementService:
        """Get singleton SessionManagementService instance."""
        if self._session_management_service is None:
            config_service = self.get_configuration_service()
            self._session_management_service = SessionManagementService(config_service)
        return self._session_management_service

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
