import os
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from src.ports.state_repository import StateRepository
from src.ports.llm_client import LLMClient
from src.core.domain import (
    AgentConfig,
    ConversationEntryDTO,
    ConversationMessage,  # Deprecated
    AgentState,
    AgentNotEmbodied,
    StateRepositoryError,
)
from src.core.exceptions import ConfigurationError
from src.core.exceptions import (
    AgentNotFoundError,
    LLMClientError,
    StatePersistenceError,
)
from .prompt_engine import PromptEngine

logger = logging.getLogger(__name__)


class AgentLogic:
    """
    Core business logic for agent embodiment and interaction.

    This class contains the pure business logic without I/O dependencies.
    All external dependencies are injected through interfaces (ports).
    """

    def __init__(self, state_repository: StateRepository, llm_client: LLMClient):
        """
        Initialize agent logic with injected dependencies.

        Args:
            state_repository: Implementation of StateRepository for persistence
            llm_client: Implementation of LLMClient for AI interactions
        """
        self.state_repository = state_repository
        self.llm_client = llm_client

        # Agent state
        self.current_agent: Optional[str] = None
        self.embodied: bool = False
        self.agent_config: Optional[Dict[str, Any]] = None
        self.agent_persona: Optional[str] = None
        self.agent_home_path: Optional[Path] = None
        self.project_root_path: Optional[Path] = None
        self.working_directory: Optional[str] = None
        self.prompt_engine: Optional[PromptEngine] = None

        # Environment and project context
        self.environment: Optional[str] = None
        self.project: Optional[str] = None

        # Output scope restriction for specialized agents
        self.output_scope: Optional[List[str]] = None

        logger.info("AgentLogic initialized with injected dependencies")

    def embody_agent(
        self,
        environment: str,
        project: str,
        agent_id: str,
        agent_home_path: Path,
        project_root_path: Path,
    ) -> bool:
        """
        Embody an agent with the given configuration.

        Args:
            environment: Environment name (develop, main, etc.)
            project: Project name
            agent_id: Agent identifier
            agent_home_path: Path to agent's home directory
            project_root_path: Path to project root directory

        Returns:
            True if successful, False otherwise
        """
        try:
            self.environment = environment
            self.project = project
            self.agent_home_path = agent_home_path
            self.project_root_path = project_root_path
            self.working_directory = str(project_root_path)

            # Initialize PromptEngine and load context
            self.prompt_engine = PromptEngine(agent_home_path)
            self.prompt_engine.load_context()

            # Store references for compatibility
            self.agent_config = self.prompt_engine.agent_config
            self.agent_persona = self.prompt_engine.persona_content

            # Load agent state
            state_file_name = self.agent_config.get("state_file_path", "state.json")
            state_data = self.state_repository.load_state(
                str(agent_home_path), state_file_name
            )

            # Load and convert conversation history using new DTO
            conversation_entries = []
            legacy_history = state_data.get("conversation_history", [])
            
            for msg in legacy_history:
                if isinstance(msg, dict) and "prompt" in msg and "response" in msg:
                    # Convert legacy format to new DTO
                    entry = ConversationEntryDTO.from_legacy_format(msg)
                    conversation_entries.append(entry)

            # Set conversation history in LLM client (convert back to legacy format for compatibility)
            if hasattr(self.llm_client, "conversation_history"):
                self.llm_client.conversation_history = [
                    entry.to_legacy_format() for entry in conversation_entries
                ]

            # Configure output scope if applicable
            target_context = self.agent_config.get("target_context")
            if target_context and "output_scope" in target_context:
                self.output_scope = target_context["output_scope"]
                logger.info(f"Output scope configured: {self.output_scope}")
            else:
                self.output_scope = None
                logger.info("No output scope restriction (meta-agent)")

            # Mark agent as embodied
            self.current_agent = agent_id
            self.embodied = True

            logger.info(f"Successfully embodied agent: {agent_id}")
            logger.info(f"Agent Home: {self.agent_home_path}")
            logger.info(f"Project Root: {self.project_root_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to embody agent {agent_id}: {e}")
            self._reset_state()
            return False

    def chat(self, message: str) -> str:
        """
        Send a message to the embodied agent.

        Args:
            message: Message to send to the agent

        Returns:
            Agent's response

        Raises:
            AgentNotEmbodied: If no agent is currently embodied
        """
        if not self.embodied:
            raise AgentNotEmbodied(
                "No agent currently embodied. Use embody_agent() first."
            )

        try:
            # Build final prompt using PromptEngine
            if self.prompt_engine is None:
                # Fallback for cases where PromptEngine wasn't initialized properly
                if hasattr(self, "agent_home_path") and self.agent_home_path:
                    self.prompt_engine = PromptEngine(self.agent_home_path)
                    self.prompt_engine.load_context()
                else:
                    error_msg = (
                        "PromptEngine not initialized and no agent home path available"
                    )
                    logger.error(error_msg)
                    return f"❌ Configuration error: {error_msg}"

            final_prompt = self.prompt_engine.build_prompt(
                self.llm_client.conversation_history, message
            )
            response = self.llm_client.invoke(final_prompt)

            # ARCHITECTURE FIX: Store only user input and AI response, not full prompt
            self.llm_client.add_to_conversation_history(message, response)

            # Save state after interaction
            self.save_agent_state()

            return response or "No response from agent."
        except Exception as e:
            error_msg = f"Chat failed: {e}"
            logger.error(error_msg)
            # CRITICAL FIX: Return error instead of raising to prevent infinite loops
            return f"❌ {error_msg}"

    def save_agent_state(self) -> bool:
        """
        Save current agent state using the state repository.

        Returns:
            True if successful, False otherwise
        """
        if not self.embodied or not self.agent_home_path:
            logger.warning("No agent to save or missing agent home path")
            return False

        try:
            # Prepare state data
            conversation_history = []
            if hasattr(self.llm_client, "conversation_history"):
                conversation_history = self.llm_client.conversation_history

            state_data = {
                "conversation_history": conversation_history,
                "last_modified": datetime.now().isoformat(),
                "agent_id": self.current_agent,
                "environment": self.environment,
                "project": self.project,
                "metadata": {
                    "working_directory": self.working_directory,
                    "output_scope": self.output_scope,
                },
            }

            state_file_name = self.agent_config.get("state_file_path", "state.json")
            success = self.state_repository.save_state(
                str(self.agent_home_path), state_file_name, state_data
            )

            if success:
                logger.info("Agent state saved successfully")
            else:
                logger.error("Failed to save agent state")

            return success

        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")
            return False

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not self.prompt_engine:
            return []
        return self.prompt_engine.get_available_tools()

    def is_embodied(self) -> bool:
        """Check if an agent is currently embodied."""
        return self.embodied

    def get_current_agent(self) -> Optional[str]:
        """Get the currently embodied agent ID."""
        return self.current_agent

    def _reset_state(self):
        """Reset agent state to initial values."""
        self.current_agent = None
        self.embodied = False
        self.agent_config = None
        self.agent_persona = None
        self.agent_home_path = None
        self.project_root_path = None
        self.working_directory = None
        self.environment = None
        self.project = None
        self.output_scope = None
        self.prompt_engine = None
