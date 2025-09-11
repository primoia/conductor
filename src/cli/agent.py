#!/usr/bin/env python3
"""
Agent CLI - Project Agent Management

This CLI provides access to project-specific agents.
It acts as a thin interface that delegates to the core business logic.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Also add src to path as fallback
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.container import container
from src.core.observability import configure_logging
from src.core.domain import TaskDTO
from src.cli.shared import (
    REPLManager,
    CLIArgumentParser,
    StateManager,
    DebugUtilities,
    ErrorHandling,
)


class AgentCLI:
    """
    Agent CLI - agora uma casca fina sobre o ConductorService.
    """

    def __init__(
        self,
        environment: str,
        project: str,
        agent_id: str,
        ai_provider: str = None,
        timeout: int = 120,
        state_provider: str = "file",
        debug_mode: bool = False,
    ):
        """Initialize Agent CLI."""
        self.logger = configure_logging(debug_mode, f"agent_{agent_id}", agent_id)
        self.debug_mode = debug_mode
        self.agent_id = agent_id
        self.environment = environment
        self.project = project
        
        # Initialize shared components
        self.state_manager = StateManager(self, self.logger)
        self.debug_utils = DebugUtilities(self, self.logger)
        
        # Get the central service
        self.conductor_service = container.get_conductor_service()
        
        # Get specialized services for specific operations
        from src.core.services.storage_service import StorageService
        from src.core.services.configuration_service import ConfigurationService
        from src.core.services.agent_discovery_service import AgentDiscoveryService
        
        config_service = ConfigurationService()
        storage_service = StorageService(config_service)
        self.agent_service = AgentDiscoveryService(storage_service)
        
        print(f"✅ AgentCLI inicializado. Usando ConductorService + AgentService.")


    @property
    def embodied(self) -> bool:
        """Verifica se o agente alvo existe no ecossistema."""
        return self.agent_service.agent_exists(self.agent_id)

    def chat(self, message: str) -> str:
        """Envia uma mensagem ao agente através do ConductorService."""
        if not self.embodied:
            return f"❌ Agente '{self.agent_id}' não encontrado pelo ConductorService."

        try:
            # 1. Construir o DTO da tarefa
            task_context = {
                "environment": self.environment,
                "project": self.project
            }
            task = TaskDTO(
                agent_id=self.agent_id,
                user_input=message,
                context=task_context
            )

            # 2. Delegar a execução para o serviço central
            result = self.conductor_service.execute_task(task)

            # 3. Processar o resultado
            if result.status == "success":
                return result.output
            else:
                return f"❌ Erro na execução da tarefa: {result.output}"

        except Exception as e:
            self.logger.error(f"Erro no chat do AgentCLI: {e}")
            return f"❌ Erro fatal no AgentCLI: {e}"

    def save_agent_state(self):
        """Save agent state using AgentService."""
        return self.agent_service.save_agent_state(self.agent_id)

    def get_available_tools(self) -> list:
        """Get available tools from agent definition."""
        try:
            agent_definition = self.agent_service.get_agent_definition(self.agent_id)
            return agent_definition.allowed_tools if agent_definition else []
        except Exception:
            return []

    def get_output_scope(self) -> list:
        """Get output scope restrictions from agent definition."""
        return self.agent_service.get_agent_output_scope(self.agent_id)


def start_repl_session(agent_cli: AgentCLI, agent_name: str):
    """Start interactive REPL session using REPLManager."""
    repl_manager = REPLManager(agent_name, agent_cli)
    repl_manager.start_session()


@ErrorHandling.handle_cli_exceptions
def main():
    """Main function for agent CLI."""
    # Validate environment first
    if not ErrorHandling.validate_environment():
        sys.exit(1)

    if not ErrorHandling.check_permissions():
        sys.exit(1)

    # Use shared argument parser
    parser = CLIArgumentParser.create_agent_parser()
    args = parser.parse_args()

    print(f"🚀 Iniciando Agent CLI")
    print(f"   Environment: {args.environment}")
    print(f"   Project: {args.project}")
    print(f"   Agent: {args.agent}")
    if args.debug:
        print(f"   Debug mode: enabled")

    # Initialize agent CLI
    agent_cli = AgentCLI(
        environment=args.environment,
        project=args.project,
        agent_id=args.agent,
        ai_provider=args.ai_provider,
        timeout=args.timeout,
        state_provider=args.state_provider,
        debug_mode=args.debug,
    )

    if not agent_cli.embodied:
        print(f"❌ Agente não encontrado no ecossistema: {args.agent}")
        sys.exit(1)

    # Show output scope if restricted
    scope = agent_cli.get_output_scope()
    if scope:
        print(f"🎯 Output scope: {', '.join(scope)}")
    else:
        print(f"🔓 No output restrictions")

    # Handle different execution modes
    if args.repl:
        start_repl_session(agent_cli, args.agent)
    elif args.input:
        print(f"\n🤖 Processing input for {args.agent}:")
        print(f"📝 Input: {args.input}")
        print("-" * 60)

        response = agent_cli.chat(args.input)
        print("\n📄 Response:")
        print("=" * 60)
        print(response)
        print("=" * 60)

        agent_cli.save_agent_state()
    else:
        ErrorHandling.show_usage_tip(parser)
        print("🤖 Agent ready for programmatic use")

    print("\n👋 Agent CLI session completed")


if __name__ == "__main__":
    main()
