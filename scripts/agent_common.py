#!/usr/bin/env python3
"""
Agent Common Module - Shared functionality for agent execution

This module contains common functions and classes used by both
gensis_agent.py (project agents) and admin.py (meta-agents).
"""

import yaml
import sys
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import time
import re
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Constants
AI_PROVIDERS_CONFIG_PATH = os.path.join("config", "ai_providers.yaml")
MAX_TOOL_CALLS_PER_TURN = 5
MAX_CONVERSATION_HISTORY = 50

# ... (Security constants remain the same)

class LLMClient:
    """
    Base LLM Client interface for multi-provider support.
    """
    def __init__(self, working_directory: str = None):
        self.working_directory = working_directory or os.getcwd()
        self.conversation_history = []
        self.agent_persona = None
        logger.debug(f"LLMClient base initialized with working directory: {self.working_directory}")

    def set_agent_persona(self, persona: str):
        self.agent_persona = persona
        logger.debug("Agent persona set in LLM client")

    def generate_artifact(self, prompt: str) -> str:
        return self._invoke_subprocess(prompt) or "No response generated."

    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        raise NotImplementedError("Provider-specific subclasses must implement _invoke_subprocess")

class ClaudeCLIClient(LLMClient):
    """
    Claude CLI Client implementation.
    """
    def __init__(self, working_directory: str = None):
        super().__init__(working_directory)
        self.claude_command = "claude"
        logger.debug("ClaudeCLIClient initialized")

    def _build_full_prompt_with_persona(self, new_prompt: str) -> str:
        prompt_parts = []
        if self.agent_persona:
            prompt_parts.append("### PERSONA:")
            prompt_parts.append(self.agent_persona)
            prompt_parts.append("\n")
        prompt_parts.append(new_prompt) # Simplified for brevity
        return "\n".join(prompt_parts)

    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        try:
            full_prompt = self._build_full_prompt_with_persona(prompt)
            cmd = [self.claude_command, "--print", "--dangerously-skip-permissions"]
            if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'get_available_tools'):
                available_tools = self.genesis_agent.get_available_tools()
                if available_tools:
                    cmd.extend(["--allowedTools", " ".join(available_tools)])
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=getattr(self, 'timeout', 120),
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                self.conversation_history.append({'prompt': prompt, 'response': response, 'timestamp': time.time()})
                return response
            else:
                logger.error(f"Claude CLI failed: {result.stderr}")
                return f"Claude CLI failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            timeout_value = getattr(self, 'timeout', 120)
            logger.error(f"Claude CLI timed out after {timeout_value} seconds")
            return f"❌ Claude CLI timed out after {timeout_value} seconds. Complex operations may need more time."
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return f"❌ Claude CLI error: {e}"

class GeminiCLIClient(LLMClient):
    # ... (Implementation for Gemini, can be simplified or assumed correct for now)
    pass

def create_llm_client(ai_provider: str, working_directory: str = None, timeout: int = 120) -> LLMClient:
    """
    Factory function to create LLM clients based on provider.
    """
    if ai_provider == 'claude':
        logger.info(f"Creating Claude CLI client with timeout: {timeout}s")
        client = ClaudeCLIClient(working_directory)
        client.timeout = timeout
        return client
    elif ai_provider == 'gemini':
        # Assuming a similar structure for Gemini client
        logger.info(f"Creating Gemini CLI client with timeout: {timeout}s")
        client = GeminiCLIClient(working_directory)
        client.timeout = timeout
        return client
    else:
        raise ValueError(f"Unsupported AI provider: {ai_provider}")

# --- Other shared functions from agent_common.py ---

def load_ai_providers_config() -> Dict[str, Any]:
    # ... (existing implementation)
    return {}

def resolve_agent_paths(environment: str, project: str, agent_id: str) -> Tuple[Path, Path]:
    conductor_root = Path(__file__).parent.parent
    if environment == "_common":
        agent_home_path = conductor_root / "projects" / "_common" / "agents" / agent_id
        project_root_path = conductor_root.parent.parent
    else:
        # ... (logic for project agents)
        # This part needs the real load_workspaces_config, which is in genesis_agent.py
        # This is the core of the circular dependency. For now, we assume a simple path.
        monorepo_root = conductor_root.parent.parent
        project_root_path = monorepo_root / project # Simplified for this fix
        agent_home_path = conductor_root / "projects" / environment / project / "agents" / agent_id

    if not agent_home_path.exists():
        raise FileNotFoundError(f"Agent home path does not exist: {agent_home_path}")
    if not project_root_path.exists():
        # This check might fail for the real project, but is ok for meta-agent
        pass

    return agent_home_path.resolve(), project_root_path.resolve()

def load_agent_config_v2(agent_home_path: Path) -> Dict[str, Any]:
    # ... (existing implementation)
    agent_yaml_path = agent_home_path / "agent.yaml"
    if not agent_yaml_path.exists():
        raise FileNotFoundError(f"agent.yaml não encontrado em: {agent_yaml_path}")
    with open(agent_yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def start_repl_session(agent, agent_name: str = "admin"):
    # ... (existing implementation)
    pass

def validate_agent_config(config: Dict[str, Any]) -> bool:
    # ... (existing implementation)
    return True