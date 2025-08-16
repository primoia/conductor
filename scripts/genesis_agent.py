#!/usr/bin/env python3
"""
Genesis Agent - Interactive Agent Embodiment CLI

This script implements the Genesis Agent from the Maestro Framework specification.
Milestone 1: Basic structure and agent loading functionality.

The Genesis Agent serves as the main interface for interactive mode in the Maestro framework,
allowing developers to "embody" specialist agents for dialogue, analysis, and debugging.
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

# Configuration Constants
AGENTS_BASE_PATH = os.path.join("projects", "develop", "agents")
MAX_TOOL_CALLS_PER_TURN = 5  # Limit to prevent infinite loops
MAX_CONVERSATION_HISTORY = 50  # Sliding window for conversation history

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
    
    def __init__(self, working_directory: str = None):
        """
        Initialize the Toolbelt.
        
        Args:
            working_directory: Base directory for tool operations (defaults to current dir)
        """
        self.working_directory = working_directory or os.getcwd()
        
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
    
    @retry_on_failure(max_retries=3, recoverable_errors=RECOVERABLE_IO_ERRORS)
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
python scripts/genesis_agent.py --embody [AGENT_ID] --project-root {project_root} --repl
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
2. Inicie uma conversa: `python scripts/genesis_agent.py --embody [AGENT] --project-root {template_vars['project_root']} --repl`

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
        
        Args:
            new_prompt: The new user prompt
            
        Returns:
            Full prompt including conversation context
        """
        if not self.conversation_history:
            return new_prompt
        
        # Build context from conversation history
        context_parts = ["Previous conversation context:"]
        
        # Include last N messages for context (limit to prevent token overflow)
        max_context_messages = 10
        recent_history = self.conversation_history[-max_context_messages:]
        
        for entry in recent_history:
            user_msg = entry.get('prompt', '').strip()
            assistant_msg = entry.get('response', '').strip()
            
            if user_msg:
                context_parts.append(f"User: {user_msg}")
            if assistant_msg:
                context_parts.append(f"Assistant: {assistant_msg}")
        
        context_parts.append("\nCurrent message:")
        context_parts.append(f"User: {new_prompt}")
        
        return "\n".join(context_parts)
    
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
            
            # Build command with proper arguments
            cmd = [self.claude_command, "--print", full_prompt]
            
            # Execute Claude CLI with timeout
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
            logger.error("Claude CLI timed out")
            return None
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return None


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
        self.gemini_command = "gemini-cli"  # Assuming a Gemini CLI tool exists
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
            # Build command for Gemini
            cmd = [self.gemini_command, "--prompt", prompt]
            
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


