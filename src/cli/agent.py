#!/usr/bin/env python3
"""
Agent CLI - Project Agent Management

This CLI provides access to project-specific agents.
It acts as a thin interface that delegates to the core business logic.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.container import container
from src.core.observability import configure_logging
from src.core.domain import AgentNotEmbodied
from src.cli.shared import (
    REPLManager,
    CLIArgumentParser,
    StateManager,
    DebugUtilities,
    ErrorHandling,
)


class AgentCLI:
    """
    Agent CLI class for project agents.

    This class handles:
    - Argument parsing
    - Logging setup
    - Delegation to AgentLogic
    - Error handling and user feedback
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

        # Get agent logic from container
        self.agent_logic = container.create_agent_logic(
            state_provider=state_provider,
            ai_provider=ai_provider or "claude",
            timeout=timeout,
        )

        # Initialize shared components
        self.state_manager = StateManager(self, self.logger)
        self.debug_utils = DebugUtilities(self, self.logger)

        # Embody the project agent
        self._embody_project_agent(environment, project, agent_id)

    def _embody_project_agent(self, environment: str, project: str, agent_id: str):
        """Embody a project agent using the container."""
        try:
            # Resolve paths for project agent
            agent_home_path, project_root_path = container.resolve_agent_paths(
                environment, project, agent_id
            )

            # Embody the agent
            success = self.agent_logic.embody_agent(
                environment=environment,
                project=project,
                agent_id=agent_id,
                agent_home_path=agent_home_path,
                project_root_path=project_root_path,
            )

            if success:
                print(f"✅ Successfully embodied project agent: {agent_id}")
                print(f"📍 Environment: {environment}")
                print(f"📦 Project: {project}")
                print(f"📂 Working Directory: {project_root_path}")
                self.logger.info(f"Embodied project agent: {agent_id}")

                # Setup LLM client reference for tools access
                if hasattr(self.agent_logic.llm_client, "genesis_agent"):
                    self.agent_logic.llm_client.genesis_agent = self.agent_logic

            else:
                raise Exception("Failed to embody project agent")

        except Exception as e:
            self.logger.error(f"Failed to embody project agent {agent_id}: {e}")
            raise

    @property
    def embodied(self) -> bool:
        """Check if agent is embodied."""
        return self.agent_logic.is_embodied()

    def chat(self, message: str) -> str:
        """Send a message to the project agent."""
        if not self.embodied:
            return "❌ No agent embodied."

        try:
            # self.logger.info(f"Processing chat message: {message[:100]}...")
            response = self.agent_logic.chat(message)
            self.logger.info(
                f"Chat response received: {len(response) if response else 0} chars"
            )

            return response

        except AgentNotEmbodied as e:
            return f"❌ {str(e)}"
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"❌ Error in chat: {e}"

    def save_agent_state(self):
        """Save agent state using StateManager."""
        return self.state_manager.save_agent_state()

    def get_available_tools(self) -> list:
        """Get available tools from agent logic."""
        return self.agent_logic.get_available_tools()

    def get_output_scope(self) -> list:
        """Get output scope restrictions."""
        return self.agent_logic.output_scope or []


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
        print(f"❌ Failed to embody agent: {args.agent}")
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
