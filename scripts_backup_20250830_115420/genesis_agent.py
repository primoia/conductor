#!/usr/bin/env python3
"""
Genesis Agent - Interactive Agent Embodiment CLI

This script implements the Genesis Agent from the Maestro Framework specification.
Milestone 1: Basic structure and agent loading functionality.

The Genesis Agent serves as the main interface for interactive mode in the Maestro framework,
allowing developers to "embody" specialist agents for dialogue, analysis, and debugging.

This script is focused exclusively on project agents that require environment/project context.
For meta-agents that manage the framework itself, use admin.py instead.
"""

import yaml
import sys
import os
import argparse
import logging
import subprocess
import tempfile
import re
import copy
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
import json
from datetime import datetime
import time
from functools import wraps

# Import shared functionality
try:
    from agent_common import (
        load_ai_providers_config,
        load_agent_config_v2,
        resolve_agent_paths,
        create_llm_client,
        start_repl_session,
        validate_agent_config
    )
except ImportError:
    # Try importing from the same directory when called from tests
    import sys
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    from agent_common import (
        load_ai_providers_config,
        load_agent_config_v2,
        resolve_agent_paths,
        create_llm_client,
        start_repl_session,
        validate_agent_config
    )

# Configuration Constants
WORKSPACES_CONFIG_PATH = os.path.join("config", "workspaces.yaml")
MAX_TOOL_CALLS_PER_TURN = 5  # Limit to prevent infinite loops
MAX_CONVERSATION_HISTORY = 50  # Sliding window for conversation history

# Custom Exceptions for v2.0 Security
class OutputScopeViolationError(Exception):
    """Exceção específica para violações de output_scope que nunca deve ser recuperável."""
    pass

# Error Handling and Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Base delay in seconds
RETRY_DELAY_MULTIPLIER = 2.0  # Exponential backoff multiplier
MAX_RETRY_DELAY = 30.0  # Maximum delay between retries

# Recoverable error types
RECOVERABLE_IO_ERRORS = (OSError, IOError, PermissionError)
RECOVERABLE_NETWORK_ERRORS = (ConnectionError, TimeoutError)
RECOVERABLE_RESOURCE_ERRORS = (MemoryError, OSError)

# Allowlist of safe shell commands for agent operations
SAFE_SHELL_COMMANDS = {
    'ls', 'mkdir', 'cat', 'echo', 'pwd', 'find', 'grep', 'head', 'tail', 
    'wc', 'sort', 'uniq', 'diff', 'tree', 'touch', 'cp', 'mv', 'python', 
    'node', 'npm', 'git', 'which', 'type'
}

# Security Configuration for Team Templates
ALLOWED_AGENT_FIELDS = {
    'id', 'version', 'description', 'ai_provider', 'persona_prompt_path', 
    'state_file_path', 'execution_task', 'available_tools', 'test_framework'
}

# Dangerous patterns in execution_task and other fields
DANGEROUS_PATTERNS = [
    r'rm\s+-rf?\s+/', r'sudo\s+', r'chmod\s+777', r'>/dev/', r'\|\s*sh\b',
    r'eval\s*\(', r'exec\s*\(', r'system\s*\(', r'`[^`]*`', r'\$\([^)]*\)',
    r'__import__', r'open\s*\(.*["\']w', r'delete\s+from', r'drop\s+table',
    r'truncate\s+table', r'alter\s+table', r'create\s+user', r'grant\s+all'
]

# Maximum sizes and limits for security
MAX_TEMPLATE_SIZE = 50000  # 50KB max for team template files
MAX_EXECUTION_TASK_LENGTH = 2000  # 2KB max for execution tasks
MAX_AGENTS_PER_TEMPLATE = 20  # Maximum agents per team template

# User Profile Validation Constants
VALID_ROLES = {
    'backend', 'frontend', 'fullstack', 'devops', 'scrum_master', 'tech_lead', 'other'
}

VALID_EXPERIENCE_LEVELS = {
    'junior', 'mid', 'senior'
}

VALID_PROJECT_TYPES = {
    'new', 'existing'
}

VALID_TEAM_SIZES = {
    'solo', 'team'
}

