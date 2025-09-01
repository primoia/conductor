import os
import json
import logging
import subprocess
import time
from typing import Optional, List
from src.ports.llm_client import LLMClient
from src.core.exceptions import LLMClientError

logger = logging.getLogger(__name__)


class BaseCLIClient(LLMClient):
    """
    Base implementation for CLI-based LLM clients.
    """
    
    def __init__(self, working_directory: str = None, timeout: int = 120):
        self.working_directory = working_directory or os.getcwd()
        self.timeout = timeout
        self.conversation_history = []
        self.genesis_agent = None  # Reference to parent agent for access to tools and config
        logger.debug(f"BaseCLIClient initialized with working directory: {self.working_directory}")




class ClaudeCLIClient(BaseCLIClient):
    """
    Claude CLI Client implementation.
    """
    
    def __init__(self, working_directory: str = None, timeout: int = 120):
        super().__init__(working_directory, timeout)
        self.claude_command = "claude"
        logger.debug("ClaudeCLIClient initialized")

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
    
    def __init__(self, working_directory: str = None, timeout: int = 120):
        super().__init__(working_directory, timeout)
        self.gemini_command = "gemini"
        logger.debug("GeminiCLIClient initialized")

    def invoke(self, prompt: str) -> str:
        """Invoke Gemini CLI with the given prompt."""
        try:
            # Gemini CLI takes the prompt via the -p argument
            cmd = [self.gemini_command, "-p", prompt]
            
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


def create_llm_client(ai_provider: str, working_directory: str = None, timeout: int = 120) -> LLMClient:
    """
    Factory function to create LLM clients based on provider.
    """
    if ai_provider == 'claude':
        logger.info(f"Creating Claude CLI client with timeout: {timeout}s")
        return ClaudeCLIClient(working_directory, timeout)
    elif ai_provider == 'gemini':
        logger.info(f"Creating Gemini CLI client with timeout: {timeout}s") 
        return GeminiCLIClient(working_directory, timeout)
    else:
        raise LLMClientError(f"Unsupported AI provider: {ai_provider}")