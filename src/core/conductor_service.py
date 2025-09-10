# src/core/conductor_service.py
import yaml
import importlib
import pkgutil
import sys
import logging
from pathlib import Path
from typing import List, Dict, Callable, Any
from src.ports.conductor_service import IConductorService
from src.ports.state_repository import IStateRepository
from src.core.config_schema import GlobalConfig, StorageConfig
from src.core.exceptions import ConfigurationError
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository
from src.core.domain import AgentDefinition, TaskDTO, TaskResultDTO
from src.core.tools.core_tools import CORE_TOOLS
from src.core.agent_executor import AgentExecutor, PlaceholderLLMClient
from src.core.prompt_engine import PromptEngine

logger = logging.getLogger(__name__)


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
            return FileSystemStateRepository(base_path=getattr(storage_config, 'path', None))
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
                # Remove agent_id from definition before creating AgentDefinition
                definition_data = state["definition"].copy()
                definition_data.pop("agent_id", None)  # Remove agent_id if present
                # Add agent_id as optional parameter
                agent_definition = AgentDefinition(**definition_data, agent_id=agent_id)
                definitions.append(agent_definition)
        return definitions

    def execute_task(self, task: TaskDTO) -> TaskResultDTO:
        try:
            # 1. Carregar o estado completo do agente
            agent_state = self.repository.load_state(task.agent_id)
            if not agent_state or "definition" not in agent_state:
                raise FileNotFoundError(f"Definição não encontrada para o agente: {task.agent_id}")

            # Remove agent_id from definition before creating AgentDefinition
            definition_data = agent_state["definition"].copy()
            definition_data.pop("agent_id", None)  # Remove agent_id if present
            agent_definition = AgentDefinition(**definition_data)
            
            # 2. Obter o caminho do agente (assumindo que está no estado)
            agent_home_path = agent_state.get("agent_home_path")
            if not agent_home_path:
                raise ValueError(f"agent_home_path não encontrado no estado do agente {task.agent_id}")

            # 3. Instanciar as dependências de execução
            #    (Usando placeholders por enquanto)
            llm_client = PlaceholderLLMClient() 
            prompt_engine = PromptEngine(agent_home_path=agent_home_path)
            prompt_engine.load_context()
            
            # 4. Filtrar as ferramentas permitidas
            allowed_tools = {
                name: tool_func for name, tool_func in self._tools.items()
                if name in agent_state.get("allowed_tools", [])
            }

            # 5. Instanciar e executar o executor
            executor = AgentExecutor(
                agent_definition=agent_definition,
                llm_client=llm_client,
                prompt_engine=prompt_engine,
                allowed_tools=allowed_tools
            )
            
            result = executor.run(task)
            return result

        except Exception as e:
            return TaskResultDTO(status="error", output=str(e), metadata={})

    def load_tools(self) -> None:
        # Carregar Core Tools
        for tool in CORE_TOOLS:
            self._tools[tool.__name__] = tool

        # Carregar Tool Plugins
        project_root = Path().resolve()
        for plugin_path_str in self._config.tool_plugins:
            plugin_path = Path(plugin_path_str).resolve()

            # Medida de Segurança: Prevenção de Path Traversal
            if project_root not in plugin_path.parents:
                logger.error(
                    f"Recusando carregar plugin de diretório não confiável: {plugin_path}. "
                    f"O caminho do plugin deve estar dentro do diretório do projeto."
                )
                continue
            
            if not plugin_path.is_dir():
                logger.warning(f"Caminho do plugin não é um diretório: {plugin_path}")
                continue
            
            logger.warning(f"Carregando plugins do diretório externo: {plugin_path}")
            
            # Adicionar ao path e importar módulos
            sys.path.insert(0, str(plugin_path.parent))
            for finder, name, ispkg in pkgutil.iter_modules([str(plugin_path)]):
                module = importlib.import_module(f"{plugin_path.name}.{name}")
                # Assumir que plugins também têm uma lista 'PLUGIN_TOOLS'
                if hasattr(module, 'PLUGIN_TOOLS'):
                    for tool in module.PLUGIN_TOOLS:
                        self._tools[tool.__name__] = tool
            sys.path.pop(0)