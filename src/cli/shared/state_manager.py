"""
State Manager - Shared Agent State Management

Provides unified state management operations for CLI interfaces.
"""

from typing import Any, Optional


class StateManager:
    """Manages agent state operations."""

    def __init__(self, cli_instance: Any, logger: Any):
        """
        Initialize state manager.

        Args:
            cli_instance: CLI instance with agent_logic
            logger: Logger instance for operations
        """
        self.cli_instance = cli_instance
        self.logger = logger

    def save_agent_state(self) -> bool:
        """
        Save agent state with proper logging and error handling.

        Returns:
            True if successful, False otherwise
        """
        # State is now managed by ConductorService directly after task execution.
        # This method is a no-op for AdminCLI/AgentCLI.
        return True

    def get_agent_status(self) -> dict:
        """
        Get comprehensive agent status.

        Returns:
            Dictionary with agent status information
        """
        status = {
            "embodied": self.cli_instance.embodied,
            "agent_id": self.cli_instance.agent_id,
            "working_directory": "N/A (gerenciado pelo ConductorService)",
            "environment": getattr(self.cli_instance, "environment", None),
            "project": getattr(self.cli_instance, "project", None),
            "available_tools": self.cli_instance.get_available_tools(),
            "output_scope": [],
        }

        if hasattr(self.cli_instance, "get_output_scope"):
            status["output_scope"] = self.cli_instance.get_output_scope()

        return status

    def get_conversation_history(self) -> list:
        """
        Get conversation history if available.

        Returns:
            List of conversation messages or empty list
        """
        # Delegar ao cli_instance
        return self.cli_instance.get_conversation_history()

    def clear_conversation_history(self) -> bool:
        """
        Clear conversation history and save state.

        Returns:
            True if successful, False otherwise
        """
        # Delegar ao cli_instance
        return self.cli_instance.clear_conversation_history()

    def backup_state(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of the current agent state.

        Args:
            backup_path: Optional custom backup path

        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder for future backup functionality
        # Could be implemented to create JSON/pickle backups
        self.logger.info("State backup functionality not yet implemented")
        return False

    def restore_state(self, backup_path: str) -> bool:
        """
        Restore agent state from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful, False otherwise
        """
        # This is a placeholder for future restore functionality
        self.logger.info("State restore functionality not yet implemented")
        return False
