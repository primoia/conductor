#!/usr/bin/env python3
"""
Genesis Core - Main Agent Runtime

This module contains the core GenesisAgent class responsible for loading and 
incorporating specialist agents as defined in the Maestro framework specification.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
sys.path.insert(0, str(scripts_dir))

# Import shared functionality
from agent_common import (
    load_ai_providers_config,
    load_agent_config_v2,
    resolve_agent_paths,
    create_llm_client,
    validate_agent_config,
    load_workspaces_config
)
from .state_repository import StateRepository
# Toolbelt will be imported when needed to avoid circular imports

logger = logging.getLogger(__name__)


class GenesisAgent:
    """
    Main Genesis Agent class implementing the "embodiment" functionality.
    
    This class is responsible for loading and incorporating specialist agents
    as defined in the Maestro framework specification.
    """
    
    def __init__(self, environment: str = None, project: str = None, agent_id: str = None, 
                 ai_provider: str = None, timeout: int = 120, state_repository: StateRepository = None):
        """
        Initialize the Genesis Agent for v2.0 architecture.
        
        Args:
            environment: Nome do ambiente (develop, main, etc.) - obrigatório para v2.0
            project: Nome do projeto alvo - obrigatório para v2.0
            agent_id: ID do agente para embodiment - opcional, pode ser feito depois
            ai_provider: AI provider override - se não especificado, usa configuração dual por tarefa
            state_repository: StateRepository implementation para gerenciamento de estado
        """
        # Load AI providers configuration for dual provider logic
        self.ai_providers_config = load_ai_providers_config()
        self.ai_provider_override = ai_provider  # Agent-specific override if provided
        self.timeout = timeout  # Store timeout for LLM operations
        
        # State repository injection
        if state_repository is None:
            # Default para FileStateRepository se não fornecido
            from .state_repository import FileStateRepository
            self.state_repository = FileStateRepository()
        else:
            self.state_repository = state_repository
        
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
        
        # Initialize toolbelt - import here to avoid circular imports
        try:
            # Add parent directory to path to access toolbelt from genesis_agent
            sys.path.insert(0, str(scripts_dir))
            from genesis_agent import Toolbelt
            self.toolbelt = Toolbelt(self.working_directory, genesis_agent=self)
        except ImportError:
            logger.warning("Toolbelt not available - some functionality may be limited")
            self.toolbelt = None
        
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
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not self.agent_config:
            return []
        return self.agent_config.get('available_tools', [])
    
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
            self.llm_client = create_llm_client(chat_provider, str(self.project_root_path), self.timeout)
            
            # Pass reference to this agent for tool access
            self.llm_client.genesis_agent = self
            
            logger.info(f"Initialized LLM client with chat provider: {chat_provider}")
            
            # FUNDAMENTAL: Muda para o diretório do projeto alvo (Project Resident Mode)
            logger.info(f"Changing working directory to project: {self.project_root_path}")
            os.chdir(str(self.project_root_path))
            
            # Atualiza working directory de todos os componentes
            self.working_directory = str(self.project_root_path)
            if self.toolbelt:
                self.toolbelt.working_directory = str(self.project_root_path)
            
            # Carrega estado do agente usando StateRepository
            state_file_name = self.agent_config.get("state_file_path", "state.json")
            state_data = self.state_repository.load_state(str(self.agent_home_path), state_file_name)
            self.llm_client.conversation_history = state_data.get("conversation_history", [])
            
            # Carrega persona do agente (usando caminho absoluto)
            persona_path = self.agent_home_path / self.agent_config.get("persona_prompt_path", "persona.md")
            if not self._load_agent_persona(str(persona_path), agent_id):
                return False
            
            # Salva paths absolutos para gestão de estado
            # Para project-resident agents, salva o state no diretório do projeto
            if self.agent_config.get('execution_mode') == 'project_resident':
                self.state_file_path = str(self.project_root_path / "agents" / agent_id / "state.json")
            else:
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
        Salva estado do agente v2.0 usando StateRepository.
        """
        if not self.agent_home_path:
            logger.warning("No agent home path configured for v2.0 agent")
            return
        
        try:
            state_data = {
                'conversation_history': self.llm_client.conversation_history,
                'last_modified': datetime.now().isoformat(),
                'agent_id': self.current_agent,
                'environment': self.environment,
                'project': self.project
            }
            
            state_file_name = self.agent_config.get("state_file_path", "state.json")
            success = self.state_repository.save_state(str(self.agent_home_path), state_file_name, state_data)
            
            if success:
                logger.info(f"Agent state saved successfully")
            else:
                logger.error("Failed to save agent state")
            
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
            '{{environment}}': getattr(self, 'environment', 'develop'),
            '{{project}}': getattr(self, 'project', 'unknown'),
            '{{project_key}}': getattr(self, 'project', 'unknown'),
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
                self.llm_client = create_llm_client(current_provider, self.working_directory, self.timeout)
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
            generation_client = create_llm_client(generation_provider, self.working_directory, self.timeout)
            
            # Transfer conversation history for context
            if hasattr(self, '_conversation_history'):
                generation_client.conversation_history = self._conversation_history.copy()
            
            # Generate artifact
            response = generation_client._invoke_subprocess(prompt)
            
            return response or "No artifact generated."
        except Exception as e:
            logger.error(f"Artifact generation failed: {e}")
            return f"Error generating artifact: {e}"