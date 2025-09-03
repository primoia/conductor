"""
Error Handling - Shared Error Management

Provides unified error handling and user feedback for CLI interfaces.
"""

import sys
import traceback
from typing import Any, Optional

from src.core.exceptions import (
    ConductorException,
    AgentNotFoundError,
    LLMClientError,
    StatePersistenceError,
)


class ErrorHandling:
    """Provides unified error handling for CLI applications."""

    @staticmethod
    def handle_cli_exceptions(func):
        """
        Decorator for handling CLI exceptions consistently.

        Args:
            func: Function to wrap with error handling

        Returns:
            Wrapped function with error handling
        """

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AgentNotFoundError as e:
                print(f"❌ ERRO: {e}", file=sys.stderr)
                sys.exit(1)
            except LLMClientError as e:
                print(f"❌ ERRO DE COMUNICAÇÃO COM IA: {e}", file=sys.stderr)
                sys.exit(1)
            except StatePersistenceError as e:
                print(f"❌ ERRO DE PERSISTÊNCIA: {e}", file=sys.stderr)
                sys.exit(1)
            except ConductorException as e:
                print(f"❌ ERRO INESPERADO: {e}", file=sys.stderr)
                sys.exit(1)
            except KeyboardInterrupt:
                print("\n⚡ Operação interrompida pelo usuário.")
                sys.exit(130)  # Standard exit code for SIGINT
            except Exception as e:
                print(f"❌ ERRO CRÍTICO: {e}", file=sys.stderr)

                # Show traceback if debug mode is enabled
                debug_mode = False
                if args and hasattr(args[0], "debug") and args[0].debug:
                    debug_mode = True
                elif "debug" in kwargs and kwargs["debug"]:
                    debug_mode = True

                if debug_mode:
                    traceback.print_exc()

                sys.exit(1)

        return wrapper

    @staticmethod
    def safe_execute(
        operation,
        error_message: str = "Operation failed",
        logger: Any = None,
        reraise: bool = False,
    ) -> tuple:
        """
        Safely execute an operation with error handling.

        Args:
            operation: Function/callable to execute
            error_message: Error message prefix
            logger: Optional logger instance
            reraise: Whether to reraise the exception

        Returns:
            Tuple of (success: bool, result: Any, error: Optional[Exception])
        """
        try:
            result = operation()
            return True, result, None
        except Exception as e:
            full_error = f"{error_message}: {e}"
            print(f"❌ {full_error}")

            if logger:
                logger.error(full_error)

            if reraise:
                raise

            return False, None, e

    @staticmethod
    def validate_environment():
        """Validate the environment and dependencies."""
        validation_errors = []

        # Check for critical directories/files
        critical_paths = [
            "src/container.py",
            "src/core/agent_logic.py",
            "src/core/observability.py",
        ]

        import os

        for path in critical_paths:
            if not os.path.exists(path):
                validation_errors.append(f"Missing critical file: {path}")

        if validation_errors:
            print("❌ ENVIRONMENT VALIDATION FAILED:")
            for error in validation_errors:
                print(f"   - {error}")
            return False

        return True

    @staticmethod
    def show_usage_tip(parser: Any):
        """Show helpful usage tips."""
        print("\n💡 DICAS DE USO:")
        print("   - Use --repl para modo interativo")
        print("   - Use --input para mensagem única")
        print("   - Use --debug para informações detalhadas")
        print("   - Use --help para ver todas as opções")
        print(f"\n📖 Para mais informações: {parser.prog} --help")

    @staticmethod
    def format_error_context(error: Exception, context: dict = None) -> str:
        """
        Format error with additional context.

        Args:
            error: Exception to format
            context: Additional context information

        Returns:
            Formatted error message
        """
        error_msg = f"❌ {type(error).__name__}: {str(error)}"

        if context:
            error_msg += "\n📍 Contexto:"
            for key, value in context.items():
                error_msg += f"\n   - {key}: {value}"

        return error_msg

    @staticmethod
    def check_permissions() -> bool:
        """Check if the current user has necessary permissions."""
        import os
        import tempfile

        try:
            # Test write permissions in temp directory
            with tempfile.NamedTemporaryFile(delete=True):
                pass
            return True
        except (PermissionError, OSError):
            print("❌ Insufficient permissions to write temporary files")
            return False
