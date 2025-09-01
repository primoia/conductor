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
        if not self.cli_instance.embodied:
            print("⚠️  No agent state to save")
            return False
        
        try:
            success = self.cli_instance.agent_logic.save_agent_state()
            if success:
                self.logger.info("Agent state saved successfully")
                return True
            else:
                print("❌ Failed to save state")
                self.logger.error("Failed to save agent state")
                return False
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
            self.logger.error(f"Failed to save state: {e}")
            return False
    
    def get_agent_status(self) -> dict:
        """
        Get comprehensive agent status.
        
        Returns:
            Dictionary with agent status information
        """
        status = {
            'embodied': self.cli_instance.embodied,
            'agent_id': None,
            'working_directory': None,
            'environment': None,
            'project': None,
            'available_tools': [],
            'output_scope': []
        }
        
        if self.cli_instance.embodied:
            status['agent_id'] = self.cli_instance.agent_logic.get_current_agent()
            status['working_directory'] = getattr(self.cli_instance.agent_logic, 'working_directory', None)
            status['environment'] = getattr(self.cli_instance.agent_logic, 'environment', None)
            status['project'] = getattr(self.cli_instance.agent_logic, 'project', None)
            status['available_tools'] = self.cli_instance.get_available_tools()
            
            if hasattr(self.cli_instance, 'get_output_scope'):
                status['output_scope'] = self.cli_instance.get_output_scope()
        
        return status
    
    def get_conversation_history(self) -> list:
        """
        Get conversation history if available.
        
        Returns:
            List of conversation messages or empty list
        """
        if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
            return self.cli_instance.agent_logic.llm_client.conversation_history
        return []
    
    def clear_conversation_history(self) -> bool:
        """
        Clear conversation history and save state.
        
        Returns:
            True if successful, False otherwise
        """
        if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
            try:
                history_count = len(self.cli_instance.agent_logic.llm_client.conversation_history)
                self.cli_instance.agent_logic.llm_client.conversation_history.clear()
                self.cli_instance.agent_logic.save_agent_state()
                self.logger.info(f"Conversation history cleared: {history_count} messages removed")
                return True
            except Exception as e:
                self.logger.error(f"Failed to clear conversation history: {e}")
                return False
        return False
    
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