import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

from src.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    This formatter converts log records to JSON format for better
    integration with monitoring and observability platforms.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(debug_mode: bool = False, agent_name: str = "conductor") -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        debug_mode: Whether to enable debug mode with console output
        agent_name: Name of the agent for log file naming
        
    Returns:
        Configured logger instance
    """
    # Create logs directory
    from pathlib import Path
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    root_logger.handlers.clear()
    
    # File handler with JSON formatting
    log_file = logs_dir / f"{agent_name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    if settings.json_logging:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
    
    root_logger.addHandler(file_handler)
    
    # Console handler for debug mode
    if debug_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        root_logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    root_logger.propagate = False
    
    # Create application-specific logger
    app_logger = logging.getLogger(f'conductor.{agent_name}')
    
    return app_logger


def add_context_to_logger(logger: logging.Logger, context: Dict[str, Any]):
    """
    Add context information to logger for structured logging.
    
    Args:
        logger: Logger instance
        context: Context dictionary to add to log records
    """
    class ContextFilter(logging.Filter):
        def filter(self, record):
            for key, value in context.items():
                setattr(record, key, value)
            return True
    
    logger.addFilter(ContextFilter())