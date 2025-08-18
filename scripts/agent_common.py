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

# Error Handling and Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0
RETRY_DELAY_MULTIPLIER = 2.0
MAX_RETRY_DELAY = 30.0

# Recoverable error types
RECOVERABLE_IO_ERRORS = (OSError, IOError, PermissionError)
RECOVERABLE_NETWORK_ERRORS = (ConnectionError, TimeoutError)
RECOVERABLE_RESOURCE_ERRORS = (MemoryError, OSError)

# Security Configuration
ALLOWED_AGENT_FIELDS = {
    'id', 'version', 'description', 'ai_provider', 'persona_prompt_path', 
    'state_file_path', 'execution_task', 'available_tools', 'test_framework'
}

DANGEROUS_PATTERNS = [
    r'rm\s+-rf?\s+/', r'sudo\s+', r'chmod\s+777', r'>/dev/', r'\|\s*sh\b',
    r'eval\s*\(', r'exec\s*\(', r'system\s*\(', r'\$\([^)]*\)',
    r'__import__', r'open\s*\(.*[\'"\\]w', r'delete\s+from', r'drop\s+table',
    r'truncate\s+table', r'alter\s+table', r'create\s+user', r'grant\s+all'
]

MAX_TEMPLATE_SIZE = 50000
MAX_EXECUTION_TASK_LENGTH = 2000
MAX_AGENTS_PER_TEMPLATE = 20


def load_ai_providers_config() -> Dict[str, Any]:
    """Load AI providers configuration from config file."""
    try:
        config_path = Path(AI_PROVIDERS_CONFIG_PATH)
        if not config_path.exists():
            logger.warning(f"AI providers config not found: {config_path}")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load AI providers config: {e}")
        return {}


