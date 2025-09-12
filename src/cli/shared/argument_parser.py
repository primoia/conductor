"""
CLI Argument Parser - Shared Argument Parsing

Provides base argument parsing functionality with common options.
"""

import argparse
from typing import Dict, Any, Optional


class CLIArgumentParser:
    """Base argument parser for CLI applications."""

    @staticmethod
    def create_main_parser() -> argparse.ArgumentParser:
        """Create main conductor CLI parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog="conductor",
            description="Conductor - AI-Powered Orchestration Framework",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  conductor list-agents                    # List all available agents
  conductor execute --agent MyAgent --input "Hello"  # Execute agent task
  conductor validate-config                # Validate configuration

For more information, visit: https://github.com/cezarfuhr/conductor
            """
        )
        
        # Create subparsers
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # List agents command
        list_parser = subparsers.add_parser('list-agents', help='List all available agents')
        list_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['list_agents_command']).list_agents_command(args))
        
        # Execute command
        exec_parser = subparsers.add_parser('execute', help='Execute an agent task')
        exec_parser.add_argument('--agent', required=True, help='Agent ID to execute')
        exec_parser.add_argument('--input', required=True, help='Input message for the agent')
        exec_parser.add_argument('--environment', help='Environment context (for project agents)')
        exec_parser.add_argument('--project', help='Project context (for project agents)')
        exec_parser.add_argument('--project-path', help='Working directory for the agent (default: agent home)')
        exec_parser.add_argument('--timeout', type=int, default=120, help='Timeout in seconds for AI operations')
        exec_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['execute_agent_command']).execute_agent_command(args))
        
        # Validate config command
        validate_parser = subparsers.add_parser('validate-config', help='Validate configuration')
        validate_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['validate_config_command']).validate_config_command(args))
        
        # Info command
        info_parser = subparsers.add_parser('info', help='Show detailed information about an agent')
        info_parser.add_argument('--agent', required=True, help='Agent ID to show info for')
        info_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['info_agent_command']).info_agent_command(args))
        
        # Backup command
        backup_parser = subparsers.add_parser('backup', help='Backup agents to persistent storage')
        backup_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['backup_agents_command']).backup_agents_command(args))
        
        # Restore command
        restore_parser = subparsers.add_parser('restore', help='Restore agents from persistent storage')
        restore_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['restore_agents_command']).restore_agents_command(args))
        
        # Install templates command
        install_parser = subparsers.add_parser('install', help='Install agent templates')
        install_parser.add_argument('--category', help='Category to install (web_development, data_science, etc.)')
        install_parser.add_argument('--agent', help='Specific agent to install')
        install_parser.add_argument('--list', action='store_true', help='List available templates')
        install_parser.set_defaults(func=lambda args: __import__('src.cli.conductor', fromlist=['install_templates_command']).install_templates_command(args))
        
        return parser

    @staticmethod
    def create_base_parser(
        description: str, epilog: str = None
    ) -> argparse.ArgumentParser:
        """
        Create base argument parser with common options.

        Args:
            description: Parser description
            epilog: Parser epilog with examples

        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog,
        )

        # Common options
        parser.add_argument(
            "--ai-provider",
            type=str,
            default=None,
            choices=["claude", "gemini"],
            help="AI provider override",
        )
        parser.add_argument(
            "--repl", action="store_true", help="Start interactive REPL"
        )
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument(
            "--input", type=str, default=None, help="Input message to send to agent"
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=120,
            help="Timeout in seconds for AI operations",
        )
        parser.add_argument(
            "--state-provider",
            type=str,
            default="file",
            choices=["file", "mongo"],
            help="State persistence provider",
        )

        return parser

    @staticmethod
    def create_admin_parser() -> argparse.ArgumentParser:
        """Create argument parser for admin CLI."""
        epilog = """
