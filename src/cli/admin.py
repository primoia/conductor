#!/usr/bin/env python3
"""
Admin CLI - Meta-Agent Management

This CLI provides access to meta-agents for framework management.
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
from src.infrastructure.utils import cleanup_orphan_sessions
from src.cli.shared import (
    REPLManager,
    CLIArgumentParser,
    StateManager,
    DebugUtilities,
    ErrorHandling,
)


class AdminCLI:
    """
    Admin CLI - agora uma casca fina sobre o ConductorService.
    """

    def __init__(
        self,
        agent_id: str,
        ai_provider: str = None,
        timeout: int = 90,
        state_provider: str = "file",
        debug_mode: bool = False,
        meta: bool = False,
        environment: str = None,
        project: str = None,
        new_agent_id: str = None,
        destination_path: str = None,
    ):
        """Initialize Admin CLI."""
        self.logger = configure_logging(debug_mode, f"admin_{agent_id}", agent_id)
        self.debug_mode = debug_mode

        # Store new agent creation parameters
        self.meta = meta
        self.new_agent_id = new_agent_id

        # Set environment and project based on meta flag
        if self.meta:
            self.environment = "_common"
            self.project = "_common"
        else:
            self.environment = environment
            self.project = project

        # Store CLI-specific state (legacy support)
        self.destination_path = destination_path
        self.simulate_mode = False

        # Initialize shared components
        self.state_manager = StateManager(self, self.logger)
        self.debug_utils = DebugUtilities(self, self.logger)

        # Store the target agent_id
        self.agent_id = agent_id
        
        # Get the central service
        self.conductor_service = container.get_conductor_service()
        
        # The "embody" is now implicit in task execution by the service
        print(f"✅ AdminCLI inicializado. Usando ConductorService.")

    @property
    def embodied(self) -> bool:
        """Verifica se o agente alvo existe no ecossistema."""
        try:
            # A nova forma de verificar é ver se o serviço consegue encontrar o agente
            agents = self.conductor_service.discover_agents()
            return any(agent.agent_id == self.agent_id for agent in agents)
        except Exception:
            return False

    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Envia uma mensagem ao agente através do ConductorService."""
        if not self.embodied:
            return f"❌ Agente '{self.agent_id}' não encontrado pelo ConductorService."

        try:
            # Handle debug mode - save input without calling provider
            if debug_save_input:
                enhanced_message = self._build_enhanced_message(message)
                self.debug_utils.save_debug_input(enhanced_message)
                return "✅ DEBUG MODE: Input captured and saved. Provider NOT called."

            # Handle simulation mode
            if self.simulate_mode:
                enhanced_message = self._build_enhanced_message(message)
                return self.debug_utils.generate_simulation_response(enhanced_message)

            # 1. Construir o DTO da tarefa
            # O contexto (meta, new_agent_id) é passado no DTO
            task_context = {
                "meta": self.meta,
                "new_agent_id": self.new_agent_id,
                "debug_save_input": debug_save_input,
                "simulate_mode": self.simulate_mode
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
            self.logger.error(f"Erro no chat do AdminCLI: {e}")
            return f"❌ Erro fatal no AdminCLI: {e}"

    def _build_enhanced_message(self, message: str) -> str:
        """Build enhanced message with agent creation context."""
        context_parts = []

        # Add environment and project context
        if self.environment and self.project:
            context_parts.append(f"AGENT_ENVIRONMENT={self.environment}")
            context_parts.append(f"AGENT_PROJECT={self.project}")

        # Add new agent ID if specified
        if self.new_agent_id:
            context_parts.append(f"NEW_AGENT_ID={self.new_agent_id}")

        # Add meta flag context
        if self.meta:
            context_parts.append("AGENT_TYPE=meta")
        else:
            context_parts.append("AGENT_TYPE=project")

        # Legacy destination path support
        if self.destination_path:
            context_parts.append(f"DESTINATION_PATH={self.destination_path}")
            self.logger.info(
                f"Enhanced message with destination path: {self.destination_path}"
            )

        # Build final message
        if context_parts:
            context_header = "\n".join(context_parts)
            enhanced_message = f"{context_header}\n\n{message}"
            self.logger.info(
                f"Enhanced message with context: {len(context_parts)} context items"
            )
            return enhanced_message
        else:
            return message

    def save_agent_state(self):
        """Save agent state using StateManager."""
        return self.state_manager.save_agent_state()

    def get_available_tools(self) -> list:
        """Get available tools from ConductorService."""
        try:
            # Get the tools available through the service
            # This might need to be adapted based on the actual ConductorService interface
            return list(self.conductor_service._tools.keys())
        except Exception as e:
            self.logger.error(f"Error getting available tools: {e}")
            return []


def start_repl_session(admin_cli: AdminCLI):
    """Start interactive REPL session using REPLManager."""
    repl_manager = REPLManager("admin", admin_cli)

    # Add admin-specific custom command
    repl_manager.add_custom_command(
        "export-debug", lambda: admin_cli.debug_utils.export_debug_report()
    )

    custom_help = "🔍 Digite 'debug' para ver contexto completo\n🔍 Digite 'export-debug' para exportar relatório de debug"
    repl_manager.start_session(custom_help)


@ErrorHandling.handle_cli_exceptions
def main():
    """Main function for admin CLI."""
    # Validate environment first
    if not ErrorHandling.validate_environment():
        sys.exit(1)

    if not ErrorHandling.check_permissions():
        sys.exit(1)

    # Execute cleanup for filesystem storage backend
    try:
        config_manager = container.config_manager
        storage_config = config_manager.load_storage_config()
        
        if storage_config.get('type') == 'filesystem':
            workspace_path = storage_config.get('workspace_path')
            if workspace_path:
                cleanup_orphan_sessions(workspace_path)
    except Exception as e:
        print(f"⚠️  Warning: Failed to execute session cleanup: {e}")

    # Use shared argument parser
    parser = CLIArgumentParser.create_admin_parser()
    args = parser.parse_args()

    # Validate arguments
    if not CLIArgumentParser.validate_admin_args(args):
        sys.exit(1)

    if args.simulate_chat:
        print(
            """
🎭 MODO SIMULAÇÃO ATIVADO

Este modo permite simular conversas sem chamar o provider real,
mantendo o contexto da conversa para análise.
"""
        )

    print(f"🚀 Iniciando Admin CLI")
    print(f"   Meta-agent: {args.agent}")
    if args.meta:
        print(f"   Agent Type: meta-agent")
        print(f"   Target: _common/agents/")
    else:
        print(f"   Agent Type: project-agent")
        print(f"   Environment: {args.environment}")
        print(f"   Project: {args.project}")

    if args.new_agent_id:
        print(f"   New Agent ID: {args.new_agent_id}")
    else:
        print(f"   New Agent ID: will suggest name")

    if args.debug:
        print(f"   Debug mode: enabled")

    # Initialize admin CLI with new parameters
    admin_cli = AdminCLI(
        agent_id=args.agent,
        ai_provider=args.ai_provider,
        timeout=args.timeout,
        state_provider=args.state_provider,
        debug_mode=args.debug,
        meta=args.meta,
        environment=args.environment,
        project=args.project,
        new_agent_id=args.new_agent_id,
        destination_path=args.destination_path,
    )

    if not admin_cli.embodied:
        print(f"❌ Failed to embody meta-agent: {args.agent}")
        sys.exit(1)

    # Configure simulation mode
    if args.simulate_chat:
        admin_cli.simulate_mode = True
        print(f"🎭 Modo simulação ativado")

    print(f"🔓 No output restrictions (meta-agent)")

    # Handle different execution modes
    if args.repl:
        start_repl_session(admin_cli)
    elif args.input:
        print(f"\n🤖 Processing input for {args.agent}:")
        print(f"📝 Input: {args.input}")
        print("-" * 60)

        response = admin_cli.chat(args.input, debug_save_input=args.debug_input)
        print("\n📄 Response:")
        print("=" * 60)
        print(response)
        print("=" * 60)

        admin_cli.save_agent_state()
    else:
        ErrorHandling.show_usage_tip(parser)
        print("🤖 Meta-agent ready for programmatic use")

    print("\n👋 Admin CLI session completed")


if __name__ == "__main__":
    main()
