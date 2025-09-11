# src/core/services/tool_management_service.py
import importlib
import pkgutil
import sys
import logging
from pathlib import Path
from typing import Dict, Callable, Any, List
from src.core.services.configuration_service import ConfigurationService
from src.core.tools.core_tools import CORE_TOOLS

logger = logging.getLogger(__name__)


class ToolManagementService:
    """Responsável por gerenciar ferramentas e plugins."""

    def __init__(self, config_service: ConfigurationService):
        self._config = config_service
        self._tools: Dict[str, Callable[..., Any]] = {}
        self.load_tools()

    def load_tools(self) -> None:
        """Carrega ferramentas core e plugins."""
        # Carregar Core Tools
        for tool in CORE_TOOLS:
            self._tools[tool.__name__] = tool

        # Carregar Tool Plugins
        self._load_tool_plugins()

    def _load_tool_plugins(self) -> None:
        """Carrega plugins de ferramentas configurados."""
        project_root = Path().resolve()
        
        for plugin_path_str in self._config.get_tool_plugins():
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
            try:
                for finder, name, ispkg in pkgutil.iter_modules([str(plugin_path)]):
                    module = importlib.import_module(f"{plugin_path.name}.{name}")
                    # Assumir que plugins também têm uma lista 'PLUGIN_TOOLS'
                    if hasattr(module, 'PLUGIN_TOOLS'):
                        for tool in module.PLUGIN_TOOLS:
                            self._tools[tool.__name__] = tool
            finally:
                sys.path.pop(0)

    def get_tools(self) -> Dict[str, Callable[..., Any]]:
        """Retorna todas as ferramentas carregadas."""
        return self._tools.copy()

    def get_allowed_tools(self, allowed_tool_names: List[str]) -> Dict[str, Callable[..., Any]]:
        """Filtra e retorna apenas as ferramentas permitidas."""
        return {
            name: tool_func for name, tool_func in self._tools.items()
            if name in allowed_tool_names
        }