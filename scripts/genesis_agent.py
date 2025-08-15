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
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
import json

# Configuration Constants
AGENTS_BASE_PATH = os.path.join("projects", "develop", "agents")

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
            'run_shell_command': self.run_shell_command
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
        # Security: Check for potentially dangerous commands
        dangerous_patterns = [
            'rm -rf', 'sudo', 'su ', 'chmod +x', 'curl', 'wget', 
            '>', '>>', '|', '&', ';', '$(', '`'
        ]
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                raise ValueError(f"Command contains potentially dangerous pattern '{pattern}': {command}")
        
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


class LLMClient:
    """
    LLM Client for communicating with Claude via subprocess.
    
    This class wraps the Claude CLI calls and manages conversation history,
    following the same pattern as run_conductor.py for consistency.
    """
    
    def __init__(self, provider: str = 'claude', working_directory: str = None):
        """
        Initialize the LLM Client.
        
        Args:
            provider: AI provider (currently only 'claude' supported)
            working_directory: Working directory for subprocess calls
        """
        self.provider = provider
        self.working_directory = working_directory or os.getcwd()
        self.conversation_history = []
        
        logger.debug(f"LLMClient initialized with provider: {provider}")
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
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
            response = self._invoke_claude_subprocess(full_prompt)
            
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
    
    def _invoke_claude_subprocess(self, prompt: str) -> Optional[str]:
        """
        Invoke Claude via subprocess (following run_conductor.py pattern).
        
        Args:
            prompt: The prompt to send to Claude
            
        Returns:
            Claude's response or None if failed
        """
        logger.debug("Invoking Claude via subprocess")
        
        try:
            if self.provider == 'claude':
                command = ["claude", "--print", "--dangerously-skip-permissions", prompt]
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return None
            
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


class GenesisAgent:
    """
    Main Genesis Agent class implementing the "embodiment" functionality.
    
    This class is responsible for loading and incorporating specialist agents
    as defined in the Maestro framework specification.
    """
    
    def __init__(self, agent_id: str, state_path: Optional[str] = None, verbose: bool = False):
        """
        Initialize the Genesis Agent.
        
        Args:
            agent_id: The ID of the specialist agent to embody
            state_path: Optional path to load previous session state
            verbose: Enable detailed logging
        """
        self.agent_id = agent_id
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
        self.toolbelt = Toolbelt(working_directory=conductor_root)
        self.llm_client = LLMClient(provider='claude', working_directory=conductor_root)
        
        # Load previous state if specified
        if self.state_path and os.path.exists(self.state_path):
            self._load_state_file()
        
        logger.info(f"Agent '{self.agent_id}' loaded successfully")
        logger.debug(f"Toolbelt initialized with tools: {self.toolbelt.get_available_tools()}")
        logger.debug(f"LLM Client initialized with provider: claude")
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
                final_response = self._process_ai_response(ai_response)
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
    
    def _process_ai_response(self, ai_response: str) -> str:
        """
        Process AI response and handle tool calls.
        
        This is the critical Passo 2.4 functionality that:
        1. Analyzes the AI response for [TOOL_CALL: ...] patterns
        2. Executes the tools if found
        3. Sends the tool results back to the AI for interpretation
        4. Returns the final response
        
        Args:
            ai_response: Raw response from the AI
            
        Returns:
            Final processed response
        """
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
            return self._process_ai_response(final_response)
            
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
  python genesis_agent.py --embody AgentCreator_Agent
  python genesis_agent.py --embody ProblemRefiner_Agent --verbose
  python genesis_agent.py --embody KotlinEntityCreator_Agent --state session.json
  python genesis_agent.py --embody AgentCreator_Agent --repl
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
        
        # Initialize and load the agent
        genesis = GenesisAgent(
            agent_id=args.embody,
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