Examples:
    # Create meta-agent with specific ID
    python -m src.cli.admin --agent AgentCreator_Agent --meta --new-agent-id MyMetaAgent --repl
    
    # Create project agent with specific ID
    python -m src.cli.admin --agent AgentCreator_Agent --new-agent-id MyAgent --environment develop --project myproject --repl
    
    # Create meta-agent with name suggestion dialog
    python -m src.cli.admin --agent AgentCreator_Agent --meta --repl
    
    # Create project agent with name suggestion dialog
    python -m src.cli.admin --agent AgentCreator_Agent --environment develop --project myproject --repl
        """

        parser = CLIArgumentParser.create_base_parser(
            "Admin CLI - Meta-Agent Management", epilog
        )

        # Admin-specific options
        parser.add_argument(
            "--agent",
            type=str,
            required=True,
            help="Meta-agent ID to embody (required)",
        )

        # New smart agent creation options
        parser.add_argument(
            "--meta",
            action="store_true",
            help="Create a meta-agent (managed in .conductor_workspace/agents/)",
        )
        parser.add_argument(
            "--new-agent-id",
            type=str,
            default=None,
            help="ID of the new agent to create (optional - will suggest if not provided)",
        )

        # Environment and project arguments (conditionally required)
        parser.add_argument(
            "--environment",
            type=str,
            default=None,
            help="Environment name (required when --meta is False)",
        )
        parser.add_argument(
            "--project",
            type=str,
            default=None,
            help="Project name (required when --meta is False)",
        )

        # Legacy options (keeping for backward compatibility)
        parser.add_argument(
            "--destination-path",
            type=str,
            default=None,
            help="Destination path for agent creation (legacy - will be inferred)",
        )
        parser.add_argument(
            "--debug-input",
            action="store_true",
            help="DEBUG: Save input without calling provider",
        )
        parser.add_argument(
            "--simulate-chat",
            action="store_true",
            help="Simulate responses without calling provider",
        )

        # Override timeout default for admin
        parser.set_defaults(timeout=90)

        return parser

    @staticmethod
    def create_agent_parser() -> argparse.ArgumentParser:
        """Create argument parser for agent CLI."""
        epilog = """
Examples:
    python -m src.cli.agent --environment develop --project myproject --agent MyAgent --repl
    python -m src.cli.agent --environment develop --project myproject --agent MyAgent --input "Hello"
        """

        parser = CLIArgumentParser.create_base_parser(
            "Agent CLI - Project Agent Management", epilog
        )

        # Agent-specific options
        parser.add_argument(
            "--environment",
            type=str,
            required=True,
            help="Environment name (develop, main, etc.)",
        )
        parser.add_argument("--project", type=str, required=True, help="Project name")
        parser.add_argument(
            "--agent", type=str, required=True, help="Agent ID to embody"
        )

        return parser

    @staticmethod
    def validate_args(
        args: argparse.Namespace,
        required_combinations: Optional[Dict[str, list]] = None,
    ) -> bool:
        """
        Validate argument combinations.

        Args:
            args: Parsed arguments
            required_combinations: Dict of {condition: [required_args]}

        Returns:
            True if valid, False otherwise
        """
        if required_combinations:
            for condition, required_args in required_combinations.items():
                if hasattr(args, condition) and getattr(args, condition):
                    for req_arg in required_args:
                        if not hasattr(args, req_arg) or not getattr(args, req_arg):
                            return False

        return True

    @staticmethod
    def validate_admin_args(args: argparse.Namespace) -> bool:
        """
        Validate admin CLI argument combinations.

        Args:
            args: Parsed arguments

        Returns:
            True if valid, False otherwise
        """
        # If --meta is True, environment and project should be prohibited
        if args.meta:
            if args.environment is not None or args.project is not None:
                print(
                    "❌ Error: --meta flag cannot be used with --environment or --project"
                )
                return False

        # If --meta is False (default), environment and project are required
        else:
            if args.environment is None or args.project is None:
                print(
                    "❌ Error: --environment and --project are required when creating project agents (not meta-agents)"
                )
                return False

        return True
