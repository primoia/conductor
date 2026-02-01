import os
import yaml
from pathlib import Path
from typing import Dict, Any

from src.config import settings, ConfigManager
from src.core.conductor_service import ConductorService
from src.core.services.configuration_service import ConfigurationService
from src.core.services.storage_service import StorageService
from src.core.services.agent_storage_service import AgentStorageService
from src.core.services.agent_storage_service import AgentStorageService
from src.core.services.agent_discovery_service import AgentDiscoveryService
from src.infrastructure.discovery_service import DiscoveryService
from src.core.services.tool_management_service import ToolManagementService
from src.core.services.task_execution_service import TaskExecutionService
from src.core.services.session_management_service import SessionManagementService
from src.core.exceptions import AgentNotFoundError
from src.ports.state_repository import IStateRepository as StateRepository
from src.ports.llm_client import LLMClient
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository
from src.infrastructure.storage.mongo_observation_repository import MongoObservationRepository
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
        self._observation_repository = None
        self._ai_providers_config = None
        self._conductor_service = None
        self._configuration_service = None
        self._storage_service = None
        self._agent_storage_service = None
        self._agent_discovery_service = None
        self._discovery_service = None
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

    def get_observation_repository(self) -> MongoObservationRepository:
        """Get singleton MongoObservationRepository instance."""
        if self._observation_repository is None:
            self._observation_repository = MongoObservationRepository(
                connection_string=self.settings.mongo_uri,
                db_name=self.settings.mongo_database,
            )
        return self._observation_repository

    def get_llm_client(
        self,
        ai_provider: str,
        working_directory: str = None,
        timeout: int = None,
        is_admin_agent: bool = False,
        mcp_config: str = None,
    ) -> LLMClient:
        """
        Get LLM client instance for the specified provider.

        Args:
            ai_provider: The AI provider to use (e.g., "claude", "gemini")
            working_directory: Working directory for the LLM client
            timeout: Timeout in seconds for long-running operations
            is_admin_agent: Whether this is an admin agent with unrestricted access
            mcp_config: Path to MCP configuration file (only used for Claude CLI)
        """
        if timeout is None:
            timeout = self.settings.default_timeout

        return create_llm_client(
            ai_provider, working_directory, timeout, is_admin_agent, mcp_config
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

    def get_discovery_service(self) -> DiscoveryService:
        """Get singleton DiscoveryService instance."""
        if self._discovery_service is None:
            self._discovery_service = DiscoveryService()
        return self._discovery_service

    def get_tool_management_service(self) -> ToolManagementService:
        """Get singleton ToolManagementService instance."""
        if self._tool_management_service is None:
            config_service = self.get_configuration_service()
            discovery_service = self.get_discovery_service()
            self._tool_management_service = ToolManagementService(config_service, discovery_service)
        return self._tool_management_service

    def get_task_execution_service(self) -> TaskExecutionService:
        """Get singleton TaskExecutionService instance."""
        if self._task_execution_service is None:
            config_service = self.get_configuration_service()
            agent_storage_service = self.get_agent_storage_service()
            tool_service = self.get_tool_management_service()
            discovery_service = self.get_discovery_service()
            self._task_execution_service = TaskExecutionService(
                agent_storage_service, tool_service, config_service, discovery_service, self
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
        """Load AI providers configuration from main config.yaml."""
        if self._ai_providers_config is None:
            # Load from main config.yaml
            config_service = self.get_configuration_service()
            global_config = config_service.get_global_config()
            
            # Extract ai_providers section from the raw config
            # Since GlobalConfig might not have ai_providers, we'll load it directly
            import yaml
            with open("config.yaml", "r", encoding="utf-8") as f:
                main_config = yaml.safe_load(f)
            
            ai_providers_section = main_config.get('ai_providers', {})
            
            if ai_providers_section:
                self._ai_providers_config = ai_providers_section
            else:
                # Default configuration if not found
                self._ai_providers_config = {
                    "default_providers": {"chat": "claude", "generation": "claude"},
                    "fallback_provider": "claude",
                }
        return self._ai_providers_config

    def get_ai_provider(self, agent_definition=None, cli_provider=None) -> str:
        """
        Determina o provider de IA com fallback hierárquico:
        1. CLI parameter (--ai-provider)
        2. Agent definition (ai_provider field)
        3. Config default (ai_providers.yaml)
        4. Fallback: 'claude'
        """
        import traceback
        from src.core.observability import configure_logging
        logger = configure_logging(False, "container", "ai_provider")
        
        logger.info("🔍 [CONTAINER] get_ai_provider chamado com:")
        logger.info(f"   - cli_provider: {cli_provider}")
        logger.info(f"   - agent_definition: {agent_definition}")
        if agent_definition:
            logger.info(f"   - agent_ai_provider: {getattr(agent_definition, 'ai_provider', 'NOT_FOUND')}")
        
        # Capturar stack trace
        stack = traceback.extract_stack()
        caller = stack[-2] if len(stack) > 1 else None
        if caller:
            logger.info(f"   - Chamado por: {caller.filename}:{caller.lineno} em {caller.name}()")
        
        # 1. CLI parameter tem prioridade máxima
        if cli_provider:
            logger.info(f"✅ [CONTAINER] Usando CLI provider: {cli_provider}")
            return cli_provider
        
        # 2. Agent definition
        if agent_definition and hasattr(agent_definition, 'ai_provider') and agent_definition.ai_provider is not None:
            agent_provider = agent_definition.ai_provider
            logger.info(f"✅ [CONTAINER] Usando agent provider: {agent_provider}")
            return agent_provider
        
        # 3. Config default
        config = self.load_ai_providers_config()
        default_providers = config.get('default_providers', {})
        logger.info(f"🔍 [CONTAINER] Config carregado: {config}")
        
        # Para tarefas de geração, usar 'generation', senão 'chat'
        task_type = 'generation'  # Default para geração de código
        if default_providers.get(task_type):
            config_provider = default_providers[task_type]
            logger.info(f"✅ [CONTAINER] Usando config provider ({task_type}): {config_provider}")
            return config_provider
        
        # 4. Fallback
        fallback = config.get('fallback_provider', 'claude')
        logger.info(f"✅ [CONTAINER] Usando fallback provider: {fallback}")
        return fallback




# Global container instance
container = DIContainer()
