import logging
import sys
from typing import Dict, Any

from pythonjsonlogger.json import JsonFormatter
from src.config import settings


class SmartFormatter(logging.Formatter):
    """
    A smart formatter that chooses between JSON and plain text format.

    It detects if it's running in an interactive terminal (TTY).
    - If TTY: formats logs as plain, readable text for the user.
    - If not TTY (e.g., piped to Docker logs): formats logs as JSON
      for structured logging platforms like Loki/Grafana.
    """

    def __init__(self):
        super().__init__()
        self.json_formatter = JsonFormatter()
        self.plain_formatter = logging.Formatter("%(message)s")

    def format(self, record: logging.LogRecord) -> str:
        if sys.stdout.isatty():
            # REPL mode: clean output
            # Only show INFO messages and above in the clean format
            if record.levelno >= logging.INFO:
                return self.plain_formatter.format(record)
            return ""  # Discard DEBUG messages in clean mode
        else:
            # Docker/Loki mode: structured JSON output
            return self.json_formatter.format(record)


def configure_logging(
    debug_mode: bool = False, agent_name: str = "conductor", agent_id: str = None
) -> logging.Logger:
    """
    Configure structured and context-aware logging.

    Args:
        debug_mode: If True, sets log level to DEBUG, otherwise INFO.
        agent_name: Name of the agent for logger naming.
        agent_id: ID of the agent to be added as context to logs.

    Returns:
        Configured logger instance for the application.
    """
    # Clear any existing handlers from all loggers to avoid duplication
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        if logger.hasHandlers():
            logger.handlers.clear()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Create a single handler that writes to standard output
    handler = logging.StreamHandler(sys.stdout)
    
    # Set handler level to INFO to filter out DEBUG messages in terminal
    # but keep root logger at DEBUG to capture all logs for observability
    handler.setLevel(logging.INFO)

    # Apply the smart formatter
    handler.setFormatter(SmartFormatter())

    root_logger.addHandler(handler)

    # Prevent propagation from the root logger
    root_logger.propagate = False

    # Get the specific application logger
    app_logger = logging.getLogger(f"conductor.{agent_name}")

    # Add agent context for structured logs
    if agent_id:
        add_context_to_logger(app_logger, {"agent": agent_id})

    return app_logger


def add_context_to_logger(logger: logging.Logger, context: Dict[str, Any]):
    """
    Add context information to a logger using a filter.

    Args:
        logger: Logger instance to which the filter will be added.
        context: Dictionary with context information to add to log records.
    """

    class ContextFilter(logging.Filter):
        def filter(self, record):
            for key, value in context.items():
                setattr(record, key, value)
            return True

    # Clear existing filters to prevent duplication if called multiple times
    logger.filters.clear()
    logger.addFilter(ContextFilter(context))
