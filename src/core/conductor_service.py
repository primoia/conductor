# src/core/conductor_service.py
import yaml
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import List, Dict, Callable, Any
from src.ports.conductor_service import IConductorService
from src.ports.state_repository import IStateRepository
from src.core.config_schema import GlobalConfig, StorageConfig
from src.core.exceptions import ConfigurationError
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository
from src.core.domain import AgentDefinition
from src.core.tools.core_tools import CORE_TOOLS


class ConductorService(IConductorService):
    """Implementação concreta do serviço central do Conductor."""

    def __init__(self, config_path: str = "config.yaml"):
        self._config = self._load_and_validate_config(config_path)
        self.repository = self._create_storage_backend(self._config.storage)
        self._tools: Dict[str, Callable[..., Any]] = {}
        self.load_tools()

    def _load_and_validate_config(self, config_path: str) -> GlobalConfig:
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return GlobalConfig(**config_data)
        except FileNotFoundError:
            raise ConfigurationError(f"Arquivo de configuração não encontrado em: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Erro ao carregar ou validar a configuração: {e}")

    def _create_storage_backend(self, storage_config: StorageConfig) -> IStateRepository:
        if storage_config.type == "filesystem":
            return FileSystemStateRepository()
        elif storage_config.type == "mongodb":
            return MongoStateRepository()
        else:
            raise ConfigurationError(f"Tipo de armazenamento desconhecido: {storage_config.type}")

    def discover_agents(self) -> List[AgentDefinition]:
        agent_ids = self.repository.list_agents()
        definitions = []
        for agent_id in agent_ids:
            state = self.repository.load_state(agent_id)
            if "definition" in state:
                # Assumindo que a 'definition' no estado corresponde aos campos do DTO
                definitions.append(AgentDefinition(**state["definition"]))
        return definitions

    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        raise NotImplementedError

    def load_tools(self) -> None:
        # Carregar Core Tools
        for tool in CORE_TOOLS:
            self._tools[tool.__name__] = tool

        # Carregar Tool Plugins
        for plugin_path_str in self._config.tool_plugins:
            plugin_path = Path(plugin_path_str).resolve()
            if not plugin_path.is_dir():
                print(f"Aviso: Caminho do plugin não é um diretório: {plugin_path}")
                continue
            
            # Adicionar ao path e importar módulos
            sys.path.insert(0, str(plugin_path.parent))
            for finder, name, ispkg in pkgutil.iter_modules([str(plugin_path)]):
                module = importlib.import_module(f"{plugin_path.name}.{name}")
                # Assumir que plugins também têm uma lista 'PLUGIN_TOOLS'
                if hasattr(module, 'PLUGIN_TOOLS'):
                    for tool in module.PLUGIN_TOOLS:
                        self._tools[tool.__name__] = tool
            sys.path.pop(0)