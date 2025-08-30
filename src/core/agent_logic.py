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
    AgentConfig, ConversationMessage, AgentState, 
    AgentNotEmbodied, ConfigurationError, StateRepositoryError
)
from src.core.exceptions import (
    AgentNotFoundError, LLMClientError, StatePersistenceError
)

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
        
        # Environment and project context
        self.environment: Optional[str] = None
        self.project: Optional[str] = None
        
        # Output scope restriction for specialized agents
        self.output_scope: Optional[List[str]] = None
        
        logger.info("AgentLogic initialized with injected dependencies")
    
    def embody_agent(self, environment: str, project: str, agent_id: str, 
                    agent_home_path: Path, project_root_path: Path) -> bool:
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
            
            # Load agent configuration
            self.agent_config = self._load_agent_config(agent_home_path)
            
            # Validate configuration
            self._validate_agent_config(self.agent_config)
            
            # Load agent persona
            persona_path = agent_home_path / self.agent_config.get("persona_prompt_path", "persona.md")
            self.agent_persona = self._load_agent_persona(persona_path, agent_id)
            
            # Set persona in LLM client
            self.llm_client.set_persona(self.agent_persona)
            
            # Load agent state
            state_file_name = self.agent_config.get("state_file_path", "state.json")
            state_data = self.state_repository.load_state(str(agent_home_path), state_file_name)
            
            # Convert conversation history to proper format
            conversation_history = []
            for msg in state_data.get("conversation_history", []):
                if isinstance(msg, dict) and 'prompt' in msg and 'response' in msg:
                    conversation_history.append(ConversationMessage(**msg))
            
            # Set conversation history in LLM client
            if hasattr(self.llm_client, 'conversation_history'):
                self.llm_client.conversation_history = [msg.dict() for msg in conversation_history]
            
            # Configure output scope if applicable
            target_context = self.agent_config.get('target_context')
            if target_context and 'output_scope' in target_context:
                self.output_scope = target_context['output_scope']
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
            raise AgentNotEmbodied("No agent currently embodied. Use embody_agent() first.")
        
        try:
            response = self.llm_client.invoke(message)
            
            # Save state after interaction
            self.save_agent_state()
            
            return response or "No response from agent."
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise
    
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
            if hasattr(self.llm_client, 'conversation_history'):
                conversation_history = self.llm_client.conversation_history
            
            state_data = {
                'conversation_history': conversation_history,
                'last_modified': datetime.now().isoformat(),
                'agent_id': self.current_agent,
                'environment': self.environment,
                'project': self.project,
                'metadata': {
                    'working_directory': self.working_directory,
                    'output_scope': self.output_scope
                }
            }
            
            state_file_name = self.agent_config.get("state_file_path", "state.json")
            success = self.state_repository.save_state(
                str(self.agent_home_path), 
                state_file_name, 
                state_data
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
        if not self.agent_config:
            return []
        return self.agent_config.get('available_tools', [])
    
    def is_embodied(self) -> bool:
        """Check if an agent is currently embodied."""
        return self.embodied
    
    def get_current_agent(self) -> Optional[str]:
        """Get the currently embodied agent ID."""
        return self.current_agent
    
    def _load_agent_config(self, agent_home_path: Path) -> Dict[str, Any]:
        """Load agent configuration from agent.yaml."""
        agent_yaml_path = agent_home_path / "agent.yaml"
        if not agent_yaml_path.exists():
            raise AgentNotFoundError(f"agent.yaml not found: {agent_yaml_path}")
        
        try:
            with open(agent_yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing agent.yaml: {e}")
    
    def _validate_agent_config(self, config: Dict[str, Any]) -> None:
        """Validate agent configuration."""
        required_fields = ['name']
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(f"Required field '{field}' missing in agent configuration")
    
    def _load_agent_persona(self, persona_path: Path, agent_name: str = None) -> str:
        """Load and process agent persona from persona.md file."""
        if not persona_path.exists():
            raise AgentNotFoundError(f"Persona file not found: {persona_path}")
        
        try:
            with open(persona_path, 'r', encoding='utf-8') as f:
                persona_content = f.read()
            
            # Resolve placeholders in persona content
            return self._resolve_persona_placeholders(persona_content, agent_name)
            
        except Exception as e:
            raise ConfigurationError(f"Error loading agent persona: {e}")
    
    def _resolve_persona_placeholders(self, persona_content: str, agent_name: str = None) -> str:
        """Resolve placeholders in persona content with actual agent values."""
        processed_content = persona_content
        
        # Get agent information for placeholder resolution
        agent_id = agent_name or getattr(self, 'current_agent', 'Unknown_Agent')
        agent_config = getattr(self, 'agent_config', {})
        
        # Extract friendly name from persona title if available
        friendly_name = self._extract_persona_title(persona_content) or agent_id
        
        # Ensure we have valid string values for replacements
        agent_id = agent_id if agent_id else 'Unknown_Agent'
        agent_description = agent_config.get('description', f'{agent_id} specialized agent')
        agent_description = agent_description if agent_description else f'{agent_id} specialized agent'
        
        # Define common placeholder mappings
        placeholders = {
            'Contexto': friendly_name,  # Replace "Contexto" with friendly name
            '{{agent_id}}': agent_id,
            '{{agent_name}}': friendly_name,
            '{{agent_description}}': agent_description,
            '{{environment}}': getattr(self, 'environment', 'develop'),
            '{{project}}': getattr(self, 'project', 'unknown'),
            '{{project_key}}': getattr(self, 'project', 'unknown'),
        }
        
        # Apply placeholder replacements only with valid strings
        for placeholder, replacement in placeholders.items():
            if replacement and isinstance(replacement, str):
                processed_content = processed_content.replace(placeholder, replacement)
        
        logger.debug(f"Resolved placeholders in persona for agent: {agent_id} (friendly: {friendly_name})")
        return processed_content
    
    def _extract_persona_title(self, persona_content: str) -> Optional[str]:
        """Extract friendly name from persona title."""
        import re
        
        # Look for "# Persona: [Title]" pattern
        title_match = re.search(r'^#\s*Persona:\s*(.+)$', persona_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up common patterns
            title = re.sub(r'Agent$', '', title)  # Remove trailing "Agent"
            title = title.strip()
            return title
        
        return None
    
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