import os
import json
import logging
import subprocess
import time
from typing import Optional, List
from pathlib import Path
from src.ports.llm_client import LLMClient
from src.core.exceptions import LLMClientError

logger = logging.getLogger(__name__)


class BaseCLIClient(LLMClient):
    """
    Base implementation for CLI-based LLM clients.
    """
    
    def __init__(self, working_directory: str = None, timeout: int = 120, is_admin_agent: bool = False):
        self.working_directory = working_directory or os.getcwd()
        self.timeout = timeout
        self.conversation_history = []
        self.genesis_agent = None  # Reference to parent agent for access to tools and config
        self.is_admin_agent = is_admin_agent  # Flag to identify admin agents
        logger.debug(f"BaseCLIClient initialized with working directory: {self.working_directory}, admin: {is_admin_agent}")




class ClaudeCLIClient(BaseCLIClient):
    """
    Claude CLI Client implementation.
    """
    
    def __init__(self, working_directory: str = None, timeout: int = 120, is_admin_agent: bool = False):
        super().__init__(working_directory, timeout, is_admin_agent)
        self.claude_command = "claude"
        logger.debug(f"ClaudeCLIClient initialized (admin: {is_admin_agent})")

    def invoke(self, prompt: str) -> str:
        """Invoke Claude CLI with the given prompt."""
        try:
            cmd = [self.claude_command, "--print", "--dangerously-skip-permissions"]
            
            # Add available tools if genesis_agent is available
            if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'get_available_tools'):
                available_tools = self.genesis_agent.get_available_tools()
                if available_tools:
                    cmd.extend(["--allowedTools", " ".join(available_tools)])
            
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                # Add to conversation history AFTER receiving response from Claude
                # Note: We store the original user input, not the full prompt
                self.conversation_history.append({
                    'prompt': prompt, 
                    'response': response, 
                    'timestamp': time.time()
                })
                return response
            else:
                logger.error(f"Claude CLI failed: {result.stderr}")
                raise LLMClientError(f"Claude CLI failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI timed out after {self.timeout} seconds")
            raise LLMClientError(f"Claude CLI timed out after {self.timeout} seconds. Complex operations may need more time.")
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            raise LLMClientError(f"Claude CLI error: {e}")


class GeminiCLIClient(BaseCLIClient):
    """
    Gemini CLI Client implementation.
    """
    
    def __init__(self, working_directory: str = None, timeout: int = 120, is_admin_agent: bool = False):
        super().__init__(working_directory, timeout, is_admin_agent)
        self.gemini_command = "gemini"
        logger.debug(f"GeminiCLIClient initialized (admin: {is_admin_agent})")

    def invoke(self, prompt: str) -> str:
        """Invoke Gemini CLI with the given prompt."""
        try:
            # Gemini CLI takes the prompt via the -p argument
            cmd = [self.gemini_command, "-p", prompt]
            
            # For Gemini CLI, always use yolo mode to avoid parameter errors
            # The real tool control should be implemented at a higher level in the framework
            cmd.extend(["--approval-mode", "yolo"])
            
            if self.is_admin_agent:
                logger.debug("Admin agent: using yolo mode (unrestricted access)")
            else:
                logger.warning("Project agent: using yolo mode - tool restrictions not implemented in Gemini CLI yet")
                # TODO: Implement tool restrictions via other means (settings.json, prompt instructions, etc.)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_directory,
                check=True  # Raise CalledProcessError on non-zero exit codes
            )
            
            response = result.stdout.strip()
            self.conversation_history.append({
                'prompt': prompt, 
                'response': response, 
                'timestamp': time.time()
            })
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Gemini CLI timed out after {self.timeout} seconds")
            raise LLMClientError(f"Gemini CLI timed out after {self.timeout} seconds.")
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip() if e.stderr else str(e)
            logger.error(f"Gemini CLI failed with exit code {e.returncode}: {error_message}")
            raise LLMClientError(f"Gemini CLI failed: {error_message}")
        except FileNotFoundError:
            logger.error(f"Gemini command not found: '{self.gemini_command}'. Make sure it's installed and in the PATH.")
            raise LLMClientError(f"Gemini command not found: '{self.gemini_command}'.")
        except Exception as e:
            logger.error(f"An unexpected error occurred with Gemini CLI: {e}")
            raise LLMClientError(f"An unexpected error occurred with Gemini CLI: {e}")
    
    def _map_tools_to_gemini(self, allowed_tools: List[str]) -> List[str]:
        """
        Map internal tool names to Gemini CLI tool names.
        
        Args:
            allowed_tools: List of internal tool names from agent.yaml
            
        Returns:
            List of Gemini CLI compatible tool names
        """
        # Map internal tool names to Gemini CLI tools  
        tool_mapping = {
            'Read': 'read_file',
            'Write': 'write_file', 
            'Bash': 'run_shell_command',
            'Grep': 'grep',
            'Glob': 'find_files',
            'run_shell_command': 'run_shell_command',
            'write_file': 'write_file',
            'read_file': 'read_file',
            # Add domain-specific tools as-is
            'collect_user_profile': 'collect_user_profile',
            'collect_project_context': 'collect_project_context',
            'suggest_team_template': 'suggest_team_template',
            'apply_team_template': 'apply_team_template',
            'create_example_project': 'create_example_project',
            'list_team_templates': 'list_team_templates'
        }
        
        # Convert allowed tools to Gemini CLI tool names
        gemini_tools = []
        for tool in allowed_tools:
            if tool in tool_mapping:
                gemini_tools.append(tool_mapping[tool])
            else:
                # For unknown tools, pass through as-is (might be valid Gemini tools)
                gemini_tools.append(tool.lower())
        
        # Remove duplicates while preserving order
        unique_tools = []
        for tool in gemini_tools:
            if tool not in unique_tools:
                unique_tools.append(tool)
        
        return unique_tools


def create_llm_client(ai_provider: str, working_directory: str = None, timeout: int = 120, is_admin_agent: bool = False) -> LLMClient:
    """
    Factory function to create LLM clients based on provider.
    """
    if ai_provider == 'claude':
        logger.info(f"Creating Claude CLI client with timeout: {timeout}s, admin: {is_admin_agent}")
        return ClaudeCLIClient(working_directory, timeout, is_admin_agent)
    elif ai_provider == 'gemini':
        logger.info(f"Creating Gemini CLI client with timeout: {timeout}s, admin: {is_admin_agent}") 
        return GeminiCLIClient(working_directory, timeout, is_admin_agent)
    else:
        raise LLMClientError(f"Unsupported AI provider: {ai_provider}")