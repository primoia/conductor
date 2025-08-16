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

# Configuration Constants
AGENTS_BASE_PATH = os.path.join("projects", "develop", "agents")
MAX_TOOL_CALLS_PER_TURN = 5  # Limit to prevent infinite loops
MAX_CONVERSATION_HISTORY = 50  # Sliding window for conversation history

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
            'apply_team_template': self.apply_team_template
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
        
        logger.debug(f"LLMClient base initialized with working directory: {self.working_directory}")
    
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
    
    Handles communication with Claude via the claude CLI command,
    following the same pattern as run_conductor.py for consistency.
    """
    
    def __init__(self, working_directory: str = None):
        """
        Initialize the Claude CLI Client.
        
        Args:
            working_directory: Working directory for subprocess calls
        """
        super().__init__(working_directory)
        self.provider = 'claude'
        logger.debug(f"ClaudeCLIClient initialized")
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history with sliding window management.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': logging.Formatter().formatTime(logging.LogRecord(
                '', 0, '', 0, '', (), None))
        })
        
        # MEMORY MANAGEMENT: Implement sliding window
        if len(self.conversation_history) > MAX_CONVERSATION_HISTORY:
            # Keep the first few messages for context and the most recent ones
            context_messages = 2  # Keep first 2 messages for context
            recent_messages = MAX_CONVERSATION_HISTORY - context_messages
            
            # Preserve context + recent messages
            preserved_history = (
                self.conversation_history[:context_messages] + 
                self.conversation_history[-recent_messages:]
            )
            
            # Add a marker showing truncation
            if len(self.conversation_history) > MAX_CONVERSATION_HISTORY + 1:  # Only add marker once
                truncation_marker = {
                    'role': 'system',
                    'content': f'[Conversation truncated - {len(self.conversation_history) - MAX_CONVERSATION_HISTORY} messages removed]',
                    'timestamp': logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))
                }
                preserved_history.insert(context_messages, truncation_marker)
            
            self.conversation_history = preserved_history
            logger.info(f"Conversation history truncated to {len(self.conversation_history)} messages")
        
        logger.debug(f"Added {role} message to conversation history ({len(content)} chars)")
    
    def build_system_prompt(self, agent_data: Dict[str, Any], agent_path: str) -> str:
        """
        Build the system prompt for the embodied agent.
        
        Args:
            agent_data: Agent configuration data
            agent_path: Path to agent directory
            
        Returns:
            System prompt string
        """
        try:
            # Load persona if available
            persona_path = os.path.join(agent_path, agent_data.get('persona_prompt_path', 'persona.md'))
            persona_content = ""
            if os.path.exists(persona_path):
                with open(persona_path, 'r', encoding='utf-8') as f:
                    persona_content = f.read()
            
            # Build system prompt
            system_prompt = f"""You are an AI assistant embodying the '{agent_data['id']}' specialist agent.

**Agent Information:**
- ID: {agent_data['id']}
- Version: {agent_data['version']}
- Description: {agent_data['description']}

**Agent Persona:**
{persona_content if persona_content else 'No persona defined.'}

**Available Tools:**
{', '.join(agent_data.get('available_tools', []))}

**Instructions:**
1. You are having a conversation with a developer who has embodied this agent
2. Stay in character as this specialist agent
3. When you need to use tools, format your request as: [TOOL_CALL: tool_name(param1="value1", param2="value2")]
4. Be helpful, knowledgeable, and focused on your specialty area
5. Ask clarifying questions when needed

