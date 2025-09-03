# src/core/exceptions.py


class ConductorException(Exception):
    """Base exception for the application."""

    pass


class AgentNotFoundError(ConductorException):
    """Raised when a specified agent is not found."""

    pass


class LLMClientError(ConductorException):
    """Raised for errors related to the LLM client."""

    pass


class StatePersistenceError(ConductorException):
    """Raised for errors related to state persistence."""

    pass


class ConfigurationError(ConductorException):
    """Raised for errors related to agent configuration."""

    pass