VALID_ENVIRONMENTS = {
    'develop', 'main', 'production'
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Error Handling Decorators
def retry_on_failure(max_retries: int = MAX_RETRIES, 
                    recoverable_errors: tuple = RECOVERABLE_IO_ERRORS,
                    delay_base: float = RETRY_DELAY_BASE):
    """
    Decorator for automatic retry with exponential backoff on recoverable errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        recoverable_errors: Tuple of exception types that are recoverable
        delay_base: Base delay for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except recoverable_errors as e:
                    last_exception = e
                    if attempt == max_retries:
                        # Final attempt failed, return error structure
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        return {
                            'success': False,
                            'error': f"Operation failed after {max_retries} retries: {str(e)}",
                            'retry_attempts': attempt,
                            'final_error': str(e)
                        }
                    
                    # Calculate delay with exponential backoff
                    delay = min(delay_base * (RETRY_DELAY_MULTIPLIER ** attempt), MAX_RETRY_DELAY)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                except (PermissionError, OutputScopeViolationError) as e:
                    # Security errors should be re-raised immediately
                    logger.error(f"Function {func.__name__} failed with security error: {e}")
                    raise e
                except Exception as e:
                    # Non-recoverable error, fail immediately
                    logger.error(f"Function {func.__name__} failed with non-recoverable error: {e}")
                    return {
                        'success': False,
                        'error': f"Non-recoverable error: {str(e)}",
                        'error_type': type(e).__name__
                    }
            
            # Shouldn't reach here, but just in case
            return {
                'success': False,
                'error': f"Unexpected failure in {func.__name__}",
                'retry_attempts': max_retries
            }
        return wrapper
    return decorator


def with_recovery_fallback(fallback_result: Dict[str, Any] = None):
    """
    Decorator that provides a fallback result when operations fail completely.
    
    Args:
        fallback_result: Dictionary to return on complete failure
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Check if result indicates failure
                if isinstance(result, dict) and not result.get('success', True):
                    logger.warning(f"Function {func.__name__} returned failure, applying fallback")
                    if fallback_result:
                        fallback = fallback_result.copy()
                        fallback['fallback_applied'] = True
                        fallback['original_error'] = result.get('error', 'Unknown error')
                        return fallback
                return result
            except Exception as e:
                logger.error(f"Function {func.__name__} raised exception: {e}")
                if fallback_result:
                    fallback = fallback_result.copy()
                    fallback['fallback_applied'] = True
                    fallback['exception_error'] = str(e)
                    return fallback
                return {
                    'success': False,
                    'error': f"Complete failure in {func.__name__}: {str(e)}",
                    'fallback_applied': True
                }
        return wrapper
    return decorator


def safe_file_operation(create_backup: bool = True):
    """
    Decorator for safe file operations with automatic backup and rollback.
    
    Args:
        create_backup: Whether to create backups before file modifications
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            backup_files = []
            
            try:
                # If this is a file operation, try to identify file paths and create backups
                if create_backup:
                    # Look for file paths in args and kwargs
                    for arg in args:
                        if isinstance(arg, str) and (arg.endswith('.yaml') or arg.endswith('.json') or arg.endswith('.md')):
                            if os.path.exists(arg):
                                backup_path = f"{arg}.backup.{int(time.time())}"
                                shutil.copy2(arg, backup_path)
                                backup_files.append((arg, backup_path))
                                logger.debug(f"Created backup: {backup_path}")
                
                result = func(*args, **kwargs)
                
                # Clean up backups on success
                for original, backup in backup_files:
                    try:
                        os.remove(backup)
                        logger.debug(f"Cleaned up backup: {backup}")
                    except:
                        pass  # Ignore cleanup failures
                
                return result
                
            except (PermissionError, OutputScopeViolationError) as e:
                # Re-raise security errors - these should not be masked by the decorator
                for original, backup in backup_files:
                    try:
                        os.remove(backup)  # Clean up backup since we're re-raising
                    except:
                        pass
                raise e
                
            except Exception as e:
                # Restore from backups on failure
                for original, backup in backup_files:
                    try:
                        shutil.copy2(backup, original)
                        logger.info(f"Restored from backup: {original}")
                    except Exception as restore_error:
                        logger.error(f"Failed to restore backup {backup}: {restore_error}")
                
                logger.error(f"File operation {func.__name__} failed: {e}")
                return {
                    'success': False,
                    'error': f"File operation failed: {str(e)}",
                    'backups_created': len(backup_files),
                    'restoration_attempted': len(backup_files) > 0
                }
        return wrapper
    return decorator


class Toolbelt:
    """
    Toolbelt class providing secure and robust tools for Genesis Agent.
    
    This class implements the three essential tools that give power to the agents:
    - read_file: Read file contents safely
    - write_file: Write content to files with proper validation
    - run_shell_command: Execute shell commands with security restrictions
    """
    
    def __init__(self, working_directory: str = None, genesis_agent=None):
        """
        Initialize the Toolbelt.
        
        Args:
            working_directory: Base directory for tool operations (defaults to current dir)
            genesis_agent: Reference to parent GenesisAgent for v2.0 security features
        """
        self.working_directory = working_directory or os.getcwd()
        self.genesis_agent = genesis_agent  # Reference for output_scope validation
        
        # Registry of available tools
        self.tools = {
            'read_file': self.read_file,
            'write_file': self.write_file,
            'run_shell_command': self.run_shell_command,
            'list_team_templates': self.list_team_templates,
            'apply_team_template': self.apply_team_template,
            'collect_user_profile': self.collect_user_profile,
            'collect_project_context': self.collect_project_context,
            'suggest_team_template': self.suggest_team_template,
            'create_example_project': self.create_example_project
        }
        
        logger.debug(f"Toolbelt initialized with working directory: {self.working_directory}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict containing success status, result, and any error messages
        """
        if tool_name not in self.tools:
            return {
                'success': False,
                'error': f"Unknown tool: {tool_name}",
                'available_tools': list(self.tools.keys())
            }
        
        try:
            logger.info(f"Executing tool: {tool_name}")
            result = self.tools[tool_name](**kwargs)
            logger.info(f"Tool {tool_name} executed successfully")
            return {
                'success': True,
                'result': result,
                'tool': tool_name
            }
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name
            }
    
    @retry_on_failure(max_retries=2, recoverable_errors=RECOVERABLE_IO_ERRORS)
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Read file contents safely with path validation.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
            ValueError: If path is invalid or outside working directory
        """
        # Resolve and validate the path
        resolved_path = self._resolve_and_validate_path(file_path)
        
        logger.debug(f"Reading file: {resolved_path}")
        
        try:
            with open(resolved_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            logger.info(f"Successfully read file: {file_path} ({len(content)} characters)")
            return content
            
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied reading file: {file_path}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Encoding error reading file {file_path}: {e}")
    
    def _validate_output_scope(self, file_path: str) -> bool:
        """
        Valida se o arquivo está dentro do output_scope definido para o agente v2.0.
        
        Args:
            file_path: Caminho do arquivo a ser validado
            
        Returns:
            True se o arquivo está permitido, False caso contrário
        """
        # Se não há agente ou output_scope, permite (meta-agente)
        if not self.genesis_agent or not hasattr(self.genesis_agent, 'output_scope'):
            return True
            
        output_scope = getattr(self.genesis_agent, 'output_scope', None)
        if not output_scope:
            return True  # Meta-agente sem restrições
        
        import fnmatch
        
        # Normaliza o caminho para comparação
        normalized_path = file_path.replace('\\', '/')
        if normalized_path.startswith('./'):
            normalized_path = normalized_path[2:]
        
        # Testa contra o padrão glob do output_scope
        if fnmatch.fnmatch(normalized_path, output_scope):
            logger.info(f"Output scope validation PASSED: {file_path} matches {output_scope}")
            return True
        else:
            logger.warning(f"Output scope validation FAILED: {file_path} does NOT match {output_scope}")
            return False
    
    def _prompt_user_confirmation(self, file_path: str, content: str) -> bool:
        """
        Solicita confirmação do usuário antes de escrever arquivo em modo REPL.
        
        Args:
            file_path: Caminho do arquivo
            content: Conteúdo a ser escrito
            
        Returns:
            True se usuário confirmar, False caso contrário
        """
        try:
            print(f"\n📝 Agent quer escrever arquivo: {file_path}")
            print(f"📏 Tamanho: {len(content)} caracteres")
            
            # Mostra preview do conteúdo
            preview_lines = content.splitlines()[:10]
            print("📄 Preview:")
            for i, line in enumerate(preview_lines, 1):
                print(f"   {i:2}: {line[:80]}")
            
            if len(preview_lines) < len(content.splitlines()):
                remaining = len(content.splitlines()) - len(preview_lines)
                print(f"   ... (+{remaining} linhas)")
            
            response = input("\n✅ Confirmar escrita? (y/N): ").strip().lower()
            return response == 'y'
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Operação cancelada")
            return False
    
    @retry_on_failure(max_retries=3, recoverable_errors=(OSError, IOError))  # Exclude PermissionError for security
    @safe_file_operation(create_backup=True)
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> str:
        """
        Write content to file safely with path validation.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_dirs: Whether to create parent directories if they don't exist
            
        Returns:
            Success message with file path
            
        Raises:
            PermissionError: If file can't be written
            ValueError: If path is invalid or outside working directory
        """
        # Resolve and validate the path
        resolved_path = self._resolve_and_validate_path(file_path, allow_create=True)
        
        # v2.0 Security: Validate output_scope
        if not self._validate_output_scope(file_path):
            raise OutputScopeViolationError(
                f"Output scope violation: '{file_path}' não está permitido pelo output_scope do agente.\n"
                f"Scope permitido: {getattr(self.genesis_agent, 'output_scope', 'N/A')}"
            )
        
        # v2.0 UX: Prompt user confirmation in REPL mode
        is_repl_mode = (self.genesis_agent and 
                       hasattr(self.genesis_agent, 'ai_providers_config'))
        
        if is_repl_mode:
            # Verifica se estamos em modo interativo (tem TTY)
            import sys
            if sys.stdin.isatty():
                if not self._prompt_user_confirmation(file_path, content):
                    return f"❌ Escrita cancelada pelo usuário: {file_path}"
        
        logger.debug(f"Writing file: {resolved_path} ({len(content)} characters)")
        
        try:
            # Create parent directories if requested
            if create_dirs:
                os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
            
            with open(resolved_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"Successfully wrote file: {file_path}")
            return f"File written successfully: {file_path} ({len(content)} characters)"
            
        except PermissionError:
            raise PermissionError(f"Permission denied writing file: {file_path}")
        except OSError as e:
            raise ValueError(f"Error writing file {file_path}: {e}")
    
    def run_shell_command(self, command: str, timeout: int = 30, 
                         capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute shell command with security restrictions.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (default: 30)
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dict containing return code, stdout, stderr, and success status
            
        Raises:
            ValueError: If command is not allowed
            subprocess.TimeoutExpired: If command times out
        """
        # SECURITY: Multi-layer validation
        
        # 1. Extract the base command (first word)
        base_command = command.strip().split()[0] if command.strip() else ""
        
        # 2. Check if base command is in allowlist
        if base_command not in SAFE_SHELL_COMMANDS:
            raise ValueError(f"Command '{base_command}' not in allowlist of safe commands. Allowed: {', '.join(sorted(SAFE_SHELL_COMMANDS))}")
        
        # 3. Check for dangerous patterns (additional layer)
        dangerous_patterns = [
            'rm -rf', 'sudo', 'su ', 'chmod +x', 'curl', 'wget', 
            '>', '>>', '|', '&', ';', '$(', '`', 'rm ', '--force',
            '/dev/', '/proc/', '/sys/', '~/', '../'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ValueError(f"Command contains potentially dangerous pattern '{pattern}': {command}")
        
        # 4. Additional safety: prevent path traversal attempts
        if '..' in command or '~' in command:
            raise ValueError(f"Command contains path traversal or home directory access: {command}")
        
        logger.debug(f"Executing shell command: {command}")
        
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.working_directory,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            result = {
                'returncode': process.returncode,
                'stdout': process.stdout if capture_output else '',
                'stderr': process.stderr if capture_output else '',
                'success': process.returncode == 0,
                'command': command
            }
            
            if result['success']:
                logger.info(f"Command executed successfully: {command}")
            else:
                logger.warning(f"Command failed with return code {process.returncode}: {command}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {command}")
            raise subprocess.TimeoutExpired(command, timeout)
        except Exception as e:
            logger.error(f"Command execution failed: {command} - {e}")
            raise
    
    def _resolve_and_validate_path(self, file_path: str, allow_create: bool = False) -> str:
        """
        Resolve and validate file path for security.
        
        Args:
            file_path: Path to validate
            allow_create: Whether to allow paths to non-existent files
            
        Returns:
            Resolved absolute path
            
        Raises:
            ValueError: If path is invalid or outside working directory
        """
        # Convert to absolute path
        if not os.path.isabs(file_path):
            resolved_path = os.path.join(self.working_directory, file_path)
        else:
            resolved_path = file_path
        
        # Normalize the path (resolve .. and . components)
        resolved_path = os.path.normpath(resolved_path)
        
        # Security check: ensure path is within working directory
        working_dir_abs = os.path.abspath(self.working_directory)
        if not resolved_path.startswith(working_dir_abs):
            raise ValueError(f"Path outside working directory not allowed: {file_path}")
        
        # Check if file exists (unless we're creating it)
        if not allow_create and not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Path does not exist: {file_path}")
        
        return resolved_path
    
    def list_team_templates(self) -> Dict[str, Any]:
        """
        List available team templates from config/teams/ directory.
        
        Returns:
            Dict containing success status and list of available team templates
        """
        try:
            teams_dir = os.path.join(os.getcwd(), "config", "teams")
            
            if not os.path.exists(teams_dir):
                return {
                    'success': False,
                    'error': 'Team templates directory not found: config/teams/',
                    'available_templates': []
                }
            
            templates = []
            for file_name in os.listdir(teams_dir):
                if file_name.endswith('.yaml') or file_name.endswith('.yml'):
                    template_path = os.path.join(teams_dir, file_name)
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = yaml.safe_load(f)
                            templates.append({
                                'id': template_data.get('id', file_name.replace('.yaml', '').replace('.yml', '')),
                                'name': template_data.get('name', 'Unknown'),
                                'description': template_data.get('description', 'No description available'),
                                'persona_type': template_data.get('persona_type', 'General'),
                                'agents_count': len(template_data.get('agents', [])),
                                'workflows_count': len(template_data.get('workflows', []))
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse team template {file_name}: {e}")
                        continue
            
            return {
                'success': True,
                'available_templates': templates,
                'count': len(templates)
            }
            
        except Exception as e:
            logger.error(f"Failed to list team templates: {e}")
            return {
                'success': False,
                'error': f"Failed to list team templates: {str(e)}",
                'available_templates': []
            }
    
    def _validate_template_security(self, template_data: Dict, template_path: str) -> Dict[str, Any]:
        """
        Comprehensive security validation for team templates.
        
        Args:
            template_data: Parsed team template YAML data
            template_path: Path to the template file for size checking
            
        Returns:
            Dict with success status and detailed error information
        """
        try:
            # 1. File size validation
            if os.path.exists(template_path):
                file_size = os.path.getsize(template_path)
                if file_size > MAX_TEMPLATE_SIZE:
                    return {
                        'success': False,
                        'error': f'Template file too large: {file_size} bytes (max: {MAX_TEMPLATE_SIZE})',
                        'security_issue': 'file_size_exceeded'
                    }
            
            # 2. Template structure validation
            if not isinstance(template_data, dict):
                return {
                    'success': False,
                    'error': 'Template must be a valid YAML dictionary',
                    'security_issue': 'invalid_structure'
                }
            
            # 3. Required fields validation
            required_fields = ['id', 'name', 'description', 'agents']
            for field in required_fields:
                if field not in template_data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}',
                        'security_issue': 'missing_required_field'
                    }
            
            # 4. Agents list validation
            agents = template_data.get('agents', [])
            if not isinstance(agents, list):
                return {
                    'success': False,
                    'error': 'Agents field must be a list',
                    'security_issue': 'invalid_agents_structure'
                }
            
            if len(agents) > MAX_AGENTS_PER_TEMPLATE:
                return {
                    'success': False,
                    'error': f'Too many agents: {len(agents)} (max: {MAX_AGENTS_PER_TEMPLATE})',
                    'security_issue': 'too_many_agents'
                }
            
            # 5. Individual agent validation
            for i, agent_config in enumerate(agents):
                if not isinstance(agent_config, dict):
                    return {
                        'success': False,
                        'error': f'Agent {i} must be a dictionary',
                        'security_issue': 'invalid_agent_structure'
                    }
                
                if 'id' not in agent_config:
                    return {
                        'success': False,
                        'error': f'Agent {i} missing required id field',
                        'security_issue': 'missing_agent_id'
                    }
                
                # Validate config_overrides
                overrides = agent_config.get('config_overrides', {})
                if not isinstance(overrides, dict):
                    return {
                        'success': False,
                        'error': f'Agent {agent_config["id"]} config_overrides must be a dictionary',
                        'security_issue': 'invalid_overrides_structure'
                    }
                
                # Check for dangerous fields in overrides
                for key, value in overrides.items():
                    if key not in ALLOWED_AGENT_FIELDS:
                        return {
                            'success': False,
                            'error': f'Dangerous field in config_overrides: {key}',
                            'security_issue': 'dangerous_override_field'
                        }
                    
                    # Special validation for execution_task
                    if key == 'execution_task' and isinstance(value, str):
                        if len(value) > MAX_EXECUTION_TASK_LENGTH:
                            return {
                                'success': False,
                                'error': f'Execution task too long: {len(value)} chars (max: {MAX_EXECUTION_TASK_LENGTH})',
                                'security_issue': 'execution_task_too_long'
                            }
                        
                        # Check for dangerous patterns
                        for pattern in DANGEROUS_PATTERNS:
                            if re.search(pattern, value, re.IGNORECASE):
                                return {
                                    'success': False,
                                    'error': f'Dangerous pattern detected in execution_task: {pattern}',
                                    'security_issue': 'dangerous_execution_pattern'
                                }
            
            # 6. Workflows validation
            workflows = template_data.get('workflows', [])
            if workflows and not isinstance(workflows, list):
                return {
                    'success': False,
                    'error': 'Workflows field must be a list',
                    'security_issue': 'invalid_workflows_structure'
                }
            
            for workflow in workflows:
                if not isinstance(workflow, dict) or 'id' not in workflow or 'path' not in workflow:
                    return {
                        'success': False,
                        'error': 'Invalid workflow configuration',
                        'security_issue': 'invalid_workflow_structure'
                    }
                
                # Validate workflow path
                workflow_path = workflow['path']
                if '..' in workflow_path or workflow_path.startswith('/'):
                    return {
                        'success': False,
                        'error': f'Dangerous workflow path: {workflow_path}',
                        'security_issue': 'dangerous_workflow_path'
                    }
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return {
                'success': False,
                'error': f"Security validation error: {str(e)}",
                'security_issue': 'validation_exception'
            }
    
    def _validate_pre_application(self, team_id: str, project_root: str, env: str, project_name: str) -> Dict[str, Any]:
        """
        Pre-application validation to ensure operation can complete successfully.
        
        Args:
            team_id: ID of the team template
            project_root: Target project root directory
            env: Environment name
            project_name: Project name
            
        Returns:
            Dict with validation results and agent availability info
        """
        try:
            validation_result = {
                'success': True,
                'available_agents': [],
                'missing_agents': [],
                'existing_agents': [],
                'warnings': []
            }
            
            # 1. Validate project root
            if not os.path.exists(project_root):
                return {
                    'success': False,
                    'error': f'Project root does not exist: {project_root}'
                }
            
            if not os.access(project_root, os.W_OK):
                return {
                    'success': False,
                    'error': f'No write permission to project root: {project_root}'
                }
            
            # 2. Load and validate team template
            teams_dir = os.path.join(os.getcwd(), "config", "teams")
            template_path = os.path.join(teams_dir, f"{team_id}.yaml")
            
            if not os.path.exists(template_path):
                return {
                    'success': False,
                    'error': f'Team template not found: {team_id}'
                }
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # 3. Security validation
            security_result = self._validate_template_security(template_data, template_path)
            if not security_result['success']:
                return security_result
            
            # 4. Check agent availability
            target_agents_dir = os.path.join(project_root, "projects", env, project_name, "agents")
            
            for agent_config in template_data.get('agents', []):
                agent_id = agent_config['id']
                
                # Check if source agent exists
                source_agent_path = os.path.join(os.getcwd(), "projects", "develop", "agents", agent_id, "agent.yaml")
                if os.path.exists(source_agent_path):
                    validation_result['available_agents'].append(agent_id)
                else:
                    validation_result['missing_agents'].append(agent_id)
                
                # Check if target agent already exists
                target_agent_dir = os.path.join(target_agents_dir, agent_id)
                if os.path.exists(target_agent_dir):
                    validation_result['existing_agents'].append(agent_id)
                    validation_result['warnings'].append(f'Agent {agent_id} already exists and will be skipped')
            
            # 5. Final validation
            if validation_result['missing_agents']:
                return {
                    'success': False,
                    'error': f'Missing source agents: {", ".join(validation_result["missing_agents"])}',
                    'missing_agents': validation_result['missing_agents']
                }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Pre-application validation failed: {e}")
            return {
                'success': False,
                'error': f"Pre-application validation error: {str(e)}"
            }
    
    def _deep_merge_dict(self, base: Dict, override: Dict) -> Dict:
        """
        Recursively merge two dictionaries with intelligent conflict resolution.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        merged = copy.deepcopy(base)
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge_dict(merged[key], value)
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                # For lists, append without duplicates for tools, replace for others
                if key == 'available_tools':
                    merged[key] = list(set(merged[key] + value))
                else:
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def _apply_config_overrides(self, base_config: Dict, overrides: Dict) -> Dict:
        """
        Apply config overrides with deep merge and security validation.
        
        Args:
            base_config: Base agent configuration
            overrides: Configuration overrides to apply
            
        Returns:
            Merged configuration
        """
        # Validate override fields
        for key in overrides.keys():
            if key not in ALLOWED_AGENT_FIELDS:
                logger.warning(f"Skipping unsafe override field: {key}")
                continue
        
        # Filter out unsafe overrides
        safe_overrides = {k: v for k, v in overrides.items() if k in ALLOWED_AGENT_FIELDS}
        
        return self._deep_merge_dict(base_config, safe_overrides)
    
    def _create_backup_snapshot(self, project_root: str, env: str, project_name: str) -> str:
        """
        Create a backup snapshot before applying template.
        
        Args:
            project_root: Project root directory
            env: Environment name
            project_name: Project name
            
        Returns:
            Backup ID for rollback
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"template_backup_{timestamp}"
            
            target_dir = os.path.join(project_root, "projects", env, project_name)
            if os.path.exists(target_dir):
                backup_dir = os.path.join(project_root, ".conductor_backups", backup_id)
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copytree(target_dir, os.path.join(backup_dir, "agents"), dirs_exist_ok=True)
                
                logger.info(f"Created backup snapshot: {backup_id}")
            
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup snapshot: {e}")
            return ""
    
    def _rollback_to_snapshot(self, project_root: str, env: str, project_name: str, backup_id: str) -> bool:
        """
        Rollback to a previous backup snapshot.
        
        Args:
            project_root: Project root directory
            env: Environment name
            project_name: Project name
            backup_id: Backup ID to restore
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            backup_dir = os.path.join(project_root, ".conductor_backups", backup_id)
            if not os.path.exists(backup_dir):
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            target_dir = os.path.join(project_root, "projects", env, project_name)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            shutil.copytree(os.path.join(backup_dir, "agents"), target_dir)
            logger.info(f"Rollback completed: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def apply_team_template(self, team_id: str, project_root: str, env: str, project_name: str = None) -> Dict[str, Any]:
        """
        Apply a team template to a specific project with comprehensive validation and rollback support.
        
        Args:
            team_id: ID of the team template to apply
            project_root: Absolute path to the target project
            env: Environment (develop, main, production)
            project_name: Name of the project (auto-inferred if not provided)
            
        Returns:
            Dict containing success status, created agents, rollback info, and operation details
        """
        backup_id = ""
        
        try:
            # Auto-infer project name if not provided
            if not project_name:
                project_name = os.path.basename(project_root.rstrip('/'))
            
            # 1. COMPREHENSIVE PRE-APPLICATION VALIDATION
            logger.info(f"Starting pre-application validation for team: {team_id}")
            validation_result = self._validate_pre_application(team_id, project_root, env, project_name)
            
            if not validation_result['success']:
                return validation_result
            
            # Log validation warnings
            for warning in validation_result.get('warnings', []):
                logger.warning(warning)
            
            # 2. CREATE BACKUP SNAPSHOT
            logger.info("Creating backup snapshot before template application")
            backup_id = self._create_backup_snapshot(project_root, env, project_name)
            
            # 3. LOAD TEAM TEMPLATE (already validated in pre-validation)
            teams_dir = os.path.join(os.getcwd(), "config", "teams")
            template_path = os.path.join(teams_dir, f"{team_id}.yaml")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # 4. CREATE TARGET DIRECTORY STRUCTURE
            target_agents_dir = os.path.join(project_root, "projects", env, project_name, "agents")
            os.makedirs(target_agents_dir, exist_ok=True)
            
            created_agents = []
            skipped_agents = []
            operation_log = []
            
            # 5. ATOMIC AGENT CREATION PROCESS
            logger.info(f"Starting atomic agent creation for {len(template_data.get('agents', []))} agents")
            
            for agent_config in template_data.get('agents', []):
                agent_id = agent_config['id']
                config_overrides = agent_config.get('config_overrides', {})
                
                try:
                    # Check if source agent exists (should be validated already)
                    source_agent_path = os.path.join(os.getcwd(), "projects", "develop", "agents", agent_id, "agent.yaml")
                    if not os.path.exists(source_agent_path):
                        logger.warning(f"Source agent not found: {agent_id}, skipping...")
                        skipped_agents.append({
                            'id': agent_id,
                            'reason': 'Source agent definition not found'
                        })
                        continue
                    
                    # Create agent directory
                    agent_dir = os.path.join(target_agents_dir, agent_id)
                    
                    # Check if agent already exists
                    if os.path.exists(agent_dir):
                        skipped_agents.append({
                            'id': agent_id,
                            'reason': 'Agent already exists in target project'
                        })
                        continue
                    
                    os.makedirs(agent_dir, exist_ok=True)
                    operation_log.append(f"Created directory: {agent_dir}")
                    
                    # Load source agent.yaml
                    with open(source_agent_path, 'r', encoding='utf-8') as f:
                        source_agent_data = yaml.safe_load(f)
                    
                    # Apply config overrides with deep merge and security validation
                    final_agent_data = self._apply_config_overrides(source_agent_data, config_overrides)
                    
                    # Write customized agent.yaml
                    target_agent_yaml = os.path.join(agent_dir, "agent.yaml")
                    with open(target_agent_yaml, 'w', encoding='utf-8') as f:
                        yaml.dump(final_agent_data, f, default_flow_style=False, allow_unicode=True)
                    operation_log.append(f"Created agent.yaml: {target_agent_yaml}")
                    
                    # Copy persona.md
                    source_persona = os.path.join(os.getcwd(), "projects", "develop", "agents", agent_id, "persona.md")
                    if os.path.exists(source_persona):
                        target_persona = os.path.join(agent_dir, "persona.md")
                        with open(source_persona, 'r', encoding='utf-8') as src:
                            with open(target_persona, 'w', encoding='utf-8') as dst:
                                dst.write(src.read())
                        operation_log.append(f"Copied persona.md: {target_persona}")
                    
                    # Create initial state.json with enhanced context
                    initial_state = {
                        "conversation_history": [],
                        "project_context": {
                            "project_root": project_root,
                            "project_name": project_name,
                            "environment": env,
                            "created_from_template": team_id,
                            "applied_overrides": list(config_overrides.keys()),
                            "backup_id": backup_id
                        },
                        "version": "1.0",
                        "created_timestamp": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    target_state = os.path.join(agent_dir, "state.json")
                    with open(target_state, 'w', encoding='utf-8') as f:
                        json.dump(initial_state, f, indent=2)
                    operation_log.append(f"Created state.json: {target_state}")
                    
                    created_agents.append({
                        'id': agent_id,
                        'path': agent_dir,
                        'overrides_applied': list(config_overrides.keys()),
                        'backup_id': backup_id
                    })
                    
                    logger.info(f"Successfully created agent: {agent_id}")
                    
                except Exception as e:
                    # Log the error and add to skipped agents
                    error_msg = f"Failed to create agent {agent_id}: {str(e)}"
                    logger.error(error_msg)
                    skipped_agents.append({
                        'id': agent_id,
                        'reason': error_msg
                    })
                    
                    # Clean up partially created agent directory
                    agent_dir = os.path.join(target_agents_dir, agent_id)
                    if os.path.exists(agent_dir):
                        try:
                            shutil.rmtree(agent_dir)
                            operation_log.append(f"Cleaned up failed agent directory: {agent_dir}")
                        except Exception as cleanup_error:
                            logger.error(f"Failed to cleanup agent directory {agent_dir}: {cleanup_error}")
                    
                    continue
            
            # 6. COPY WORKFLOWS WITH VALIDATION
            workflows_copied = []
            workflow_errors = []
            
            if 'workflows' in template_data:
                try:
                    workflows_dir = os.path.join(project_root, "workflows")
                    os.makedirs(workflows_dir, exist_ok=True)
                    operation_log.append(f"Created workflows directory: {workflows_dir}")
                    
                    for workflow_config in template_data['workflows']:
                        try:
                            workflow_id = workflow_config['id']
                            workflow_path = workflow_config['path']
                            source_workflow = os.path.join(os.getcwd(), "config", "workflows", workflow_path)
                            
                            if os.path.exists(source_workflow):
                                target_workflow = os.path.join(workflows_dir, f"{workflow_id}.yaml")
                                with open(source_workflow, 'r', encoding='utf-8') as src:
                                    with open(target_workflow, 'w', encoding='utf-8') as dst:
                                        dst.write(src.read())
                                workflows_copied.append(workflow_id)
                                operation_log.append(f"Copied workflow: {target_workflow}")
                            else:
                                workflow_errors.append(f"Workflow source not found: {workflow_path}")
                                logger.warning(f"Workflow source not found: {workflow_path}")
                                
                        except Exception as workflow_error:
                            error_msg = f"Failed to copy workflow {workflow_config.get('id', 'unknown')}: {workflow_error}"
                            workflow_errors.append(error_msg)
                            logger.error(error_msg)
                            
                except Exception as e:
                    logger.error(f"Failed to process workflows: {e}")
                    workflow_errors.append(f"Workflows processing failed: {str(e)}")
            
            # 7. GENERATE PROJECT README
            try:
                readme_content = self._generate_project_readme(template_data, project_name, created_agents, project_root)
                readme_path = os.path.join(project_root, "CONDUCTOR_TEAM_README.md")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                operation_log.append(f"Generated README: {readme_path}")
            except Exception as e:
                logger.error(f"Failed to generate README: {e}")
                readme_path = None
            
            # 8. SUCCESS RESPONSE WITH COMPREHENSIVE DETAILS
            logger.info(f"Team template applied successfully: {len(created_agents)} agents created")
            
            return {
                'success': True,
                'team_applied': template_data.get('name', team_id),
                'project_path': target_agents_dir,
                'created_agents': created_agents,
                'skipped_agents': skipped_agents,
                'workflows_copied': workflows_copied,
                'workflow_errors': workflow_errors,
                'readme_created': readme_path,
                'backup_id': backup_id,
                'operation_log': operation_log,
                'validation_warnings': validation_result.get('warnings', [])
            }
            
        except Exception as e:
            # CRITICAL ERROR - PERFORM ROLLBACK
            error_msg = f"Critical error during team template application: {str(e)}"
            logger.error(error_msg)
            
            rollback_success = False
            rollback_error = None
            
            # Attempt rollback if backup was created
            if backup_id:
                try:
                    logger.info(f"Attempting rollback to backup: {backup_id}")
                    rollback_success = self._rollback_to_snapshot(project_root, env, project_name, backup_id)
                    if rollback_success:
                        logger.info("Rollback completed successfully")
                    else:
                        logger.error("Rollback failed")
                except Exception as rollback_exception:
                    rollback_error = str(rollback_exception)
                    logger.error(f"Rollback exception: {rollback_error}")
            
            return {
                'success': False,
                'error': error_msg,
                'backup_id': backup_id,
                'rollback_attempted': bool(backup_id),
                'rollback_success': rollback_success,
                'rollback_error': rollback_error,
                'operation_log': operation_log if 'operation_log' in locals() else []
            }
    
    def _generate_project_readme(self, template_data: Dict, project_name: str, created_agents: List, project_root: str) -> str:
        """Generate a README.md with usage examples for the applied team template."""
        
        readme_content = f"""# {template_data.get('name', 'Team')} - Conductor Setup

Este projeto foi configurado com o team template: **{template_data.get('id', 'unknown')}**

## Descrição
{template_data.get('description', 'No description available')}

## Agentes Criados

"""
        
        for agent in created_agents:
            readme_content += f"- **{agent['id']}**: Localizado em `{agent['path']}`\n"
        
        readme_content += f"""
## Exemplos de Uso

### Modo Interativo (Conversar com um agente)
```bash
# Incorporar um agente específico
python scripts/genesis_agent.py --environment develop --project {project_name} --agent [AGENT_ID] --repl
```

### Modo Automático (Executar workflows)
```bash
# Executar um workflow pré-configurado
python scripts/run_conductor.py --projeto {project_root} workflows/[WORKFLOW_NAME].yaml
```

## Próximos Passos

1. **Explore os agentes**: Use o modo interativo para conversar com cada agente
2. **Execute workflows**: Use os workflows pré-configurados para tarefas comuns  
3. **Customize**: Modifique os agent.yaml conforme suas necessidades

---
*Gerado automaticamente pelo Conductor Onboarding*
"""
        
        return readme_content
    
    def collect_user_profile(self) -> Dict[str, Any]:
        """
        Interactive tool to collect user profile through structured Q&A.
        This tool is designed to be called by AI agents to gather user information
        through natural conversation rather than forms.
        
        Returns:
            Dict with collected profile data and validation status
        """
        try:
            print("\n🎯 Vamos coletar algumas informações para personalizar sua experiência!")
            print("=" * 60)
            
            profile = {}
            
            # 1. Name collection
            while True:
                name = input("👤 Qual é o seu nome? ").strip()
                if name and len(name) >= 2:
                    profile['name'] = name
                    break
                print("   Por favor, digite um nome válido (mínimo 2 caracteres).")
            
            # 2. Role collection
            print(f"\n🎭 Qual é o seu papel principal, {profile['name']}?")
            print("   Opções: backend, frontend, fullstack, devops, scrum_master, tech_lead, other")
            while True:
                role = input("   Sua escolha: ").strip().lower()
                if role in VALID_ROLES:
                    profile['role'] = role
                    break
                print(f"   Opção inválida. Escolha entre: {', '.join(VALID_ROLES)}")
            
            # 3. Main language
            while True:
                language = input("\n💻 Qual é sua linguagem de programação principal? ").strip()
                if language and len(language) >= 2:
                    profile['main_language'] = language.lower()
                    break
                print("   Por favor, digite uma linguagem válida.")
            
            # 4. Main framework (optional)
            framework = input("🔧 Framework principal (opcional, Enter para pular): ").strip()
            profile['main_framework'] = framework.lower() if framework else None
            
            # 5. Experience level
            print("\n📊 Qual é o seu nível de experiência?")
            print("   Opções: junior, mid, senior")
            while True:
                experience = input("   Sua escolha: ").strip().lower()
                if experience in VALID_EXPERIENCE_LEVELS:
                    profile['experience_level'] = experience
                    break
                print(f"   Opção inválida. Escolha entre: {', '.join(VALID_EXPERIENCE_LEVELS)}")
            
            # 6. Project type
            print("\n📋 Tipo de projeto:")
            print("   Opções: new (novo projeto), existing (projeto existente)")
            while True:
                project_type = input("   Sua escolha: ").strip().lower()
                if project_type in VALID_PROJECT_TYPES:
                    profile['project_type'] = project_type
                    break
                print(f"   Opção inválida. Escolha entre: {', '.join(VALID_PROJECT_TYPES)}")
            
            # 7. Team size
            print("\n👥 Tamanho da equipe:")
            print("   Opções: solo (trabalhando sozinho), team (trabalhando em equipe)")
            while True:
                team_size = input("   Sua escolha: ").strip().lower()
                if team_size in VALID_TEAM_SIZES:
                    profile['team_size'] = team_size
                    break
                print(f"   Opção inválida. Escolha entre: {', '.join(VALID_TEAM_SIZES)}")
            
            # Add metadata
            profile['profile_complete'] = True
            profile['collected_at'] = datetime.now().isoformat()
            
            print(f"\n✅ Perfeito, {profile['name']}! Perfil coletado com sucesso.")
            print(f"   Papel: {profile['role']} | Linguagem: {profile['main_language']} | Nível: {profile['experience_level']}")
            
            return {
                'success': True,
                'profile': profile,
                'message': f'Perfil de {profile["name"]} coletado com sucesso'
            }
            
        except KeyboardInterrupt:
            return {
                'success': False,
                'error': 'Profile collection cancelled by user',
                'profile': {}
            }
        except Exception as e:
            logger.error(f"Failed to collect user profile: {e}")
            return {
                'success': False,
                'error': f"Profile collection failed: {str(e)}",
                'profile': {}
            }
    
    def collect_project_context(self) -> Dict[str, Any]:
        """
        Interactive tool to collect project context and validate project structure.
        
        Returns:
            Dict with project context data and validation status
        """
        try:
            print("\n📂 Agora vamos configurar o contexto do seu projeto!")
            print("=" * 60)
            
            context = {}
            
            # 1. Project name
            while True:
                project_name = input("📝 Nome do projeto: ").strip()
                if project_name and len(project_name) >= 2:
                    # Sanitize project name
                    context['project_name'] = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name)
                    if context['project_name'] != project_name:
                        print(f"   Nome sanitizado para: {context['project_name']}")
                    break
                print("   Por favor, digite um nome válido (mínimo 2 caracteres).")
            
            # 2. Project root path
            while True:
                project_root = input("📁 Caminho completo para o diretório do projeto: ").strip()
                if project_root:
                    # Expand user path and normalize
                    expanded_path = os.path.expanduser(project_root)
                    normalized_path = os.path.abspath(expanded_path)
                    
                    if os.path.exists(normalized_path):
                        context['project_root'] = normalized_path
                        break
                    else:
                        create_dir = input(f"   Diretório não existe. Criar '{normalized_path}'? (y/n): ").strip().lower()
                        if create_dir in ['y', 'yes', 's', 'sim']:
                            try:
                                os.makedirs(normalized_path, exist_ok=True)
                                context['project_root'] = normalized_path
                                print(f"   ✅ Diretório criado: {normalized_path}")
                                break
                            except Exception as e:
                                print(f"   ❌ Erro ao criar diretório: {e}")
                        else:
                            print("   Por favor, forneça um caminho válido ou permita a criação.")
                print("   Por favor, forneça um caminho válido.")
            
            # 3. Environment
            print("\n🌍 Ambiente de trabalho:")
            print("   Opções: develop (desenvolvimento), main (principal), production (produção)")
            while True:
                environment = input("   Sua escolha: ").strip().lower()
                if environment in VALID_ENVIRONMENTS:
                    context['environment'] = environment
                    break
                print(f"   Opção inválida. Escolha entre: {', '.join(VALID_ENVIRONMENTS)}")
            
            # 4. Check for existing structure
            conductor_structure_path = os.path.join(
                context['project_root'], 
                'projects', 
                context['environment'], 
                context['project_name'], 
                'agents'
            )
            
            context['existing_structure_detected'] = os.path.exists(conductor_structure_path)
            
            if context['existing_structure_detected']:
                print(f"\n⚠️  Detectei estrutura Conductor existente em:")
                print(f"   {conductor_structure_path}")
                
                existing_agents = []
                if os.path.isdir(conductor_structure_path):
                    existing_agents = [d for d in os.listdir(conductor_structure_path) 
                                     if os.path.isdir(os.path.join(conductor_structure_path, d))]
                
                if existing_agents:
                    print(f"   Agentes existentes: {', '.join(existing_agents)}")
                
                reconfigure = input("   Deseja reconfigurar ou adicionar agentes? (y/n): ").strip().lower()
                context['reconfigure_existing'] = reconfigure in ['y', 'yes', 's', 'sim']
            else:
                context['reconfigure_existing'] = False
            
            # 5. Determine if new project
            has_source_files = any(
                os.path.exists(os.path.join(context['project_root'], pattern))
                for pattern in ['src/', 'lib/', '*.py', '*.js', '*.kt', '*.java', '*.ts']
            )
            
            context['is_new_project'] = not has_source_files
            
            # Add metadata
            context['context_complete'] = True
            context['collected_at'] = datetime.now().isoformat()
            
            print(f"\n✅ Contexto do projeto '{context['project_name']}' configurado!")
            print(f"   Caminho: {context['project_root']}")
            print(f"   Ambiente: {context['environment']}")
            print(f"   Tipo: {'Projeto novo' if context['is_new_project'] else 'Projeto existente'}")
            
            return {
                'success': True,
                'context': context,
                'message': f'Contexto do projeto {context["project_name"]} coletado com sucesso'
            }
            
        except KeyboardInterrupt:
            return {
                'success': False,
                'error': 'Project context collection cancelled by user',
                'context': {}
            }
        except Exception as e:
            logger.error(f"Failed to collect project context: {e}")
            return {
                'success': False,
                'error': f"Project context collection failed: {str(e)}",
                'context': {}
            }
    
    @retry_on_failure(max_retries=2, recoverable_errors=RECOVERABLE_IO_ERRORS)
    @with_recovery_fallback(fallback_result={
        'success': True,
        'suggestions': [{'template_id': 'basic-team', 'template_name': 'Basic Team', 'score': 10, 'reasons': ['Fallback template'], 'confidence': 0.3}],
        'message': 'Using fallback suggestion due to system error'
    })
    def suggest_team_template(self, user_profile: Dict = None, project_context: Dict = None) -> Dict[str, Any]:
        """
        Suggest team templates based on user profile and project context.
        Uses a rules-based engine loaded from config/onboarding_rules.yaml.
        
        Args:
            user_profile: User profile data (optional, will use state if not provided)
            project_context: Project context data (optional, will use state if not provided)
            
        Returns:
            Dict with suggested templates and reasoning
        """
        try:
            # If no data provided, this is likely being called by AI - provide instructions
            if not user_profile and not project_context:
                return {
                    'success': True,
                    'message': 'Para usar esta ferramenta, primeiro colete o perfil do usuário e contexto do projeto',
                    'suggestions': [],
                    'instructions': [
                        'Use [TOOL_CALL: collect_user_profile] primeiro',
                        'Depois use [TOOL_CALL: collect_project_context]', 
                        'Então chame esta ferramenta novamente com os dados coletados'
                    ]
                }
            
            # Load rules configuration
            rules_config = self._load_onboarding_rules()
            if not rules_config:
                logger.warning("Failed to load onboarding rules, using fallback logic")
                return self._suggest_template_fallback(user_profile, project_context)
            
            # Get available team templates
            templates_result = self.list_team_templates()
            if not templates_result['success']:
                return templates_result
            
            available_templates = templates_result['available_templates']
            suggestions = []
            
            # Apply rules-based scoring using external configuration
            for template in available_templates:
                score = 0
                reasons = []
                template_id = template['id']
                
                # Apply role-based rules
                if user_profile and user_profile.get('role'):
                    role_score, role_reasons = self._apply_role_rules(
                        user_profile['role'], template_id, rules_config
                    )
                    score += role_score
                    reasons.extend(role_reasons)
                
                # Apply language-based rules
                if user_profile and user_profile.get('main_language'):
                    lang_score, lang_reasons = self._apply_language_rules(
                        user_profile['main_language'], template_id, rules_config
                    )
                    score += lang_score
                    reasons.extend(lang_reasons)
                
                # Apply experience adjustments
                if user_profile and user_profile.get('experience_level'):
                    exp_score, exp_reasons = self._apply_experience_rules(
                        user_profile['experience_level'], template, rules_config
                    )
                    score += exp_score
                    reasons.extend(exp_reasons)
                
                # Apply team size rules
                if user_profile and user_profile.get('team_size'):
                    team_score, team_reasons = self._apply_team_size_rules(
                        user_profile['team_size'], template, rules_config
                    )
                    score += team_score
                    reasons.extend(team_reasons)
                
                # Apply project type rules
                if project_context and project_context.get('is_new_project') is not None:
                    proj_score, proj_reasons = self._apply_project_type_rules(
                        project_context['is_new_project'], template, rules_config
                    )
                    score += proj_score
                    reasons.extend(proj_reasons)
                
                # Add suggestion if score is meaningful
                if score > 0:
                    max_score = rules_config.get('confidence_calculation', {}).get('max_possible_score', 100)
                    suggestions.append({
                        'template_id': template_id,
                        'template_name': template['name'],
                        'description': template['description'],
                        'score': score,
                        'reasons': reasons,
                        'agents_count': template.get('agents_count', 0),
                        'confidence': min(score / max_score, 1.0)
                    })
            
            # Sort by score (highest first)
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply fallback strategy if no good matches
            if not suggestions:
                suggestions = self._apply_fallback_strategy(available_templates, rules_config)
            
            # Limit to max suggestions
            max_suggestions = rules_config.get('max_suggestions', 3)
            top_suggestions = suggestions[:max_suggestions]
            
            return {
                'success': True,
                'suggestions': top_suggestions,
                'total_evaluated': len(available_templates),
                'top_recommendation': top_suggestions[0] if top_suggestions else None,
                'message': f'Encontradas {len(top_suggestions)} sugestões baseadas no seu perfil',
                'rules_version': rules_config.get('version', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to suggest team template: {e}")
            return {
                'success': False,
                'error': f"Template suggestion failed: {str(e)}",
                'suggestions': []
            }
    
    @retry_on_failure(max_retries=2, recoverable_errors=RECOVERABLE_IO_ERRORS)
    def _load_onboarding_rules(self) -> Dict[str, Any]:
        """Load onboarding rules configuration from YAML file."""
        try:
            rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'onboarding_rules.yaml')
            if not os.path.exists(rules_path):
                logger.warning(f"Onboarding rules file not found: {rules_path}")
                return {}
            
            with open(rules_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.debug(f"Loaded onboarding rules version: {config.get('version', 'unknown')}")
            return config
        except Exception as e:
            logger.error(f"Failed to load onboarding rules: {e}")
            return {}
    
    def _apply_role_rules(self, role: str, template_id: str, rules_config: Dict) -> Tuple[int, List[str]]:
        """Apply role-based scoring rules."""
        score = 0
        reasons = []
        
        role_rules = rules_config.get('suggestion_rules', {}).get('role_matching', {}).get(role, {})
        preferred_templates = role_rules.get('preferred_templates', [])
        
        for template_rule in preferred_templates:
            pattern = template_rule.get('pattern', '')
            if pattern and re.search(pattern, template_id, re.IGNORECASE):
                rule_score = template_rule.get('score', 0)
                reason = template_rule.get('reason', f'Match for {role}')
                score += rule_score
                reasons.append(reason)
                break  # Take first matching rule
        
        return score, reasons
    
    def _apply_language_rules(self, language: str, template_id: str, rules_config: Dict) -> Tuple[int, List[str]]:
        """Apply language-based scoring rules."""
        score = 0
        reasons = []
        
        lang_rules = rules_config.get('suggestion_rules', {}).get('language_matching', {}).get(language.lower(), {})
        preferred_templates = lang_rules.get('preferred_templates', [])
        
        for template_rule in preferred_templates:
            pattern = template_rule.get('pattern', '')
            if pattern and re.search(pattern, template_id, re.IGNORECASE):
                rule_score = template_rule.get('score', 0)
                reason = template_rule.get('reason', f'Match for {language}')
                score += rule_score
                reasons.append(reason)
                break  # Take first matching rule
        
        return score, reasons
    
    def _apply_experience_rules(self, experience: str, template: Dict, rules_config: Dict) -> Tuple[int, List[str]]:
        """Apply experience level adjustments."""
        score = 0
        reasons = []
        
        exp_rules = rules_config.get('suggestion_rules', {}).get('experience_adjustments', {}).get(experience, {})
        preferences = exp_rules.get('preferences', [])
        
        agents_count = template.get('agents_count', 0)
        template_complexity = template.get('complexity', 'basic')  # Default to basic if not specified
        
        for pref in preferences:
            condition = pref.get('condition', '')
            # Simple condition evaluation
            if self._evaluate_condition(condition, agents_count, template_complexity):
                rule_score = pref.get('score_bonus', 0)
                reason = pref.get('reason', f'Suitable for {experience} level')
                score += rule_score
                reasons.append(reason)
        
        return score, reasons
    
    def _apply_team_size_rules(self, team_size: str, template: Dict, rules_config: Dict) -> Tuple[int, List[str]]:
        """Apply team size considerations."""
        score = 0
        reasons = []
        
        team_rules = rules_config.get('suggestion_rules', {}).get('team_size_matching', {}).get(team_size, {})
        preferences = team_rules.get('preferences', [])
        
        agents_count = template.get('agents_count', 0)
        template_focus = template.get('focus', 'productivity')  # Default focus
        
        for pref in preferences:
            condition = pref.get('condition', '')
            if self._evaluate_condition(condition, agents_count, template_focus):
                rule_score = pref.get('score_bonus', 0)
                reason = pref.get('reason', f'Suitable for {team_size}')
                score += rule_score
                reasons.append(reason)
        
        return score, reasons
    
    def _apply_project_type_rules(self, is_new_project: bool, template: Dict, rules_config: Dict) -> Tuple[int, List[str]]:
        """Apply project type considerations."""
        score = 0
        reasons = []
        
        project_type = 'new' if is_new_project else 'existing'
        proj_rules = rules_config.get('suggestion_rules', {}).get('project_type_matching', {}).get(project_type, {})
        preferences = proj_rules.get('preferences', [])
        
        template_includes = template.get('includes', [])
        template_focus = template.get('focus', 'general')
        
        for pref in preferences:
            condition = pref.get('condition', '')
            if self._evaluate_template_condition(condition, template_includes, template_focus):
                rule_score = pref.get('score_bonus', 0)
                reason = pref.get('reason', f'Good for {project_type} projects')
                score += rule_score
                reasons.append(reason)
        
        return score, reasons
    
    def _evaluate_condition(self, condition: str, agents_count: int, attribute: str) -> bool:
        """Evaluate simple conditions like 'agents_count <= 3'."""
        try:
            # Replace variables in condition
            condition = condition.replace('agents_count', str(agents_count))
            condition = condition.replace('template_complexity', f'"{attribute}"')
            condition = condition.replace('template_focus', f'"{attribute}"')
            
            # Simple evaluation for basic conditions
            if '<=' in condition:
                parts = condition.split('<=')
                if len(parts) == 2:
                    return int(parts[0].strip()) <= int(parts[1].strip())
            elif '>=' in condition:
                parts = condition.split('>=')
                if len(parts) == 2:
                    return int(parts[0].strip()) >= int(parts[1].strip())
            elif '==' in condition:
                parts = condition.split('==')
                if len(parts) == 2:
                    left = parts[0].strip().strip('"')
                    right = parts[1].strip().strip('"')
                    return left == right
            elif 'AND' in condition:
                sub_conditions = condition.split('AND')
                return all(self._evaluate_condition(sub.strip(), agents_count, attribute) for sub in sub_conditions)
        except:
            pass
        return False
    
    def _evaluate_template_condition(self, condition: str, template_includes: List, template_focus: str) -> bool:
        """Evaluate template-specific conditions."""
        try:
            if 'template_includes' in condition:
                target = condition.split('==')[1].strip().strip('"\'')
                return target in template_includes
            elif 'template_focus' in condition:
                target = condition.split('==')[1].strip().strip('"\'')
                return template_focus == target
        except:
            pass
        return False
    
    def _apply_fallback_strategy(self, available_templates: List[Dict], rules_config: Dict) -> List[Dict]:
        """Apply fallback strategy when no templates match."""
        fallback = rules_config.get('fallback_strategy', {})
        default_patterns = fallback.get('default_template_patterns', ['.*basic.*'])
        fallback_score = fallback.get('fallback_score', 10)
        fallback_reason = fallback.get('fallback_reason', 'Template versátil recomendado')
        
        suggestions = []
        for template in available_templates:
            for pattern in default_patterns:
                if re.search(pattern, template['id'], re.IGNORECASE):
                    suggestions.append({
                        'template_id': template['id'],
                        'template_name': template['name'],
                        'description': template['description'],
                        'score': fallback_score,
                        'reasons': [fallback_reason],
                        'agents_count': template.get('agents_count', 0),
                        'confidence': fallback.get('minimum_confidence', 0.3)
                    })
                    break
        
        return suggestions
    
    def _suggest_template_fallback(self, user_profile: Dict, project_context: Dict) -> Dict[str, Any]:
        """Fallback suggestion logic when rules config fails to load."""
        logger.warning("Using hardcoded fallback suggestion logic")
        
        # Get available team templates
        templates_result = self.list_team_templates()
        if not templates_result['success']:
            return templates_result
        
        available_templates = templates_result['available_templates']
        
        # Simple hardcoded logic as fallback
        if available_templates:
            basic_template = available_templates[0]  # Take first available
            return {
                'success': True,
                'suggestions': [{
                    'template_id': basic_template['id'],
                    'template_name': basic_template['name'],
                    'description': basic_template['description'],
                    'score': 20,
                    'reasons': ['Fallback: Template básico selecionado'],
                    'agents_count': basic_template.get('agents_count', 0),
                    'confidence': 0.4
                }],
                'total_evaluated': len(available_templates),
                'top_recommendation': {
                    'template_id': basic_template['id'],
                    'template_name': basic_template['name'],
                    'description': basic_template['description'],
                    'score': 20,
                    'reasons': ['Fallback: Template básico selecionado'],
                    'agents_count': basic_template.get('agents_count', 0),
                    'confidence': 0.4
                },
                'message': '1 sugestão encontrada (modo fallback)'
            }
        
        return {
            'success': False,
            'error': 'No templates available',
            'suggestions': []
        }
    
    @retry_on_failure(max_retries=3, recoverable_errors=RECOVERABLE_IO_ERRORS)
    @safe_file_operation(create_backup=False)  # Don't backup for new file creation
    def create_example_project(self, project_root: str, team_template_id: str, user_profile: Dict = None) -> Dict[str, Any]:
        """
        Create a "Hello World" example project based on the selected team template and user profile.
        Uses external template files for better maintainability.
        
        Args:
            project_root: Target project root directory
            team_template_id: ID of the applied team template
            user_profile: User profile for language/framework selection
            
        Returns:
            Dict with created files and success status
        """
        try:
            # Determine project context
            project_context = self._determine_project_context(team_template_id, user_profile)
            
            # Create examples directory
            examples_dir = os.path.join(project_root, 'examples')
            os.makedirs(examples_dir, exist_ok=True)
            
            # Template variables for substitution
            template_vars = {
                'project_name': os.path.basename(project_root),
                'team_name': project_context['team_name'],
                'team_id': team_template_id,
                'project_root': project_root,
                'environment': 'develop',  # Default environment
                'generated_at': datetime.now().isoformat(),
                'system_version': '1.0'
            }
            
            created_files = []
            
            # Create language-specific examples using external templates
            template_files = self._get_template_files_for_language(project_context['language'])
            
            for template_info in template_files:
                try:
                    output_file = self._create_file_from_template(
                        template_info, examples_dir, template_vars
                    )
                    if output_file:
                        created_files.append(output_file)
                        logger.info(f"Created example file: {output_file}")
                except Exception as e:
                    logger.warning(f"Failed to create template {template_info['template']}: {e}")
                    # Continue with other templates
            
            # Always create README
            readme_file = self._create_readme_from_template(project_root, template_vars, created_files)
            if readme_file:
                created_files.append(readme_file)
            
            return {
                'success': True,
                'created_files': created_files,
                'project_type': project_context['language'],
                'team_name': project_context['team_name'],
                'message': f'Exemplo criado com {len(created_files)} arquivos para {project_context["language"]}'
            }
            
        except Exception as e:
            logger.error(f"Failed to create example project: {e}")
            return {
                'success': False,
                'error': f"Example project creation failed: {str(e)}",
                'created_files': []
            }
    
    def _determine_project_context(self, team_template_id: str, user_profile: Dict = None) -> Dict[str, str]:
        """Determine project context from template and profile."""
        context = {
            'language': 'python',  # Default
            'framework': 'basic',
            'team_name': 'Generic Development Team'
        }
        
        # Determine from team template ID
        if 'kotlin' in team_template_id:
            context.update({
                'language': 'kotlin',
                'framework': 'spring-boot',
                'team_name': 'Kotlin Backend Team'
            })
        elif 'react' in team_template_id:
            context.update({
                'language': 'typescript',
                'framework': 'react',
                'team_name': 'React Frontend Team'
            })
        elif 'devops' in team_template_id:
            context.update({
                'language': 'yaml',
                'framework': 'docker',
                'team_name': 'DevOps Infrastructure Team'
            })
        elif user_profile:
            # Use profile info if available
            context.update({
                'language': user_profile.get('main_language', 'python'),
                'framework': user_profile.get('main_framework', 'basic'),
                'team_name': f"{user_profile.get('main_language', 'Python').title()} Development Team"
            })
        
        return context
    
    def _get_template_files_for_language(self, language: str) -> List[Dict[str, str]]:
        """Get template files for specific language."""
        templates_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'examples')
        
        if language == 'kotlin':
            return [
                {
                    'template': 'kotlin-spring-boot.kt',
                    'output': 'HelloWorld.kt',
                    'description': 'Kotlin Spring Boot REST API example'
                }
            ]
        elif language in ['typescript', 'javascript']:
            return [
                {
                    'template': 'react-component.tsx',
                    'output': 'HelloConductor.tsx',
                    'description': 'React TypeScript component example'
                }
            ]
        elif language == 'yaml':
            return [
                {
                    'template': 'docker-compose.yml',
                    'output': 'docker-compose.yml',
                    'description': 'Docker Compose configuration'
                },
                {
                    'template': 'hello.html',
                    'output': 'hello.html',
                    'description': 'HTML page for nginx container'
                }
            ]
        else:
            # Default to Python
            return [
                {
                    'template': 'python-hello.py',
                    'output': 'hello_conductor.py',
                    'description': 'Python hello world script'
                }
            ]
    
    def _create_file_from_template(self, template_info: Dict, output_dir: str, template_vars: Dict) -> Optional[str]:
        """Create file from template with variable substitution."""
        try:
            templates_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'examples')
            template_path = os.path.join(templates_base, template_info['template'])
            
            if not os.path.exists(template_path):
                logger.warning(f"Template file not found: {template_path}")
                return None
            
            # Read template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Simple variable substitution
            for var, value in template_vars.items():
                template_content = template_content.replace(f'{{{{{var}}}}}', str(value))
            
            # Write output file
            output_path = os.path.join(output_dir, template_info['output'])
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create file from template {template_info['template']}: {e}")
            return None
    
    def _create_readme_from_template(self, project_root: str, template_vars: Dict, created_files: List[str]) -> Optional[str]:
        """Create README from template."""
        try:
            templates_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'examples')
            template_path = os.path.join(templates_base, 'README_template.md')
            
            if not os.path.exists(template_path):
                # Fallback to simple README
                readme_content = f"""# 🎼 {template_vars['project_name']} - Conductor Example Project

Projeto criado pelo **{template_vars['team_name']}**!

## 📁 Arquivos Criados

{chr(10).join(f'- `{os.path.basename(f)}`' for f in created_files)}

## 🚀 Próximos Passos

1. Explore os agentes no diretório: `{template_vars['project_root']}/projects/{template_vars['environment']}/{template_vars['project_name']}/agents/`
2. Inicie uma conversa: `python scripts/genesis_agent.py --environment {template_vars['environment']} --project {template_vars['project_name']} --agent [AGENT] --repl`

---
*Gerado pelo Conductor Onboarding v{template_vars['system_version']}*
"""
            else:
                # Use template file
                with open(template_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                # Variable substitution
                for var, value in template_vars.items():
                    readme_content = readme_content.replace(f'{{{{{var}}}}}', str(value))
                
                # Handle file lists (simplified)
                files_list = '\n'.join(f'- `{os.path.basename(f)}`: Exemplo gerado automaticamente' for f in created_files)
                readme_content = readme_content.replace('{{#created_files}}', '').replace('{{/created_files}}', '')
                readme_content = readme_content.replace('- `{{file_path}}`: {{file_description}}', files_list)
            
            # Write README
            readme_path = os.path.join(project_root, 'CONDUCTOR_EXAMPLE_README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            return readme_path
            
        except Exception as e:
            logger.error(f"Failed to create README: {e}")
            return None



class LLMClient:
    """
    Base LLM Client interface for multi-provider support.
    
    This abstract base class defines the common interface for different AI providers,
    enabling dynamic provider selection based on agent configuration.
    """

    
    def __init__(self, working_directory: str = None):
        """
        Initialize the base LLM Client.
        
        Args:
            working_directory: Working directory for subprocess calls
        """
        self.working_directory = working_directory or os.getcwd()
        self.conversation_history = []
        self.agent_persona = None
        
        logger.debug(f"LLMClient base initialized with working directory: {self.working_directory}")
    
    def set_agent_persona(self, persona: str):
        """
        Set the agent persona for this LLM client.
        
        Args:
            persona: The agent's persona text from persona.md
        """
        self.agent_persona = persona
        logger.debug("Agent persona set in LLM client")
    
    def generate_artifact(self, prompt: str) -> str:
        """
        Generate an artifact using this LLM client.
        Base implementation just calls _invoke_subprocess.
        """
        return self._invoke_subprocess(prompt) or "No response generated."
    
    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        """
        Abstract method for invoking AI via subprocess.
        Must be implemented by provider-specific subclasses.
        
        Args:
            prompt: The prompt to send to the AI provider
            
        Returns:
            AI response or None if failed
        """
        raise NotImplementedError("Provider-specific subclasses must implement _invoke_subprocess")


class ClaudeCLIClient(LLMClient):
    """
    Claude CLI Client implementation.
    
    This client uses the official Claude CLI to interact with Anthropic's Claude API.
    It provides a robust interface for conversational AI interactions with proper
    error handling and conversation history management.
    """
    
    def __init__(self, working_directory: str = None):
        """
        Initialize the Claude CLI Client.
        
        Args:
            working_directory: Working directory for subprocess calls
        """
        super().__init__(working_directory)
        self.claude_command = "claude"
        logger.debug("ClaudeCLIClient initialized")
    
    def _build_contextual_prompt(self, new_prompt: str) -> str:
        """
        Build a prompt that includes conversation history for context.
        Uses intelligent context compression to avoid token overflow.
        
        Args:
            new_prompt: The new user prompt
            
        Returns:
            Full prompt including conversation context (optimized)
        """
        if not self.conversation_history:
            return new_prompt
        
        # Check if this looks like an AgentCreator session with collected specs
        if self._is_agent_creation_session():
            return self._build_agent_creation_context(new_prompt)
        
        # For other conversations, use limited recent context
        context_parts = ["Recent conversation:"]
        
        # Only include last 3 messages to keep context manageable
        max_context_messages = 3
        recent_history = self.conversation_history[-max_context_messages:]
        
        for entry in recent_history:
            user_msg = entry.get('prompt', '').strip()
            assistant_msg = entry.get('response', '').strip()
            
            # Truncate long messages to essential parts
            if user_msg:
                user_summary = user_msg[:150] + "..." if len(user_msg) > 150 else user_msg
                context_parts.append(f"User: {user_summary}")
            if assistant_msg:
                assistant_summary = assistant_msg[:200] + "..." if len(assistant_msg) > 200 else assistant_msg
                context_parts.append(f"Assistant: {assistant_summary}")
        
        context_parts.append("\nCurrent message:")
        context_parts.append(f"User: {new_prompt}")
        
        return "\n".join(context_parts)
    
    def _is_agent_creation_session(self) -> bool:
        """
        Detect if this is an AgentCreator session collecting agent specifications.
        """
        if len(self.conversation_history) < 2:
            return False
        
        # Look for agent creation keywords in conversation
        recent_messages = self.conversation_history[-5:]
        agent_keywords = ['ambiente', 'projeto', 'agente', 'agent', 'cURL', 'QA', 'documentation']
        
        for entry in recent_messages:
            response = entry.get('response', '').lower()
            if any(keyword in response for keyword in agent_keywords):
                return True
        
        return False
    
    def _build_agent_creation_context(self, new_prompt: str) -> str:
        """
        Build optimized context for agent creation sessions.
        Extracts and summarizes collected specifications instead of full history.
        """
        context_parts = ["Agent creation session in progress:"]
        
        # Extract key information from conversation history
        extracted_specs = self._extract_agent_specifications()
        
        if extracted_specs:
            context_parts.append("Collected specifications:")
            for key, value in extracted_specs.items():
                if value:
                    context_parts.append(f"- {key}: {value}")
        
        # Add only the most recent exchange for immediate context
        if self.conversation_history:
            last_entry = self.conversation_history[-1]
            last_response = last_entry.get('response', '')
            if last_response:
                # Truncate to key points
                response_summary = last_response[:300] + "..." if len(last_response) > 300 else last_response
                context_parts.append(f"\nLast response: {response_summary}")
        
        context_parts.append(f"\nCurrent message: {new_prompt}")
        
        return "\n".join(context_parts)
    
    def _extract_agent_specifications(self) -> dict:
        """
        Extract agent specifications from conversation history.
        Returns structured data instead of raw conversation.
        """
        specs = {
            'ambiente': None,
            'projeto': None,
            'nome_agente': None,
            'funcionalidade': None,
            'publico_alvo': None,
            'provedor_ia': None,
            'ferramentas': None,
            'conteudo_doc': [],
            'regras_formatacao': [],
            'informacoes_adicionais': []
        }
        
        # Parse conversation history for key information
        for entry in self.conversation_history:
            response = entry.get('response', '')
            
            # Extract environment
            if 'ambiente' in response.lower() and 'develop' in response:
                specs['ambiente'] = 'develop'
            
            # Extract project
            if 'projeto' in response.lower():
                if 'nex-web-backend' in response:
                    specs['projeto'] = 'nex-web-backend'
            
            # Extract agent name
            if 'nome' in response.lower() and 'agent' in response:
                if 'QADocumentationAgent_Agent' in response:
                    specs['nome_agente'] = 'QADocumentationAgent_Agent'
            
            # Extract functionality
            if 'documentação técnica' in response.lower():
                specs['funcionalidade'] = 'Gerar documentação técnica'
            
            # Extract target audience
            if 'QA' in response and 'time' in response.lower():
                specs['publico_alvo'] = 'Time de QA'
            
            # Extract content requirements
            if 'cURL' in response:
                if 'cURL' not in specs['conteudo_doc']:
                    specs['conteudo_doc'].append('Comando cURL')
            if 'JSON' in response and 'exemplo' in response.lower():
                if 'Exemplos JSON' not in specs['conteudo_doc']:
                    specs['conteudo_doc'].append('Exemplos JSON')
            if 'status code' in response.lower():
                if 'Status codes' not in specs['conteudo_doc']:
                    specs['conteudo_doc'].append('Status codes')
            
            # Extract formatting rules
            if 'aspas duplas' in response.lower():
                if 'Aspas duplas' not in specs['regras_formatacao']:
                    specs['regras_formatacao'].append('URLs com aspas duplas')
            if '{{' in response and '}}' in response:
                if 'Postman vars' not in specs['regras_formatacao']:
                    specs['regras_formatacao'].append('Variáveis Postman {{var}}')
        
        return specs
    
    def _build_full_prompt_with_persona(self, new_prompt: str) -> str:
        """
        Build a complete prompt that includes persona and conversation context.
        
        Args:
            new_prompt: The new user prompt
            
        Returns:
            Complete prompt with persona and context
        """
        prompt_parts = []
        
        # Add persona if available
        if self.agent_persona:
            prompt_parts.append("### PERSONA:")
            prompt_parts.append(self.agent_persona)
            prompt_parts.append("")  # Empty line separator
        
        # Add contextual conversation
        contextual_prompt = self._build_contextual_prompt(new_prompt)
        prompt_parts.append(contextual_prompt)
        
        return "\n".join(prompt_parts)
    
    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        """
        Invoke Claude CLI with the given prompt including conversation context.
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Claude's response or None if failed
        """
        try:
            # Build full prompt with persona and conversation context
            full_prompt = self._build_full_prompt_with_persona(prompt)
            
            # Build command with proper arguments and allowed tools
            cmd = [self.claude_command, "--print"]
            
            # Add allowed tools based on agent configuration
            # Check if we have access to agent's available tools via genesis_agent reference
            if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'get_available_tools'):
                available_tools = self.genesis_agent.get_available_tools()
                if available_tools:
                    tools_str = " ".join(available_tools)
                    cmd.extend(["--allowedTools", tools_str])
                    logger.debug(f"Adding allowed tools: {tools_str}")
            else:
                # Fallback: allow common tools for file operations
                if "Write" in prompt or "write_file" in prompt or "criar arquivo" in prompt.lower() or "salvar" in prompt.lower():
                    cmd.extend(["--allowedTools", "Write Edit Bash Read Grep Glob LS"])
                    logger.debug("Adding fallback allowed tools for file operations")
            
            # Use stdin instead of command line argument for better compatibility
            input_text = full_prompt
            
            # Debug: log the command being executed
            logger.debug(f"Executing Claude CLI command: {' '.join(cmd[:3])} ... [prompt]")
            
            # Execute Claude CLI with reasonable timeout using stdin
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=90,  # Increased timeout for complex operations like agent generation
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                if response:
                    # Add to conversation history
                    self.conversation_history.append({
                        'prompt': prompt,
                        'response': response,
                        'timestamp': time.time()
                    })
                    
                    logger.debug(f"Claude CLI response: {response[:100]}...")
                    return response
                else:
                    logger.warning("Claude CLI returned empty response")
                    return None
            else:
                logger.error(f"Claude CLI failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timed out after 90 seconds")
            return "❌ Claude CLI timed out after 90 seconds. Complex operations may need more time."
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return f"❌ Claude CLI error: {e}"


class GeminiCLIClient(LLMClient):
    """
    Gemini CLI Client implementation.
    
    This client interfaces with Google's Gemini AI through command-line tools.
    It provides similar functionality to Claude but using Google's AI models.
    """
    
    def __init__(self, working_directory: str = None):
        """
        Initialize the Gemini CLI Client.
        
        Args:
            working_directory: Working directory for subprocess calls
        """
        super().__init__(working_directory)
        self.gemini_command = ["npx", "--yes", "@google/gemini-cli"]
        logger.debug("GeminiCLIClient initialized")
    
    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        """
        Invoke Gemini CLI with the given prompt.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Gemini's response or None if failed
        """
        try:
            # Build command for Gemini exactly like focused_gemini_orchestrator.py
            cmd = self.gemini_command.copy()
            cmd.extend(["--prompt", prompt])
            
            # Add tool approval mode for file operations
            if "Write" in prompt or "write_file" in prompt or "criar arquivo" in prompt.lower() or "salvar" in prompt.lower():
                cmd.extend(["--approval-mode", "yolo"])  # Use yolo for auto-approval
                logger.debug("Adding yolo approval mode for file operations")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                if response:
                    self.conversation_history.append({
                        'prompt': prompt,
                        'response': response,
                        'timestamp': time.time()
                    })
                    logger.debug(f"Gemini CLI response: {response[:100]}...")
                    return response
                else:
                    logger.warning("Gemini CLI returned empty response")
                    return None
            else:
                logger.error(f"Gemini CLI failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Gemini CLI timed out")
            return None
        except Exception as e:
            logger.error(f"Gemini CLI error: {e}")
            return None


def create_llm_client(ai_provider: str, working_directory: str = None) -> LLMClient:
    """
    Factory function to create LLM clients based on provider.
    
    Args:
        ai_provider: The AI provider to use ('claude', 'gemini')
        working_directory: Working directory for subprocess calls
        
    Returns:
        Configured LLM client instance
        
    Raises:
        ValueError: If unsupported provider is specified
    """
    if ai_provider == 'claude':
        return ClaudeCLIClient(working_directory)
    elif ai_provider == 'gemini':
        return GeminiCLIClient(working_directory)
    else:
        raise ValueError(f"Unsupported AI provider: {ai_provider}. Supported providers: 'claude', 'gemini'")


# Workspace Resolution Functions for v2.0 Architecture
def load_workspaces_config() -> Dict[str, str]:
    """
    Carrega a configuração de workspaces do arquivo config/workspaces.yaml.
    
    Returns:
        Dict com mapeamento environment -> path
        
    Raises:
        FileNotFoundError: Se o arquivo de configuração não existir
        yaml.YAMLError: Se houver erro de parsing do YAML
    """
    config_path = Path(__file__).parent.parent / WORKSPACES_CONFIG_PATH
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração de workspaces não encontrado: {config_path}\n"
            f"Crie o arquivo com o mapeamento de ambientes para seus diretórios."
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'workspaces' not in config:
            raise ValueError("Arquivo workspaces.yaml deve conter uma seção 'workspaces'")
        
        return config['workspaces']
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Erro ao fazer parse do workspaces.yaml: {e}")


# Functions moved to agent_common.py:
# - load_ai_providers_config()
# - resolve_agent_paths()
# - load_agent_config_v2()


class GenesisAgent:
    """
    Main Genesis Agent class implementing the "embodiment" functionality.
    
    This class is responsible for loading and incorporating specialist agents
    as defined in the Maestro framework specification.
    """
    
    def __init__(self, environment: str = None, project: str = None, agent_id: str = None, 
                 ai_provider: str = None):
        """
        Initialize the Genesis Agent for v2.0 architecture.
        
        Args:
            environment: Nome do ambiente (develop, main, etc.) - obrigatório para v2.0
            project: Nome do projeto alvo - obrigatório para v2.0
            agent_id: ID do agente para embodiment - opcional, pode ser feito depois
            ai_provider: AI provider override - se não especificado, usa configuração dual por tarefa
        """
        # Load AI providers configuration for dual provider logic
        self.ai_providers_config = load_ai_providers_config()
        self.ai_provider_override = ai_provider  # Agent-specific override if provided
        
        # Agent state
        self.current_agent = None
        self.embodied = False
        self.agent_config = None
        self.agent_home_path = None
        self.project_root_path = None
        
        # Salva CWD original para restaurar, com fallback se diretório foi deletado
        try:
            self.original_cwd = os.getcwd()
        except FileNotFoundError:
            # Se CWD atual foi removido, use um diretório seguro
            self.original_cwd = str(Path.home())
            os.chdir(self.original_cwd)
        
        # v2.0 Architecture - Project Resident Mode
        if environment and project:
            self.environment = environment
            self.project = project
            
            try:
                # Resolve paths usando nova arquitetura
                if agent_id:
                    self.agent_home_path, self.project_root_path = resolve_agent_paths(
                        environment, project, agent_id
                    )
                    logger.info(f"v2.0 Mode: Paths resolved for {agent_id}")
                    logger.info(f"Agent Home: {self.agent_home_path}")
                    logger.info(f"Project Root: {self.project_root_path}")
                else:
                    # Só resolve workspace root por enquanto
                    workspaces = load_workspaces_config()
                    workspace_root = Path(workspaces[environment])
                    self.project_root_path = workspace_root / project
                    
                    if not self.project_root_path.exists():
                        raise ValueError(f"Projeto não encontrado: {self.project_root_path}")
                    
                    logger.info(f"v2.0 Mode: Workspace resolved for {environment}/{project}")
                    logger.info(f"Project Root: {self.project_root_path}")
                
                # Define working directory como projeto alvo
                self.working_directory = str(self.project_root_path)
                
            except Exception as e:
                logger.error(f"Erro ao resolver paths v2.0: {e}")
                raise
        else:
            logger.warning("Inicializando sem environment/project - use embody_agent_v2() depois")
            self.environment = environment
            self.project = project
            self.working_directory = os.getcwd()
        
        # Initialize LLM client - will be set when agent is embodied
        self.llm_client = None
        
        # Initialize toolbelt
        self.toolbelt = Toolbelt(self.working_directory, genesis_agent=self)
        
        logger.info(f"GenesisAgent initialized (v2.0) with dual provider support")
    
    def resolve_provider_for_task(self, task_type: str) -> str:
        """
        Resolve qual provedor de IA usar baseado no tipo de tarefa.
        
        Args:
            task_type: 'chat' para conversação ou 'generation' para geração de artefatos
            
        Returns:
            Nome do provedor a ser usado
        """
        # 1. Agent-specific override has highest priority
        if self.ai_provider_override:
            logger.debug(f"Using agent override provider: {self.ai_provider_override}")
            return self.ai_provider_override
        
        # 2. Agent config ai_provider has second priority
        if hasattr(self, 'agent_config') and self.agent_config:
            agent_provider = self.agent_config.get('ai_provider')
            if agent_provider:
                logger.debug(f"Using agent config provider: {agent_provider}")
                return agent_provider
        
        # 3. Use task-specific default from ai_providers.yaml
        default_providers = self.ai_providers_config.get('default_providers', {})
        provider = default_providers.get(task_type)
        
        if provider:
            logger.debug(f"Using task-specific provider for {task_type}: {provider}")
            return provider
        
        # 4. Fallback to configured fallback provider
        fallback = self.ai_providers_config.get('fallback_provider', 'claude')
        logger.warning(f"No provider found for task {task_type}, using fallback: {fallback}")
        return fallback
    
    def get_chat_provider(self) -> str:
        """Resolve provedor para tarefas de chat/conversação."""
        return self.resolve_provider_for_task('chat')
    
    def get_generation_provider(self) -> str:
        """Resolve provedor para tarefas de geração de artefatos."""
        return self.resolve_provider_for_task('generation')
    
    def embody_agent_v2(self, agent_id: str) -> bool:
        """
        Embody um agente usando a nova arquitetura v2.0 com Project Resident Mode.
        
        Args:
            agent_id: ID do agente para embodiment
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            if not self.environment or not self.project:
                raise ValueError("Environment e project devem estar definidos para usar embody_agent_v2()")
            
            # Resolve caminhos do agente e projeto usando função compartilhada
            self.agent_home_path, self.project_root_path = resolve_agent_paths(
                self.environment, self.project, agent_id
            )
            
            # Carrega configuração do agente v2.0 usando função compartilhada
            self.agent_config = load_agent_config_v2(self.agent_home_path)
            
            # Validate configuration using shared function
            validate_agent_config(self.agent_config)
            
            # Initialize LLM client with chat provider (default for conversation)
            chat_provider = self.get_chat_provider()
            self.llm_client = create_llm_client(chat_provider, str(self.project_root_path))
            logger.info(f"Initialized LLM client with chat provider: {chat_provider}")
            
            # FUNDAMENTAL: Muda para o diretório do projeto alvo (Project Resident Mode)
            logger.info(f"Changing working directory to project: {self.project_root_path}")
            os.chdir(str(self.project_root_path))
            
            # Atualiza working directory de todos os componentes
            self.working_directory = str(self.project_root_path)
            self.toolbelt.working_directory = str(self.project_root_path)
            
            # Carrega estado do agente (usando caminho absoluto)
            state_file_path = self.agent_home_path / self.agent_config.get("state_file_path", "state.json")
            self._load_agent_state_v2(str(state_file_path))
            
            # Carrega persona do agente (usando caminho absoluto)
            persona_path = self.agent_home_path / self.agent_config.get("persona_prompt_path", "persona.md")
            if not self._load_agent_persona(str(persona_path), agent_id):
                return False
            
            # Salva paths absolutos para gestão de estado
            self.state_file_path = str(state_file_path)
            
            # Marca agente como embodied
            self.current_agent = agent_id
            self.embodied = True
            
            logger.info(f"Successfully embodied agent v2.0: {agent_id}")
            logger.info(f"Agent Home: {self.agent_home_path}")
            logger.info(f"Project Root (CWD): {self.project_root_path}")
            logger.info(f"State File: {self.state_file_path}")
            
            # Configura validação de output_scope se aplicável
            target_context = self.agent_config.get('target_context')
            if target_context and 'output_scope' in target_context:
                self.output_scope = target_context['output_scope']
                logger.info(f"Output scope configured: {self.output_scope}")
            else:
                self.output_scope = None
                logger.info("No output scope restriction (meta-agent)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to embody agent v2.0 {agent_id}: {e}")
            # Restaura CWD original em caso de erro
            try:
                os.chdir(self.original_cwd)
            except:
                pass
            return False
    
    def _load_agent_state_v2(self, state_file_path: str):
        """
        Carrega estado do agente v2.0 usando caminho absoluto.
        
        Args:
            state_file_path: Caminho absoluto para o state.json
        """
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # Carrega conversation history se existir
                if 'conversation_history' in state_data and isinstance(state_data['conversation_history'], list):
                    self.llm_client.conversation_history = state_data['conversation_history']
                    logger.info(f"Loaded conversation history: {len(self.llm_client.conversation_history)} messages")
                else:
                    self.llm_client.conversation_history = []
                    logger.info("No conversation history found, starting fresh")
                
                # Carrega outras informações de estado
                if 'last_modified' in state_data:
                    logger.info(f"Last modified: {state_data['last_modified']}")
            else:
                logger.info(f"No state file found at {state_file_path}, starting fresh")
                self.llm_client.conversation_history = []
                
        except Exception as e:
            logger.warning(f"Could not load agent state from {state_file_path}: {e}")
            self.llm_client.conversation_history = []
    
    def save_agent_state_v2(self):
        """
        Salva estado do agente v2.0 usando caminho absoluto.
        """
        if not self.state_file_path:
            logger.warning("No state file path configured for v2.0 agent")
            return
        
        try:
            state_data = {
                'conversation_history': self.llm_client.conversation_history,
                'last_modified': datetime.now().isoformat(),
                'agent_id': self.current_agent,
                'environment': self.environment,
                'project': self.project
            }
            
            # Garante que o diretório do agente existe
            state_file = Path(self.state_file_path)
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Agent state saved to: {self.state_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save agent state v2.0: {e}")
    
    def _load_agent_persona(self, persona_path: str, agent_name: str = None) -> bool:
        """
        Load agent persona from persona.md file and resolve placeholders.
        
        Args:
            persona_path: Path to the persona.md file
            agent_name: Name of the agent (for placeholder resolution)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(persona_path):
                with open(persona_path, 'r', encoding='utf-8') as f:
                    persona_content = f.read()
                
                # Resolve placeholders in persona content
                self.agent_persona = self._resolve_persona_placeholders(persona_content, agent_name)
                
                # Pass persona to LLM client if it supports it
                if hasattr(self.llm_client, 'set_agent_persona'):
                    self.llm_client.set_agent_persona(self.agent_persona)
                
                logger.debug(f"Loaded and processed persona from {persona_path}")
                return True
            else:
                logger.error(f"Persona file not found: {persona_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading agent persona: {e}")
            return False
    
    def _resolve_persona_placeholders(self, persona_content: str, agent_name: str = None) -> str:
        """
        Resolve placeholders in persona content with actual agent values.
        
        Args:
            persona_content: Raw persona content with placeholders
            agent_name: Name of the agent (overrides self.current_agent)
            
        Returns:
            Processed persona content with resolved placeholders
        """
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
        }
        
        # Apply placeholder replacements only with valid strings
        for placeholder, replacement in placeholders.items():
            if replacement and isinstance(replacement, str):
                processed_content = processed_content.replace(placeholder, replacement)
        
        logger.debug(f"Resolved placeholders in persona for agent: {agent_id} (friendly: {friendly_name})")
        return processed_content
    
    def _extract_persona_title(self, persona_content: str) -> str:
        """
        Extract friendly name from persona title.
        
        Args:
            persona_content: Raw persona content
            
        Returns:
            Extracted friendly name or None
        """
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
    
    def _save_agent_state(self):
        """
        Save current agent state to state.json file.
        """
        try:
            if hasattr(self, 'state_file_path') and hasattr(self, 'agent_state'):
                # Update conversation history from LLM client
                if hasattr(self.llm_client, 'conversation_history'):
                    self.agent_state["conversation_history"] = self.llm_client.conversation_history
                
                # Update timestamp
                self.agent_state["last_updated"] = datetime.now().isoformat()
                
                # Write to file
                with open(self.state_file_path, 'w') as f:
                    json.dump(self.agent_state, f, indent=2)
                
                logger.debug(f"Agent state saved to {self.state_file_path}")
                
        except Exception as e:
            logger.error(f"Error saving agent state: {e}")
    
    def chat(self, message: str) -> str:
        """
        Send a message to the current embodied agent using chat provider.
        
        Args:
            message: Message to send to the agent
            
        Returns:
            Agent's response
        """
        if not self.embodied:
            return "No agent currently embodied. Use embody_agent_v2() first."
        
        try:
            # Ensure we're using the chat provider
            current_provider = self.get_chat_provider()
            if not hasattr(self.llm_client, 'ai_provider') or self.llm_client.ai_provider != current_provider:
                logger.info(f"Switching to chat provider: {current_provider}")
                self.llm_client = create_llm_client(current_provider, self.working_directory)
                # Restore conversation history
                if hasattr(self, '_conversation_history'):
                    self.llm_client.conversation_history = self._conversation_history
            
            response = self.llm_client._invoke_subprocess(message)
            
            # Cache conversation history for provider switching
            self._conversation_history = self.llm_client.conversation_history
            
            # Save state after each interaction
            if hasattr(self, 'save_agent_state_v2'):
                self.save_agent_state_v2()
            
            return response or "No response from agent."
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"Error: {e}"
    
    def generate_artifact(self, prompt: str) -> str:
        """
        Generate an artifact using the generation provider (typically Claude).
        
        Args:
            prompt: Prompt for artifact generation, including conversation context
            
        Returns:
            Generated artifact content
        """
        if not self.embodied:
            return "No agent currently embodied. Use embody_agent_v2() first."
        
        try:
            # Use generation provider for artifact creation
            generation_provider = self.get_generation_provider()
            logger.info(f"Using generation provider for artifact: {generation_provider}")
            
            # Create dedicated LLM client for generation
            generation_client = create_llm_client(generation_provider, self.working_directory)
            
            # Transfer conversation history for context
            if hasattr(self, '_conversation_history'):
                generation_client.conversation_history = self._conversation_history.copy()
            
            # Generate artifact
            response = generation_client._invoke_subprocess(prompt)
            
            return response or "No artifact generated."
        except Exception as e:
            logger.error(f"Artifact generation failed: {e}")
            return f"Error generating artifact: {e}"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Genesis Agent CLI v2.0 - Project Agent Executor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/genesis_agent.py --environment develop --project nex-web-backend --agent KotlinEntityCreator_Agent --repl
    python scripts/genesis_agent.py --environment develop --project nex-web-backend --agent ProblemRefiner_Agent

Note: For meta-agents that manage the framework itself, use admin.py instead:
    python scripts/admin.py --agent AgentCreator_Agent --repl
        """
    )
    
    # v2.0 Arguments
    parser.add_argument('--environment', type=str, 
                        help='Environment name (develop, main, etc.) - Required for v2.0')
    parser.add_argument('--project', type=str,
                        help='Project name - Required for v2.0')
    parser.add_argument('--agent', type=str,
                        help='Agent ID to embody - Required for v2.0')
    
    # Common Arguments
    parser.add_argument('--ai-provider', type=str, default=None, choices=['claude', 'gemini'], 
                        help='AI provider override (uses dual provider system by default)')
    parser.add_argument('--repl', action='store_true', 
                        help='Start interactive REPL')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (args.environment and args.project):
        print("❌ Erro: Especifique argumentos obrigatórios para agentes de projeto")
        print("Uso: --environment develop --project nex-web-backend --agent KotlinEntityCreator_Agent")
        print("\n💡 Para meta-agentes que gerenciam o framework, use admin.py:")
        print("   python scripts/admin.py --agent AgentCreator_Agent")
        exit(1)
    
    # Initialize Genesis Agent
    try:
        print(f"🚀 Iniciando Genesis Agent v2.0 (Project Agent Executor)")
        print(f"   Environment: {args.environment}")
        print(f"   Project: {args.project}")
        
        agent = GenesisAgent(
            environment=args.environment,
            project=args.project,
            agent_id=args.agent,
            ai_provider=args.ai_provider
        )
        
        # Embody agent if specified
        if args.agent:
            print(f"🤖 Embodying agent: {args.agent}")
            if agent.embody_agent_v2(args.agent):
                print(f"✅ Successfully embodied {args.agent} in {args.environment}/{args.project}")
                print(f"📂 Working directory: {agent.working_directory}")
                if hasattr(agent, 'output_scope') and agent.output_scope:
                    print(f"🔒 Output scope: {agent.output_scope}")
                else:
                    print(f"🔓 No output restrictions (meta-agent)")
            else:
                print(f"❌ Failed to embody {args.agent}")
                exit(1)
    
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        exit(1)
    
    # Start REPL if requested
    if args.repl:
        start_repl_session(agent, "genesis")
    
    # If not REPL mode, just run a single interaction
    elif not args.repl and agent.embodied:
        print("\n💡 Tip: Use --repl for interactive mode")
        print("🤖 Agent ready for programmatic use")
    
    print("\n👋 Genesis Agent session completed")

