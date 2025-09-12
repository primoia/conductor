#!/usr/bin/env python3
"""
Admin CLI - Meta-Agent Management

This CLI provides access to meta-agents for framework management.
It acts as a thin interface that delegates to the core business logic.
"""

import sys
import os
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
        new_agent_id: str = None,
    ):
        """Initialize Admin CLI."""
        self.logger = configure_logging(debug_mode, f"admin_{agent_id}", agent_id)
        self.debug_mode = debug_mode

        # Store new agent creation parameters
        self.meta = meta
        self.new_agent_id = new_agent_id

        # Store CLI-specific state
        self.simulate_mode = False

        # Initialize shared components
        self.state_manager = StateManager(self, self.logger)
        self.debug_utils = DebugUtilities(self, self.logger)

        # Store the target agent_id
        self.agent_id = agent_id
        
        # Get services from container (properly configured and singleton)
        self.conductor_service = container.get_conductor_service()
        self.agent_service = container.get_agent_discovery_service()
        
        # The "embody" is now implicit in task execution by the service
        print(f"✅ AdminCLI inicializado. Usando ConductorService + AgentService.")

    @property
    def embodied(self) -> bool:
        """Verifica se o agente alvo existe no ecossistema."""
        return self.agent_service.agent_exists(self.agent_id)

    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Envia uma mensagem ao agente através do ConductorService."""
        if not self.embodied:
            from src.core.constants import Messages, Paths
            suggestions = self.agent_service.get_similar_agent_names(self.agent_id)
            location = f"{Paths.WORKSPACE_ROOT}/{Paths.AGENTS_DIR}/"
            error_msg = Messages.AGENT_NOT_FOUND.format(agent_id=self.agent_id, location=location)
            if suggestions:
                error_msg += f"\n{Messages.SUGGEST_SIMILAR.format(suggestions=', '.join(suggestions))}"
            error_msg += f"\n{Messages.USE_LIST_COMMAND}"
            return error_msg

        try:
            # Handle debug mode - save input without calling provider
            if debug_save_input:
                enhanced_message = self.agent_service.build_meta_agent_context(
                    message, self.meta, self.new_agent_id
                )
                self.debug_utils.save_debug_input(enhanced_message)
                return "✅ DEBUG MODE: Input captured and saved. Provider NOT called."

            # Handle simulation mode
            if self.simulate_mode:
                enhanced_message = self.agent_service.build_meta_agent_context(
                    message, self.meta, self.new_agent_id
                )
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



    def get_available_tools(self) -> list:
        """Get available tools from agent definition."""
        try:
            agent_definition = self.agent_service.get_agent_definition(self.agent_id)
            return agent_definition.allowed_tools if agent_definition else []
        except Exception as e:
            self.logger.error(f"Error getting available tools: {e}")
            return []

    def get_conversation_history(self) -> list:
        """Get conversation history through AgentService."""
        try:
            return self.agent_service.get_conversation_history(self.agent_id)
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []

    def clear_conversation_history(self) -> bool:
        """Clear the agent's conversation history through AgentService."""
        try:
            success = self.agent_service.clear_conversation_history(self.agent_id)
            if success:
                self.logger.info(f"Cleared conversation history for agent {self.agent_id}")
            else:
                self.logger.warning(f"Could not clear conversation history for agent {self.agent_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error clearing conversation history: {e}")
            return False

    def get_full_prompt(self, sample_message: str = "Mensagem de exemplo") -> str:
        """
        Get the complete prompt that would be sent to the AI provider.
        This always shows the REAL prompt, regardless of test mode.
        """
        # Use the unified function from AgentDiscoveryService
        return self.agent_service.get_full_prompt(
            agent_id=self.agent_id, 
            sample_message=sample_message, 
            meta=self.meta, 
            new_agent_id=self.new_agent_id,
            current_message=None,
            save_to_file=False
        )


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
        session_service = container.get_session_management_service()
        session_service.cleanup_orphan_sessions()
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

    # Configure custom exception hook for debug mode
    if args.debug:
        def custom_exception_hook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, Exception):
                print(f"❌ ERRO CRÍTICO: {exc_value}", file=sys.stderr)
                traceback.print_exception(exc_type, exc_value, exc_traceback)
            else:
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
        sys.excepthook = custom_exception_hook

    print(f"🚀 Iniciando Admin CLI")
    print(f"   Agent: {args.agent}")
    if args.meta:
        print(f"   Type: meta-agent")
    else:
        print(f"   Type: project-agent")

    if args.new_agent_id:
        print(f"   New Agent ID: {args.new_agent_id}")
    else:
        print(f"   New Agent ID: will suggest name")

    if args.debug:
        print(f"   Debug mode: enabled")

    # Initialize admin CLI
    admin_cli = AdminCLI(
        agent_id=args.agent,
        ai_provider=args.ai_provider,
        timeout=args.timeout,
        state_provider=args.state_provider,
        debug_mode=args.debug,
        meta=args.meta,
        new_agent_id=args.new_agent_id,
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


    else:
        ErrorHandling.show_usage_tip(parser)
        print("🤖 Meta-agent ready for programmatic use")

    print("\n👋 Admin CLI session completed")


if __name__ == "__main__":
    main()
