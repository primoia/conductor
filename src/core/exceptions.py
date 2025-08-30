# src/core/exceptions.py

class ConductorException(Exception):
    """Base exception for the application."""
    pass

class AgentNotFoundError(ConductorException):
    """Raised when a specified agent is not found."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' not found.")

class LLMClientError(ConductorException):
    """Raised for errors related to the LLM client."""
    pass

class StatePersistenceError(ConductorException):
    """Raised for errors related to state persistence."""
    pass