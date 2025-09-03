from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime


class AgentConfig(BaseModel):
    """Model for agent configuration."""

    name: str
    description: Optional[str] = None
    persona_prompt_path: str = "persona.md"
    state_file_path: str = "state.json"
    execution_mode: str = "project_resident"
    ai_provider: Optional[str] = None
    available_tools: List[str] = []
    target_context: Optional[Dict[str, Any]] = None


class ConversationMessage(BaseModel):
    """Model for conversation messages."""

    prompt: str
    response: str
    timestamp: float


class AgentState(BaseModel):
    """Model for agent state."""

    agent_id: str
    environment: str
    project: str
    conversation_history: List[ConversationMessage] = []
    last_modified: datetime
    metadata: Dict[str, Any] = {}


class ConductorException(Exception):
    """Base exception for Conductor framework."""

    pass


class AgentNotEmbodied(ConductorException):
    """Raised when trying to use an agent that hasn't been embodied."""

    pass


class ConfigurationError(ConductorException):
    """Raised when there's a configuration error."""

    pass


class StateRepositoryError(ConductorException):
    """Raised when there's an error with state persistence."""

    pass
