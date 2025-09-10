# src/core/tool_executor.py

from typing import Dict, Callable

class SecurityViolationError(Exception):
    pass

class ToolExecutor:
    def __init__(self, tool_manager, config: Dict):
        self.tools: Dict[str, Callable] = tool_manager.tools
        self.config: Dict = config.get('tool_config', {})

    def execute(self, tool_name: str, **kwargs):
        """
        Executa uma ferramenta após verificar as políticas de segurança.
        """
        if tool_name not in self.tools:
            raise ValueError(f"Ferramenta '{tool_name}' não encontrada.")

        # Aplicar política de segurança específica para 'shell_run'
        if tool_name == 'shell_run':
            self._enforce_shell_policy(kwargs.get('command'))

        tool_func = self.tools[tool_name]
        return tool_func(**kwargs)

    def _enforce_shell_policy(self, command: str):
        """Verifica se o comando de shell é permitido pela política."""
        policy = self.config.get('shell_run', {})
        allowed = policy.get('allowed_commands')

        if allowed is None: # Se a chave 'allowed_commands' não existe, nada é permitido.
            raise SecurityViolationError("Execução de 'shell_run' não é permitida. Nenhuma 'allowed_commands' definida na política.")
        
        # O comando real pode ter argumentos (ex: "ls -la"). Verificamos o comando base.
        command_base = command.split()[0]
        if command_base not in allowed:
            raise SecurityViolationError(
                f"Comando de shell '{command_base}' não é permitido pela política de segurança."
            )