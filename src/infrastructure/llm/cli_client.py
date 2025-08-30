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
        self.agent_persona = None
        self.genesis_agent = None  # Reference to parent agent for access to tools and config
        logger.debug(f"BaseCLIClient initialized with working directory: {self.working_directory}")

    def set_persona(self, persona: str) -> None:
        """Set the agent persona."""
        self.agent_persona = persona
        logger.debug("Agent persona set in LLM client")

    def _build_full_prompt_with_persona(self, new_prompt: str) -> str:
        """Build the full prompt including persona, config, and context."""
        prompt_parts = []
        
        # 1. PERSONA (contexto)
        if self.agent_persona:
            prompt_parts.append("### PERSONA:")
            prompt_parts.append(self.agent_persona)
            prompt_parts.append("\n")
        
        # 2. AGENT_CONFIG (configuração do agente)
        if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'agent_config'):
            prompt_parts.append("### AGENT_CONFIG:")
            prompt_parts.append(json.dumps(self.genesis_agent.agent_config, indent=2, ensure_ascii=False))
            prompt_parts.append("\n")
        
        # 3. CONTEXT (histórico de conversas para contexto)
        if self.conversation_history:
            prompt_parts.append("### CONTEXT:")
            for msg in self.conversation_history:
                prompt_parts.append(f"User: {msg.get('prompt', 'N/A')}")
                prompt_parts.append(f"Assistant: {msg.get('response', 'N/A')}")
                prompt_parts.append("")
            prompt_parts.append("")
        
        # 4. COMMAND (comando atual - sempre no final)
        prompt_parts.append("### COMMAND:")
        prompt_parts.append(new_prompt)
        prompt_parts.append("")
        prompt_parts.append("IMPORTANTE: Responda APENAS ao comando acima, usando o contexto fornecido.")
        
        return "\n".join(prompt_parts)


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
            full_prompt = self._build_full_prompt_with_persona(prompt)
            cmd = [self.claude_command, "--print", "--dangerously-skip-permissions"]
            
            # Add available tools if genesis_agent is available
            if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'get_available_tools'):
                available_tools = self.genesis_agent.get_available_tools()
                if available_tools:
                    cmd.extend(["--allowedTools", " ".join(available_tools)])
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                # Add to conversation history AFTER receiving response from Claude
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
        self.gemini_command = "gemini"  # Assuming a similar CLI interface
        logger.debug("GeminiCLIClient initialized")

    def invoke(self, prompt: str) -> str:
        """Invoke Gemini CLI with the given prompt."""
        # For now, this is a placeholder implementation
        # In a real scenario, you would implement the actual Gemini CLI integration
        try:
            full_prompt = self._build_full_prompt_with_persona(prompt)
            
            # This is a simplified implementation - replace with actual Gemini CLI calls
            logger.info("GeminiCLIClient: Processing prompt (placeholder implementation)")
            
            # Simulate response (replace with real Gemini CLI call)
            response = f"[Gemini Response to: {prompt[:50]}...]"
            
            # Add to conversation history
            self.conversation_history.append({
                'prompt': prompt, 
                'response': response, 
                'timestamp': time.time()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini CLI error: {e}")
            raise LLMClientError(f"Gemini CLI error: {e}")


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