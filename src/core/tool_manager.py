# src/core/tool_manager.py

import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Callable

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, function: Callable):
        if name in self.tools:
            print(f"Aviso: A ferramenta '{name}' está sendo sobrescrita.")
        self.tools[name] = function

    def load_plugins_from_config(self, config: Dict):
        """
        Escaneia diretórios de plugins definidos na configuração, carrega os módulos
        e registra as funções marcadas com @tool.
        """
        plugin_paths = config.get('tool_plugins', [])
        for path_str in plugin_paths:
            self._load_from_directory(Path(path_str))

    def _load_from_directory(self, dir_path: Path):
        """Carrega ferramentas de todos os arquivos .py em um diretório."""
        for file_path in dir_path.glob("*.py"):
            self._load_from_file(file_path)
            
    def _load_from_file(self, file_path: Path):
        """Carrega um módulo Python e registra suas ferramentas."""
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, func in inspect.getmembers(module, inspect.isfunction):
                if getattr(func, '_is_tool', False):
                    self.register_tool(func.__name__, func)
        except Exception as e:
            print(f"Erro ao carregar o plugin '{file_path}': {e}")