The developer can interact with you naturally. Respond as the embodied agent would."""
            
            return system_prompt
            
        except Exception as e:
            logger.error(f"Failed to build system prompt: {e}")
            return f"You are the {agent_data['id']} agent. Respond helpfully to the user's queries."
    
    def send_message(self, user_message: str, agent_data: Dict[str, Any], 
                    agent_path: str) -> str:
        """
        Send a message to the LLM and get a response.
        
        Args:
            user_message: User's message
            agent_data: Agent configuration data
            agent_path: Path to agent directory
            
        Returns:
            LLM response
        """
        try:
            # Add user message to history
            self.add_message('user', user_message)
            
            # Build the complete prompt
            system_prompt = self.build_system_prompt(agent_data, agent_path)
            
            # Build conversation context
            conversation_context = ""
            if len(self.conversation_history) > 1:
                conversation_context = "\n\nConversation History:\n"
                for msg in self.conversation_history[:-1]:  # Exclude the current message
                    conversation_context += f"{msg['role'].upper()}: {msg['content']}\n"
            
            # Combine everything into the final prompt
            full_prompt = f"""{system_prompt}
{conversation_context}

Current user message: {user_message}

Please respond as the {agent_data['id']} agent:"""
            
            # Call Claude via subprocess
            response = self._invoke_subprocess(full_prompt)
            
            if response:
                # Add assistant response to history
                self.add_message('assistant', response)
                return response
            else:
                error_msg = "Sorry, I couldn't process your request. Please try again."
                self.add_message('assistant', error_msg)
                return error_msg
                
        except Exception as e:
            logger.error(f"Failed to send message to LLM: {e}")
            error_msg = f"Error communicating with AI: {e}"
            self.add_message('assistant', error_msg)
            return error_msg
    
    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        """
        Invoke Claude via subprocess (following run_conductor.py pattern).
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Claude's response or None if failed
        """
        logger.debug("Invoking Claude via subprocess")
        
        try:
            command = ["claude", "--print", "--dangerously-skip-permissions", prompt]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
                cwd=self.working_directory
            )
            
            if process.returncode != 0:
                logger.error(f"Claude execution failed with return code {process.returncode}")
                logger.error(f"Error: {process.stderr}")
                return None
            
            response = process.stdout.strip()
            logger.info("Claude call completed successfully")
            return response
            
        except FileNotFoundError:
            logger.error("Claude command not found. Make sure 'claude' is installed and in your PATH.")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Claude call timed out after 120 seconds")
            return None
        except Exception as e:
            logger.error(f"Claude call failed with unexpected exception: {e}")
            return None
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_history_summary(self) -> str:
        """Get a summary of the conversation history."""
        if not self.conversation_history:
            return "No conversation history"
        
        return f"Conversation: {len(self.conversation_history)} messages"


class GeminiCLIClient(LLMClient):
    """
    Gemini CLI Client implementation.
    
    Handles communication with Gemini via the npx @google/gemini-cli command,
    following the same pattern as run_conductor.py for consistency.
    """
    
    def __init__(self, working_directory: str = None):
        """
        Initialize the Gemini CLI Client.
        
        Args:
            working_directory: Working directory for subprocess calls
        """
        super().__init__(working_directory)
        self.provider = 'gemini'
        logger.debug(f"GeminiCLIClient initialized")
    
    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        """
        Invoke Gemini via subprocess (following run_conductor.py pattern).
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Gemini's response or None if failed
        """
        logger.debug("Invoking Gemini via subprocess")
        
        try:
            command = ["npx", "--yes", "@google/gemini-cli", "-p", prompt]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
                cwd=self.working_directory
            )
            
            if process.returncode != 0:
                logger.error(f"Gemini execution failed with return code {process.returncode}")
                logger.error(f"Error: {process.stderr}")
                return None
            
            response = process.stdout.strip()
            logger.info("Gemini call completed successfully")
            return response
            
        except FileNotFoundError:
            logger.error("Gemini CLI not found. Make sure 'npx' is available and @google/gemini-cli can be installed.")
            return None
        except subprocess.TimeoutExpired:
            logger.error("Gemini call timed out after 120 seconds")
            return None
        except Exception as e:
            logger.error(f"Gemini call failed with unexpected exception: {e}")
            return None


def create_llm_client(ai_provider: str, working_directory: str = None) -> LLMClient:
    """
    Factory function to create the appropriate LLM client based on provider.
    
    Args:
        ai_provider: The AI provider ('claude' or 'gemini')
        working_directory: Working directory for subprocess calls
        
    Returns:
        Appropriate LLMClient instance
        
    Raises:
        ValueError: If ai_provider is not supported
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
    
    def __init__(self, agent_id: str, project_root: str, state_path: Optional[str] = None, verbose: bool = False):
        """
        Initialize the Genesis Agent.
        
        Args:
            agent_id: The ID of the specialist agent to embody
            project_root: The absolute path to the target project
            state_path: Optional path to load previous session state
            verbose: Enable detailed logging
        """
        self.agent_id = agent_id
        self.project_root = os.path.abspath(project_root)  # Store as absolute path
        self.state_path = state_path
        self.verbose = verbose
        self.agent_data = None
        self.agent_path = None
        self.toolbelt = None
        self.llm_client = None
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            
        logger.info(f"Initializing Genesis Agent for embodiment of: {agent_id}")
    
    def locate_agent_directory(self) -> bool:
        """
        Locate the agent directory following the Maestro framework convention.
        
        Expected path: projects/develop/agents/<agent_id>/
        
        Returns:
            bool: True if agent directory was found, False otherwise
        """
        logger.debug(f"Locating agent directory for: {self.agent_id}")
        
        # Get the conductor root directory (parent of scripts)
        conductor_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agent_path = os.path.join(conductor_root, AGENTS_BASE_PATH, self.agent_id)
        
        if not os.path.exists(agent_path):
            logger.error(f"Agent directory not found: {agent_path}")
            return False
        
        if not os.path.isdir(agent_path):
            logger.error(f"Agent path exists but is not a directory: {agent_path}")
            return False
            
        self.agent_path = agent_path
        logger.info(f"Agent directory located: {agent_path}")
        return True
    
    def load_agent_yaml(self) -> bool:
        """
        Load and parse the agent.yaml file.
        
        Returns:
            bool: True if agent.yaml was successfully loaded and parsed, False otherwise
        """
        if not self.agent_path:
            logger.error("Agent path not set. Call locate_agent_directory() first.")
            return False
            
        agent_yaml_path = os.path.join(self.agent_path, "agent.yaml")
        
        if not os.path.exists(agent_yaml_path):
            logger.error(f"agent.yaml not found: {agent_yaml_path}")
            return False
            
        try:
            logger.debug(f"Loading agent.yaml from: {agent_yaml_path}")
            with open(agent_yaml_path, 'r', encoding='utf-8') as f:
                self.agent_data = yaml.safe_load(f)
            
            # Validate required fields according to Maestro specification
            required_fields = ['id', 'version', 'description']
            for field in required_fields:
                if field not in self.agent_data:
                    logger.error(f"Missing required field in agent.yaml: {field}")
                    return False
            
            # Validate that the agent ID matches
            if self.agent_data['id'] != self.agent_id:
                logger.error(f"Agent ID mismatch. Expected: {self.agent_id}, Found: {self.agent_data['id']}")
                return False
                
            logger.info(f"Successfully loaded agent.yaml for: {self.agent_id}")
            logger.debug(f"Agent version: {self.agent_data['version']}")
            logger.debug(f"Agent description: {self.agent_data['description']}")
            
            return True
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in agent.yaml: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load agent.yaml: {e}")
            return False
    
    def load_agent(self) -> bool:
        """
        Complete agent loading process.
        
        This method orchestrates the full agent loading sequence:
        1. Locate agent directory
        2. Load and parse agent.yaml
        
        Returns:
            bool: True if agent was successfully loaded, False otherwise
        """
        logger.info(f"Starting agent loading process for: {self.agent_id}")
        
        if not self.locate_agent_directory():
            return False
            
        if not self.load_agent_yaml():
            return False
            
        # Initialize toolbelt and LLM client after successful agent loading
        conductor_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.toolbelt = Toolbelt(working_directory=self.project_root)  # Use project root as working directory
        
        # Dynamic AI provider selection based on agent configuration
        ai_provider = self.agent_data.get('ai_provider', 'claude')  # Default to claude if not specified
        try:
            self.llm_client = create_llm_client(ai_provider, working_directory=self.project_root)
        except ValueError as e:
            logger.error(f"Failed to create LLM client: {e}")
            return False
        
        # Load previous state if specified
        if self.state_path and os.path.exists(self.state_path):
            self._load_state_file()
        
        logger.info(f"Agent '{self.agent_id}' loaded successfully")
        logger.debug(f"Toolbelt initialized with tools: {self.toolbelt.get_available_tools()}")
        logger.debug(f"LLM Client initialized with provider: {ai_provider}")
        return True
    
    def get_agent_data(self) -> Dict[str, Any]:
        """
        Get the loaded agent data.
        
        Returns:
            Dict containing the agent configuration and metadata
        """
        if not self.agent_data:
            raise RuntimeError("Agent data not loaded. Call load_agent() first.")
            
        # Return a copy to prevent external modification
        return self.agent_data.copy()
    
    def print_agent_summary(self) -> None:
        """
        Print a formatted summary of the loaded agent data.
        """
        if not self.agent_data:
            logger.error("No agent data loaded")
            return
            
        print("\n" + "="*60)
        print("GENESIS AGENT - MILESTONE 1 OUTPUT")
        print("="*60)
        print(f"Agent ID: {self.agent_data['id']}")
        print(f"Version: {self.agent_data['version']}")
        print(f"Description: {self.agent_data['description']}")
        print(f"Agent Path: {self.agent_path}")
        print("\nComplete Agent Data Dictionary:")
        print("-"*40)
        print(json.dumps(self.agent_data, indent=2, ensure_ascii=False))
        print("="*60)
    
    def run_repl(self) -> None:
        """
        Run the interactive REPL (Read-Eval-Print-Loop).
        
        This method implements the core interactive functionality of the Genesis Agent,
        allowing the developer to converse with the embodied specialist agent.
        """
        if not self.agent_data:
            logger.error("No agent data loaded. Cannot start REPL.")
            return
            
        logger.info(f"Starting REPL for embodied agent: {self.agent_id}")
        print(f"\n🎭 Genesis Agent - Embodying {self.agent_id}")
        print(f"📋 Description: {self.agent_data['description']}")
        print("\n🔧 Available commands:")
        print("  /help    - Show available commands")
        print("  /exit    - Exit the session")
        print("\n💬 Start your conversation below:")
        print("-" * 60)
        
        while True:
            try:
                # Dynamic prompt showing the embodied agent
                prompt = f"[{self.agent_id}] > "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                    
                # Handle internal commands
                if user_input.startswith('/'):
                    if not self._handle_internal_command(user_input):
                        break  # Exit command was issued
                    continue
                
                # Send message to LLM and process response (Passo 2.3 + 2.4)
                print("🤖 Thinking...")
                ai_response = self.llm_client.send_message(user_input, self.agent_data, self.agent_path)
                
                # Check for tool calls in the response (Passo 2.4)
                final_response = self._process_ai_response(ai_response, recursion_depth=0)
                print(f"🤖 {final_response}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupt received. Use /exit to quit properly.")
                continue
            except EOFError:
                print("\n\n👋 Session ended.")
                break
                
        logger.info("REPL session ended")
    
    def _handle_internal_command(self, command: str) -> bool:
        """
        Handle internal Genesis Agent commands that start with '/'.
        
        Args:
            command: The command string (including the '/')
            
        Returns:
            bool: True to continue REPL, False to exit
        """
        command = command.lower().strip()
        
        if command == '/exit':
            return self._handle_exit_command()
        elif command == '/help':
            return self._handle_help_command()
        elif command == '/save':
            return self._handle_save_command()
        elif command == '/onboard':
            return self._handle_onboard_command()
        elif command == '/back':
            return self._handle_back_command()
        else:
            print(f"❌ Unknown command: {command}")
            print("💡 Type /help to see available commands")
            return True
    
    def _handle_exit_command(self) -> bool:
        """
        Handle the /exit command with confirmation.
        
        Returns:
            bool: False to exit REPL, True to continue
        """
        try:
            confirmation = input("❓ Are you sure you want to exit? (y/N): ").strip().lower()
            if confirmation in ['y', 'yes']:
                print("👋 Goodbye!")
                return False
            else:
                print("↩️  Continuing session...")
                return True
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            return False
    
    def _handle_help_command(self) -> bool:
        """
        Handle the /help command - show available internal commands.
        
        Returns:
            bool: Always True to continue REPL
        """
        print("\n🔧 Genesis Agent Internal Commands:")
        print("  /help    - Show this help message")
        print("  /save    - Save the current conversation state")
        print("  /onboard - Start the '3 Clicks to Productivity' team setup")
        print("  /back    - Return from onboarding mode to original agent")
        print("  /exit    - Exit the REPL session (with confirmation)")
        print("\n🎭 Embodied Agent Information:")
        print(f"  Agent ID: {self.agent_id}")
        print(f"  Version: {self.agent_data.get('version', 'Unknown')}")
        print(f"  Description: {self.agent_data.get('description', 'No description')}")
        
        # Show available tools if any
        available_tools = self.agent_data.get('available_tools', [])
        if available_tools:
            print(f"\n🛠️  Available Tools: {', '.join(available_tools)}")
        else:
            print("\n🛠️  No tools configured for this agent")
            
        print()
        return True
    
    def _handle_save_command(self) -> bool:
        """
        Handle the /save command - persist current conversation state.
        
        Returns:
            bool: Always True to continue REPL
        """
        try:
            state_data = {
                'agent_id': self.agent_id,
                'conversation_history': self.llm_client.conversation_history,
                'timestamp': logging.Formatter().formatTime(logging.LogRecord(
                    '', 0, '', 0, '', (), None)),
                'agent_path': self.agent_path
            }
            
            # Determine state file path
            if self.state_path:
                state_file_path = self.state_path
            else:
                # Default to agent's state.json
                state_file_path = os.path.join(self.agent_path, 'state.json')
            
            # Save state
            with open(state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Conversation state saved to: {state_file_path}")
            print(f"📊 Saved {len(state_data['conversation_history'])} messages")
            logger.info(f"State saved to: {state_file_path}")
            
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
            logger.error(f"Failed to save state: {e}")
        
        return True
    
    def _handle_onboard_command(self) -> bool:
        """
        Handle the /onboard command - start the 3 Clicks to Productivity experience.
        
        This command switches to the Onboarding_Agent temporarily to guide the user
        through team template selection and application.
        
        Returns:
            bool: Always True to continue REPL
        """
        try:
            print("\n🎼 Bem-vindo ao Conductor Onboarding!")
            print("Vou ajudá-lo a configurar um time de agentes especialistas em apenas 3 cliques!")
            print("=" * 70)
            
            # Check if Onboarding_Agent exists
            onboard_agent_path = os.path.join(os.getcwd(), "projects", "develop", "agents", "Onboarding_Agent")
            if not os.path.exists(onboard_agent_path):
                print("❌ Onboarding_Agent não encontrado!")
                print("💡 Certifique-se de que o Onboarding_Agent foi criado em projects/develop/agents/")
                return True
            
            # Temporarily switch context to Onboarding_Agent
            original_agent = {
                'id': self.agent_id,
                'path': self.agent_path,
                'data': self.agent_data
            }
            
            # Load Onboarding_Agent
            try:
                self.agent_id = "Onboarding_Agent"
                self.agent_path = onboard_agent_path
                self.agent_data = self._load_agent_config(onboard_agent_path)
                
                print(f"🤖 Onboarding_Agent ativado!")
                print("💬 Agora você está conversando com o especialista em onboarding.")
                print("🚀 Digite sua mensagem para começar a experiência '3 Clicks to Productivity'")
                print("💡 Ou digite '/back' para voltar ao agente anterior")
                print()
                
                # Set a flag to indicate we're in onboarding mode
                self._in_onboarding_mode = True
                self._original_agent = original_agent
                
            except Exception as e:
                print(f"❌ Erro ao carregar Onboarding_Agent: {e}")
                return True
                
        except Exception as e:
            print(f"❌ Erro no comando /onboard: {e}")
            logger.error(f"Onboard command failed: {e}")
        
        return True
    
    def _handle_back_command(self) -> bool:
        """
        Handle the /back command - return from onboarding mode to original agent.
        
        Returns:
            bool: Always True to continue REPL
        """
        try:
            if hasattr(self, '_in_onboarding_mode') and self._in_onboarding_mode:
                # Restore original agent
                original = self._original_agent
                self.agent_id = original['id']
                self.agent_path = original['path']
                self.agent_data = original['data']
                
                # Clear onboarding mode flags
                self._in_onboarding_mode = False
                del self._original_agent
                
                print(f"\n🔙 Retornado para {self.agent_id}")
                print("💬 Você está de volta ao agente original.")
                print()
            else:
                print("💡 Comando /back só funciona quando você está no modo onboarding.")
                print("💡 Use /onboard para iniciar a experiência de onboarding.")
                
        except Exception as e:
            print(f"❌ Erro no comando /back: {e}")
            logger.error(f"Back command failed: {e}")
        
        return True
    
    def _load_state_file(self) -> None:
        """
        Load conversation state from a state file.
        """
        try:
            with open(self.state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Validate state data
            if state_data.get('agent_id') != self.agent_id:
                logger.warning(f"State file agent ID mismatch: expected {self.agent_id}, found {state_data.get('agent_id')}")
            
            # Restore conversation history
            conversation_history = state_data.get('conversation_history', [])
            self.llm_client.conversation_history = conversation_history
            
            logger.info(f"Loaded state from: {self.state_path}")
            logger.info(f"Restored {len(conversation_history)} messages")
            
        except Exception as e:
            logger.error(f"Failed to load state file {self.state_path}: {e}")
    
    def _process_ai_response(self, ai_response: str, recursion_depth: int = 0) -> str:
        """
        Process AI response and handle tool calls with recursion protection.
        
        This is the critical Passo 2.4 functionality that:
        1. Analyzes the AI response for [TOOL_CALL: ...] patterns
        2. Executes the tools if found
        3. Sends the tool results back to the AI for interpretation
        4. Returns the final response
        
        Args:
            ai_response: Raw response from the AI
            recursion_depth: Current recursion depth (prevents infinite loops)
            
        Returns:
            Final processed response
        """
        # SECURITY: Prevent infinite loops
        if recursion_depth >= MAX_TOOL_CALLS_PER_TURN:
            logger.warning(f"Maximum tool calls reached ({MAX_TOOL_CALLS_PER_TURN}). Stopping to prevent loops.")
            return f"⚠️  Maximum tool calls reached ({MAX_TOOL_CALLS_PER_TURN}). Stopping execution to prevent infinite loops.\n\nPartial response: {ai_response}"
        # Check for tool call pattern
        tool_call_match = self._extract_tool_call(ai_response)
        
        if not tool_call_match:
            # No tool call found, return the response as-is
            return ai_response
        
        try:
            tool_name, tool_params = tool_call_match
            
            # Validate tool is available for this agent
            available_tools = self.agent_data.get('available_tools', [])
            if tool_name not in available_tools:
                return f"Error: Tool '{tool_name}' is not available for this agent. Available tools: {', '.join(available_tools)}"
            
            # Execute the tool
            print(f"🔧 Executing tool: {tool_name}")
            tool_result = self.toolbelt.execute_tool(tool_name, **tool_params)
            
            # Format tool result for AI
            if tool_result['success']:
                tool_output = f"Tool '{tool_name}' executed successfully. Result: {tool_result['result']}"
            else:
                tool_output = f"Tool '{tool_name}' failed. Error: {tool_result['error']}"
            
            # Send tool result back to AI for interpretation
            print("🤖 Interpreting tool results...")
            interpretation_prompt = f"""Tool execution completed. Here's what happened:

Original AI response: {ai_response}

Tool execution result: {tool_output}

Please provide a final response to the user based on this tool execution result. Do not repeat the tool call format - just give a natural response about what was accomplished or what went wrong."""
            
            final_response = self.llm_client.send_message(interpretation_prompt, self.agent_data, self.agent_path)
            
            # Recursively process in case the AI wants to make another tool call
            return self._process_ai_response(final_response, recursion_depth + 1)
            
        except Exception as e:
            logger.error(f"Error processing tool call: {e}")
            return f"Error executing tool: {e}. Original response: {ai_response}"
    
    def _extract_tool_call(self, response: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Extract tool call from AI response.
        
        Looks for pattern: [TOOL_CALL: tool_name(param1="value1", param2="value2")]
        
        Args:
            response: AI response text
            
        Returns:
            Tuple of (tool_name, parameters_dict) or None if no tool call found
        """
        # Pattern to match [TOOL_CALL: tool_name(params)]
        pattern = r'\[TOOL_CALL:\s*(\w+)\((.*?)\)\]'
        match = re.search(pattern, response, re.IGNORECASE)
        
        if not match:
            return None
        
        tool_name = match.group(1)
        params_str = match.group(2).strip()
        
        try:
            # Parse parameters
            params = {}
            if params_str:
                # Simple parameter parsing - expects param="value" format
                param_pattern = r'(\w+)=[\"\']([^\"\']*?)[\"\']'
                param_matches = re.findall(param_pattern, params_str)
                
                for param_name, param_value in param_matches:
                    params[param_name] = param_value
            
            logger.debug(f"Extracted tool call: {tool_name} with params: {params}")
            return (tool_name, params)
            
        except Exception as e:
            logger.error(f"Failed to parse tool call parameters: {e}")
            return None


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments according to Genesis Agent specification.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Genesis Agent - Interactive Agent Embodiment CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python genesis_agent.py --embody AgentCreator_Agent --project-root /path/to/project
  python genesis_agent.py --embody ProblemRefiner_Agent --project-root /path/to/project --verbose
  python genesis_agent.py --embody KotlinEntityCreator_Agent --project-root /path/to/project --state session.json
  python genesis_agent.py --embody AgentCreator_Agent --project-root /path/to/project --repl
        """
    )
    
    parser.add_argument(
        '--embody', 
        required=True,
        help='The ID of the Specialist Agent to be embodied (required)'
    )
    
    parser.add_argument(
        '--state',
        help='Load a state file from a previous session (optional)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable detailed logging (optional)'
    )
    
    parser.add_argument(
        '--repl',
        action='store_true',
        help='Start interactive REPL mode after loading the agent (optional)'
    )
    
    parser.add_argument(
        '--project-root',
        required=True,
        help='The absolute path to the target project on which the agent will operate (required)'
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for Genesis Agent Milestone 1.
    
    This function implements the basic agent loading and validation functionality
    as specified in the Genesis Execution Plan.
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        logger.info("Genesis Agent Milestone 1 - Starting execution")
        logger.info(f"Target agent: {args.embody}")
        
        if args.state:
            logger.info(f"State file specified: {args.state}")
            
        if args.verbose:
            logger.info("Verbose mode enabled")
        
        # Validate project root
        if not os.path.exists(args.project_root):
            logger.error(f"Project root not found: {args.project_root}")
            sys.exit(1)
        
        if not os.path.isdir(args.project_root):
            logger.error(f"Project root is not a directory: {args.project_root}")
            sys.exit(1)
        
        logger.info(f"Project root: {args.project_root}")
        
        # Initialize and load the agent
        genesis = GenesisAgent(
            agent_id=args.embody,
            project_root=args.project_root,
            state_path=args.state,
            verbose=args.verbose
        )
        
        # Load the agent
        if not genesis.load_agent():
            logger.error("Failed to load agent")
            sys.exit(1)
        
        # Print the agent data (Milestone 1 requirement)
        genesis.print_agent_summary()
        
        # Check if REPL mode was requested (Milestone 2.1)
        if args.repl:
            logger.info("REPL mode requested - starting interactive session")
            genesis.run_repl()
        
        logger.info("Genesis Agent execution completed successfully")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()