def load_agent_config_v2(agent_home_path: Path) -> Dict[str, Any]:
    """
    Carrega a configuração do agente da nova estrutura v2.0.
    
    Args:
        agent_home_path: Caminho para o diretório do agente
        
    Returns:
        Configuração do agente com target_context
        
    Raises:
        FileNotFoundError: Se agent.yaml não existir
        ValueError: Se configuração for inválida para v2.0
    """
    agent_yaml_path = agent_home_path / "agent.yaml"
    
    if not agent_yaml_path.exists():
        raise FileNotFoundError(f"agent.yaml não encontrado em: {agent_yaml_path}")
    
    try:
        with open(agent_yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Erro ao fazer parse de agent.yaml: {e}")
    
    # Valida se é um agente v2.0
    version = config.get('version', '1.0')
    if str(version) != '2.0':
        raise ValueError(
            f"Agente não é v2.0 (versão atual: {version}). "
            f"Execute o script de migração: python scripts/migrate_agents_v2.py"
        )
    
    # Valida execution_mode
    execution_mode = config.get('execution_mode')
    if not execution_mode:
        raise ValueError("Campo 'execution_mode' obrigatório em agentes v2.0")
    
    return config


def resolve_agent_paths(environment: str, project: str, agent_id: str) -> Tuple[Path, Path]:
    """
    Resolve paths for agent and project in v2.0 architecture.
    
    Args:
        environment: Environment name (develop, main, etc.)
        project: Project name
        agent_id: Agent ID
        
    Returns:
        Tuple of (agent_home_path, project_root_path)
        
    Raises:
        FileNotFoundError: If agent or project not found
    """
    # Check if this is a meta-agent (in _common)
    # Meta-agents are specifically in projects/_common/agents/
    meta_agent_path = Path("projects") / "_common" / "agents" / agent_id
    if meta_agent_path.exists():
        # This is a meta-agent
        agent_home_path = meta_agent_path.resolve()
        # Meta-agents don't have a specific project context
        project_root_path = Path.cwd()
        
    else:
        # Regular project agents - need to resolve project_root using workspaces
        agent_home_path = Path("projects") / environment / project / "agents" / agent_id
        if not agent_home_path.exists():
            raise ValueError(
                f"Agente '{agent_id}' não encontrado em: {agent_home_path}\
"
                f"Verifique se o agente existe no projeto '{project}' no ambiente '{environment}'."
            )
        
        # Load workspaces configuration to resolve project root
        try:
            # Import here to avoid circular imports  
            import sys
            if 'scripts.genesis_agent' in sys.modules:
                load_workspaces_config = sys.modules['scripts.genesis_agent'].load_workspaces_config
            else:
                from genesis_agent import load_workspaces_config
            workspaces = load_workspaces_config()
            
            if environment not in workspaces:
                raise ValueError(
                    f"Environment '{environment}' não encontrado em workspaces.yaml\
"
                    f"Environments disponíveis: {list(workspaces.keys())}"
                )
            
            workspace_root = Path(workspaces[environment])
            project_root_path = workspace_root / project
            
            if not project_root_path.exists():
                raise ValueError(
                    f"Projeto '{project}' não encontrado em: {project_root_path}\
"
                    f"Verifique se o projeto existe no ambiente '{environment}'."
                )
                
        except ImportError:
            # Fallback to simple path resolution for tests or when load_workspaces_config is not available
            project_root_path = Path("projects") / environment / project
            if not project_root_path.exists():
                raise ValueError(
                    f"Projeto '{project}' não encontrado em: {project_root_path}\
"
                    f"Verifique se o projeto existe no ambiente '{environment}'."
                )
        
        # Convert to absolute paths
        agent_home_path = agent_home_path.resolve()
        project_root_path = project_root_path.resolve()
    
    return agent_home_path, project_root_path


def create_llm_client(ai_provider: str, working_directory: str = None) -> 'LLMClient':
    """Create LLM client for the specified provider."""
    # Import here to avoid circular imports
    try:
        from genesis_agent import create_llm_client as genesis_create_llm_client
        return genesis_create_llm_client(ai_provider, working_directory)
    except ImportError:
        logger.error("LLMClient not available")
        raise

def start_repl_session(agent, agent_name: str = "admin"):
    """Start interactive REPL session for the agent."""
    print("\n" + "="*60)
    print("🎼 Agent REPL started")
    print("Commands: 'exit' to quit, 'save' to save state")
    print("Generation: 'gerar documento', 'preview', 'consolidar' use generation provider")
    print("="*60)
    
    if hasattr(agent, 'embodied') and agent.embodied:
        chat_provider = agent.get_chat_provider()
        generation_provider = agent.get_generation_provider()
        print(f"💬 Chat provider: {chat_provider}")
        print(f"🏗️  Generation provider: {generation_provider}")
        print("="*60)
    
    while True:
        user_input = ""
        try:
            # Check if we're receiving piped input (non-interactive mode)
            import sys
            if not sys.stdin.isatty():
                # Read all available input as one message for non-interactive mode
                lines = []
                commands = []
                try:
                    while True:
                        line = input()
                        # Separate commands from content
                        if line.lower().strip() in ['exit', 'quit', 'gerar documento', 'preview', 'consolidar', 'clear', 'help']:
                            commands.append(line.lower().strip())
                        else:
                            lines.append(line)
                except EOFError:
                    # End of input reached - process content first, then commands
                    if lines:
                        user_input = '\n'.join(lines)
                        print(f"[{agent.current_agent or agent_name}]> ")
                        print(f"📝 Processing multi-line input ({len(lines)} lines)...")
                        
                        # Process the main content message
                        generation_commands = ['gerar documento', 'preview', 'consolidar', 'criar artefato', 'salvar documento']
                        is_generation_task = any(cmd in user_input.lower() for cmd in generation_commands)
                        
                        try:
                            if is_generation_task:
                                print(f"🏗️  Using generation provider for artifact creation...")
                                response = agent.generate_artifact(user_input)
                            else:
                                response = agent.chat(user_input)
                            
                            print(response)

                        except Exception as agent_error:
                            print(f"\n❌ Erro na execução do agente: {agent_error}")
                            print("   A sessão REPL continua ativa. Você pode tentar novamente ou digitar 'exit'.")
                        
                        # Save state after processing
                        if hasattr(agent, 'save_agent_state_v2'):
                            agent.save_agent_state_v2()
                    
                    # Now process commands
                    for cmd in commands:
                        if cmd in ['exit', 'quit']:
                            print("👋 Encerrando sessão.")
                            return
                        elif cmd == 'gerar documento':
                            print("🏗️  Using generation provider for document generation...")
                            try:
                                response = agent.generate_artifact("gerar documento")
                                print(response)
                            except Exception as e:
                                print(f"❌ Error generating document: {e}")
                            if hasattr(agent, 'save_agent_state_v2'):
                                agent.save_agent_state_v2()
                        # Handle other commands as needed
                    
                    # Exit after processing all
                    print("👋 Encerrando sessão.")
                    return
            else:
                # Interactive mode - read line by line as before
                user_input = input(f"[{agent.current_agent or agent_name}]> ")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Encerrando sessão.")
            break

        # Process the user input if it was successfully received.
        if user_input.lower() in ['exit', 'quit']:
            break
        
        if user_input.lower() == 'save':
            if hasattr(agent, 'save_agent_state_v2'):
                agent.save_agent_state_v2()
            else:
                print("⚠️  State saving not available")
            continue

        if user_input.lower() in ['help', '?']:
            chat_prov = agent.get_chat_provider() if hasattr(agent, 'get_chat_provider') else 'N/A'
            gen_prov = agent.get_generation_provider() if hasattr(agent, 'get_generation_provider') else 'N/A'
            print("Commands:")
            print("  'exit'/'quit' = quit session")
            print("  'save' = save agent state")
            print("  'help'/'?' = this message")
            print(f"  Current chat provider: {chat_prov}")
            print(f"  Current generation provider: {gen_prov}")
            continue

        if not user_input.strip():
            continue

        # Inner try-except block for recoverable agent errors during processing.
        try:
            generation_commands = ['gerar documento', 'preview', 'consolidar', 'criar artefato', 'salvar documento']
            is_generation_task = any(cmd in user_input.lower() for cmd in generation_commands)
            
            if is_generation_task:
                print(f"🏗️  Using generation provider for artifact creation...")
                response = agent.generate_artifact(user_input)
            else:
                response = agent.chat(user_input)
            
            print(response)

        except Exception as agent_error:
            print(f"\n❌ Erro na execução do agente: {agent_error}")
            print("   A sessão REPL continua ativa. Você pode tentar novamente ou digitar 'exit'.")
            continue
        
        if hasattr(agent, 'save_agent_state_v2'):
            agent.save_agent_state_v2()
    
    print("\n👋 Agent session completed")


def validate_agent_config(config: Dict[str, Any]) -> bool:
    """Validate agent configuration for security and correctness."""
    execution_task = config.get('execution_task', '')
    if execution_task:
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, execution_task, re.IGNORECASE):
                raise ValueError(f"Dangerous pattern detected in execution_task: {pattern}")
    
    if len(execution_task) > MAX_EXECUTION_TASK_LENGTH:
        raise ValueError(f"execution_task too long ({len(execution_task)} chars, max {MAX_EXECUTION_TASK_LENGTH})")
    
    return True
