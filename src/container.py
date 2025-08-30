import os
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple

from src.config import settings
from src.core.agent_logic import AgentLogic
from src.core.exceptions import AgentNotFoundError
from src.ports.state_repository import StateRepository
from src.ports.llm_client import LLMClient
from src.infrastructure.persistence.state_repository import FileStateRepository, MongoStateRepository
from src.infrastructure.llm.cli_client import create_llm_client


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
        self._state_repository = None
        self._ai_providers_config = None
    
    def get_state_repository(self, provider: str = 'file') -> StateRepository:
        """Get state repository instance based on provider."""
        if provider == 'mongo':
            return MongoStateRepository(
                database_name=self.settings.mongo_database,
                collection_name=self.settings.mongo_collection
            )
        else:
            return FileStateRepository()
    
    def get_llm_client(self, ai_provider: str, working_directory: str = None, 
                      timeout: int = None) -> LLMClient:
        """Get LLM client instance for the specified provider."""
        if timeout is None:
            timeout = self.settings.default_timeout
        
        return create_llm_client(ai_provider, working_directory, timeout)
    
    def create_agent_logic(self, state_provider: str = 'file', 
                          ai_provider: str = 'claude',
                          working_directory: str = None,
                          timeout: int = None) -> AgentLogic:
        """
        Create a fully configured AgentLogic instance.
        
        Args:
            state_provider: State persistence provider ('file' or 'mongo')
            ai_provider: AI provider ('claude' or 'gemini')
            working_directory: Working directory for the LLM client
            timeout: Timeout for LLM operations
            
        Returns:
            Configured AgentLogic instance with injected dependencies
        """
        # Get dependencies
        state_repository = self.get_state_repository(state_provider)
        llm_client = self.get_llm_client(ai_provider, working_directory, timeout)
        
        # Create and return AgentLogic with injected dependencies
        return AgentLogic(state_repository, llm_client)
    
    def load_ai_providers_config(self) -> Dict[str, Any]:
        """Load AI providers configuration."""
        if self._ai_providers_config is None:
            config_path = Path("config") / "ai_providers.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._ai_providers_config = yaml.safe_load(f)
            else:
                # Default configuration
                self._ai_providers_config = {
                    'default_providers': {
                        'chat': 'claude',
                        'generation': 'claude'
                    },
                    'fallback_provider': 'claude'
                }
        return self._ai_providers_config
    
    def load_workspaces_config(self) -> Dict[str, str]:
        """Load workspaces configuration."""
        config_path = Path("config") / "workspaces.yaml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Workspaces config not found: {config_path}\n"
                "Create the file with environment to directory mappings."
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'workspaces' not in config:
            raise ValueError("workspaces.yaml must contain a 'workspaces' section")
        
        return config['workspaces']
    
    def resolve_agent_paths(self, environment: str, project: str, agent_id: str) -> Tuple[Path, Path]:
        """
        Resolve agent and project paths based on environment.
        
        Args:
            environment: Environment name (develop, main, _common)
            project: Project name  
            agent_id: Agent identifier
            
        Returns:
            Tuple of (agent_home_path, project_root_path)
        """
        conductor_root = Path(__file__).parent.parent
        
        if environment == "_common":
            # Meta-agents are in projects/_common/agents/
            agent_home_path = conductor_root / "projects" / "_common" / "agents" / agent_id
            project_root_path = conductor_root.parent.parent  # Monorepo root
        else:
            # Project agents
            workspaces = self.load_workspaces_config()
            workspace_root = Path(workspaces[environment])
            project_root_path = workspace_root / project
            agent_home_path = conductor_root / "projects" / environment / project / "agents" / agent_id
        
        if not agent_home_path.exists():
            raise AgentNotFoundError(f"Agent home path does not exist: {agent_home_path}")
        
        return agent_home_path.resolve(), project_root_path.resolve()


# Global container instance
container = DIContainer()