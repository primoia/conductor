"""
CLI Argument Parser - Shared Argument Parsing

Provides base argument parsing functionality with common options.
"""

import argparse
from typing import Dict, Any, Optional


class CLIArgumentParser:
    """Base argument parser for CLI applications."""
    
    @staticmethod
    def create_base_parser(description: str, epilog: str = None) -> argparse.ArgumentParser:
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
            epilog=epilog
        )
        
        # Common options
        parser.add_argument('--ai-provider', type=str, default=None,
                          choices=['claude', 'gemini'],
                          help='AI provider override')
        parser.add_argument('--repl', action='store_true',
                          help='Start interactive REPL')
        parser.add_argument('--debug', action='store_true',
                          help='Enable debug mode')
        parser.add_argument('--input', type=str, default=None,
                          help='Input message to send to agent')
        parser.add_argument('--timeout', type=int, default=120,
                          help='Timeout in seconds for AI operations')
        parser.add_argument('--state-provider', type=str, default='file',
                          choices=['file', 'mongo'],
                          help='State persistence provider')
        
        return parser
    
    @staticmethod
    def create_admin_parser() -> argparse.ArgumentParser:
        """Create argument parser for admin CLI."""
        epilog = """
Examples:
    python -m src.cli.admin --agent AgentCreator_Agent --repl
    python -m src.cli.admin --agent AgentCreator_Agent --input "Create an agent"
        """
        
        parser = CLIArgumentParser.create_base_parser(
            'Admin CLI - Meta-Agent Management',
            epilog
        )
        
        # Admin-specific options
        parser.add_argument('--agent', type=str, required=True,
                          help='Meta-agent ID to embody (required)')
        parser.add_argument('--destination-path', type=str, default=None,
                          help='Destination path for agent creation')
        parser.add_argument('--debug-input', action='store_true',
                          help='DEBUG: Save input without calling provider')
        parser.add_argument('--simulate-chat', action='store_true',
                          help='Simulate responses without calling provider')
        
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
            'Agent CLI - Project Agent Management',
            epilog
        )
        
        # Agent-specific options
        parser.add_argument('--environment', type=str, required=True,
                          help='Environment name (develop, main, etc.)')
        parser.add_argument('--project', type=str, required=True,
                          help='Project name')
        parser.add_argument('--agent', type=str, required=True,
                          help='Agent ID to embody')
        
        return parser
    
    @staticmethod
    def validate_args(args: argparse.Namespace, required_combinations: Optional[Dict[str, list]] = None) -> bool:
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