class GenesisAgent:
    """
    Main Genesis Agent class implementing the "embodiment" functionality.
    
    This class is responsible for loading and incorporating specialist agents
    as defined in the Maestro framework specification.
    """
    
    def __init__(self, project_root: str = None, working_directory: str = None, ai_provider: str = 'claude'):
        """
        Initialize the Genesis Agent.
        
        Args:
            project_root: Root directory for project operations
            working_directory: Working directory for subprocess calls
            ai_provider: AI provider to use ('claude', 'gemini')
        """
        self.project_root = project_root or os.getcwd()
        self.working_directory = working_directory or self.project_root
        self.ai_provider = ai_provider
        
        # Initialize LLM client
        self.llm_client = create_llm_client(ai_provider, self.working_directory)
        
        # Initialize toolbelt
        self.toolbelt = Toolbelt(self.working_directory)
        
        # Agent state
        self.current_agent = None
        self.embodied = False
        
        logger.info(f"GenesisAgent initialized with provider: {ai_provider}")
    
    def embody_agent(self, agent_name: str) -> bool:
        """
        Embody a specific agent by loading its configuration and state.
        
        Args:
            agent_name: Name of the agent to embody
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Construct agent directory path
            agent_dir = os.path.join(AGENTS_BASE_PATH, agent_name)
            if not os.path.exists(agent_dir):
                logger.error(f"Agent directory not found: {agent_dir}")
                return False
            
            # Load agent configuration
            agent_yaml_path = os.path.join(agent_dir, "agent.yaml")
            if not os.path.exists(agent_yaml_path):
                logger.error(f"Agent configuration not found: {agent_yaml_path}")
                return False
                
            import yaml
            with open(agent_yaml_path, 'r') as f:
                self.agent_config = yaml.safe_load(f)
            
            # Load agent state and conversation history
            state_file_path = os.path.join(agent_dir, self.agent_config.get("state_file_path", "state.json"))
            self._load_agent_state(state_file_path)
            
            # Load agent persona
            persona_path = os.path.join(agent_dir, self.agent_config.get("persona_prompt_path", "persona.md"))
            if not self._load_agent_persona(persona_path, agent_name):
                return False
            
            # Store paths for future state saving
            self.agent_dir = agent_dir
            self.state_file_path = state_file_path
            
            # Set current agent and mark as embodied
            self.current_agent = agent_name
            self.embodied = True
            
            logger.info(f"Successfully embodied agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to embody agent {agent_name}: {e}")
            return False
    
    def _load_agent_state(self, state_file_path: str):
        """
        Load agent state from state.json file.
        
        Args:
            state_file_path: Path to the state.json file
        """
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, 'r') as f:
                    state_data = json.load(f)
                
                # Load conversation history into LLM client
                conversation_history = state_data.get("conversation_history", [])
                if hasattr(self.llm_client, 'conversation_history'):
                    self.llm_client.conversation_history = conversation_history
                    logger.debug(f"Loaded {len(conversation_history)} conversation entries from state")
                
                # Store full state data for future reference
                self.agent_state = state_data
                
            else:
                logger.info(f"State file not found: {state_file_path}, initializing with empty state")
                self.agent_state = {
                    "version": "1.0",
                    "agent_id": self.current_agent,
                    "conversation_history": [],
                    "last_updated": datetime.now().isoformat()
                }
                if hasattr(self.llm_client, 'conversation_history'):
                    self.llm_client.conversation_history = []
                    
        except Exception as e:
            logger.error(f"Error loading agent state: {e}")
            # Initialize with empty state on error
            self.agent_state = {
                "version": "1.0", 
                "agent_id": getattr(self, 'current_agent', 'unknown'),
                "conversation_history": [],
                "last_updated": datetime.now().isoformat()
            }
            if hasattr(self.llm_client, 'conversation_history'):
                self.llm_client.conversation_history = []
    
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
        Send a message to the current embodied agent.
        
        Args:
            message: Message to send to the agent
            
        Returns:
            Agent's response
        """
        if not self.embodied:
            return "No agent currently embodied. Use embody_agent() first."
        
        try:
            response = self.llm_client._invoke_subprocess(message)
            
            # Save state after each interaction to persist conversation history
            self._save_agent_state()
            
            return response or "No response from agent."
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return f"Error: {e}"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Genesis Agent CLI')
    parser.add_argument('--embody', type=str, help='Agent name to embody')
    parser.add_argument('--project-root', type=str, help='Project root directory')
    parser.add_argument('--ai-provider', type=str, default='claude', choices=['claude', 'gemini'], 
                        help='AI provider to use')
    parser.add_argument('--repl', action='store_true', help='Start interactive REPL')
    
    args = parser.parse_args()
    
    # Initialize Genesis Agent
    agent = GenesisAgent(
        project_root=args.project_root,
        ai_provider=args.ai_provider
    )
    
    # Embody agent if specified
    if args.embody:
        if agent.embody_agent(args.embody):
            print(f"Successfully embodied {args.embody}")
        else:
            print(f"Failed to embody {args.embody}")
            exit(1)
    
    # Start REPL if requested
    if args.repl:
        print("Genesis Agent REPL started. Type 'exit' to quit.")
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    break
                response = agent.chat(user_input)
                print(response)
            except KeyboardInterrupt:
                print("\nExiting...")
                break

