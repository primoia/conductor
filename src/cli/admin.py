#!/usr/bin/env python3
"""
Admin CLI - Meta-Agent Management

This CLI provides access to meta-agents for framework management.
It acts as a thin interface that delegates to the core business logic.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.container import container
from src.core.observability import configure_logging
from src.core.domain import AgentNotEmbodied
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
    Admin CLI class that provides a thin interface to agent logic.

    This class handles:
    - Argument parsing
    - Logging setup
    - Delegation to AgentLogic
    - Error handling and user feedback
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

        # Get agent logic from container (admin agents get unrestricted access)
        self.agent_logic = container.create_agent_logic(
            state_provider=state_provider,
            ai_provider=ai_provider or "claude",
            timeout=timeout,
            is_admin_agent=True,
        )

        # Store CLI-specific state (legacy support)
        self.destination_path = destination_path
        self.simulate_mode = False

        # Initialize shared components
        self.state_manager = StateManager(self, self.logger)
        self.debug_utils = DebugUtilities(self, self.logger)

        # Embody the meta-agent
        self._embody_meta_agent(agent_id)

    def _embody_meta_agent(self, agent_id: str):
        """Embody a meta-agent using the container."""
        try:
            # Resolve paths for meta-agent
            agent_home_path, project_root_path = container.resolve_agent_paths(
                "_common", "_common", agent_id
            )

            # Embody the agent
            success = self.agent_logic.embody_agent(
                environment="_common",
                project="_common",
                agent_id=agent_id,
                agent_home_path=agent_home_path,
                project_root_path=project_root_path,
            )

            if success:
                print(f"✅ Successfully embodied meta-agent: {agent_id}")
                self.logger.info(f"Embodied meta-agent: {agent_id}")

                # Setup LLM client reference for tools access
                if hasattr(self.agent_logic.llm_client, "genesis_agent"):
                    # For compatibility with existing tooling
                    self.agent_logic.llm_client.genesis_agent = self.agent_logic

            else:
                raise Exception("Failed to embody meta-agent")

        except Exception as e:
            self.logger.error(f"Failed to embody meta-agent {agent_id}: {e}")
            raise

    @property
    def embodied(self) -> bool:
        """Check if agent is embodied."""
        return self.agent_logic.is_embodied()

    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Send a message to the meta-agent."""
        if not self.embodied:
            return "❌ No agent embodied."

        try:
            # Build enhanced message with context
            enhanced_message = self._build_enhanced_message(message)

            # Handle debug mode - save input without calling provider
            if debug_save_input:
                self.debug_utils.save_debug_input(enhanced_message)
                return "✅ DEBUG MODE: Input captured and saved. Provider NOT called."

            # Handle simulation mode
            if self.simulate_mode:
                return self.debug_utils.generate_simulation_response(enhanced_message)

            # Normal chat interaction
            # self.logger.info(f"Processing chat message: {message[:100]}...")
            response = self.agent_logic.chat(enhanced_message)
            self.logger.info(
                f"Chat response received: {len(response) if response else 0} chars"
            )

            return response

        except AgentNotEmbodied as e:
            return f"❌ {str(e)}"
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"❌ Error in chat: {e}"

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
        """Get available tools from agent logic."""
        return self.agent_logic.get_available_tools()


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
