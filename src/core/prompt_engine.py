# src/core/prompt_engine.py
import os
import yaml
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.exceptions import AgentNotFoundError, ConfigurationError

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Guardião central de todo o contexto de um agente.
    Responsável por carregar, processar e construir prompts.
    """
    
    def __init__(self, agent_home_path: Path):
        self.agent_home_path = agent_home_path
        self.persona_content: Optional[str] = None
        self.agent_config: Optional[Dict[str, Any]] = None
        logger.debug(f"PromptEngine inicializado para o caminho: {agent_home_path}")

    def load_context(self) -> None:
        """
        Carrega e processa todos os artefatos de contexto do agente.
        Esta é a principal função de inicialização.
        """
        self._load_agent_config()
        self._validate_agent_config()
        self._load_agent_persona()
        self._resolve_persona_placeholders()
        logger.info(f"Contexto para o agente em '{self.agent_home_path}' carregado com sucesso.")

    def build_prompt(self, conversation_history: List[Dict[str, Any]], user_input: str) -> str:
        """Constrói o prompt final usando o contexto já carregado."""
        if self.persona_content is None or self.agent_config is None:
            raise ValueError("Contexto não foi carregado. Chame load_context() primeiro.")
            
        formatted_history = self._format_history(conversation_history)
        agent_instructions = self.agent_config.get('prompt', '')
        
        final_prompt = f"""
{self.persona_content}

### INSTRUÇÕES DO AGENTE
{agent_instructions}

### HISTÓRICO DA TAREFA ATUAL
{formatted_history}
### NOVA INSTRUÇÃO DO USUÁRIO
{user_input}
"""
        logger.info("Prompt final construído com sucesso.")
        return final_prompt

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not self.agent_config:
            return []
        return self.agent_config.get('available_tools', [])

    def _load_agent_config(self) -> None:
        """Lógica movida do AgentLogic para carregar agent.yaml."""
        agent_yaml_path = self.agent_home_path / "agent.yaml"
        if not agent_yaml_path.exists():
            raise AgentNotFoundError(f"agent.yaml not found: {agent_yaml_path}")
        
        try:
            with open(agent_yaml_path, 'r', encoding='utf-8') as f:
                self.agent_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing agent.yaml: {e}")

    def _validate_agent_config(self) -> None:
        """Lógica movida do AgentLogic para validar a configuração."""
        if self.agent_config is None:
            raise ConfigurationError("Agent config is None")
            
        # Check for either 'name' or 'id' field
        if 'name' not in self.agent_config and 'id' not in self.agent_config:
            raise ConfigurationError("Required field 'name' or 'id' missing in agent configuration")

    def _load_agent_persona(self) -> None:
        """Lógica movida do AgentLogic para carregar persona.md."""
        persona_prompt_path = self.agent_config.get("persona_prompt_path", "persona.md")
        persona_path = self.agent_home_path / persona_prompt_path
        
        if not persona_path.exists():
            raise AgentNotFoundError(f"Persona file not found: {persona_path}")
        
        try:
            with open(persona_path, 'r', encoding='utf-8') as f:
                self.persona_content = f.read()
                
        except Exception as e:
            raise ConfigurationError(f"Error loading agent persona: {e}")

    def _resolve_persona_placeholders(self) -> None:
        """Lógica movida do AgentLogic para resolver placeholders na persona."""
        if self.persona_content is None:
            return
            
        processed_content = self.persona_content
        
        # Get agent information for placeholder resolution  
        agent_id = self.agent_config.get('name') or self.agent_config.get('id', 'Unknown_Agent')
        
        # Extract friendly name from persona title if available
        friendly_name = self._extract_persona_title(self.persona_content) or agent_id
        
        # Ensure we have valid string values for replacements
        agent_id = agent_id if agent_id else 'Unknown_Agent'
        agent_description = self.agent_config.get('description', f'{agent_id} specialized agent')
        agent_description = agent_description if agent_description else f'{agent_id} specialized agent'
        
        # Define common placeholder mappings
        placeholders = {
            'Contexto': friendly_name,  # Replace "Contexto" with friendly name
            '{{agent_id}}': agent_id,
            '{{agent_name}}': friendly_name,
            '{{agent_description}}': agent_description,
            # Note: environment and project placeholders would need to be passed in if needed
        }
        
        # Apply placeholder replacements only with valid strings
        for placeholder, replacement in placeholders.items():
            if replacement and isinstance(replacement, str):
                processed_content = processed_content.replace(placeholder, replacement)
        
        self.persona_content = processed_content
        logger.debug(f"Resolved placeholders in persona for agent: {agent_id} (friendly: {friendly_name})")

    def _extract_persona_title(self, persona_content: str) -> Optional[str]:
        """Extract friendly name from persona title."""
        # Look for "# Persona: [Title]" pattern
        title_match = re.search(r'^#\s*Persona:\s*(.+)$', persona_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up common patterns
            title = re.sub(r'Agent$', '', title)  # Remove trailing "Agent"
            title = title.strip()
            return title
        
        return None

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """
        Formata o histórico da conversa em uma string legível.
        """
        if not history:
            return "Nenhum histórico de conversa para esta tarefa ainda."
        
        formatted_lines = []
        for turn in history:
            prompt = turn.get("prompt", "")
            response = turn.get("response", "")
            formatted_lines.append(f"Usuário: {prompt}\nIA: {response}")
        
        return "\n---\n".join(formatted_lines)