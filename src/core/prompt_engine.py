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

    def __init__(self, agent_home_path: str):
        """
        Inicializa o PromptEngine com o caminho para o diretório principal do agente.
        """
        self.agent_home_path = Path(agent_home_path)
        self.agent_config: Dict[str, Any] = {}
        self.persona_content: str = ""
        self.playbook: Dict[str, Any] = {}
        self.playbook_content: str = ""
        logger.debug(f"PromptEngine inicializado para o caminho: {agent_home_path}")

    def load_context(self) -> None:
        """
        Carrega e processa todos os artefatos de contexto do agente.
        Esta é a principal função de inicialização.
        """
        self._load_agent_config()
        self._validate_agent_config()
        self._load_agent_persona()
        self._load_agent_playbook()
        self._resolve_persona_placeholders()

    def build_prompt(self, conversation_history: List[Dict], message: str) -> str:
        """Constrói o prompt final usando o contexto já carregado."""
        if not self.persona_content or not self.agent_config:
            raise ValueError(
                "Contexto não foi carregado. Chame load_context() primeiro."
            )

        formatted_history = self._format_history(conversation_history)
        agent_instructions = self.agent_config.get("prompt", "")

        # SAFETY: Truncate persona if too long to prevent system errors
        MAX_PERSONA_LENGTH = 20000  # Reasonable limit for persona content
        persona_content = self.persona_content
        if len(persona_content) > MAX_PERSONA_LENGTH:
            logger.warning(
                f"Persona content too long ({len(persona_content)} chars), truncating"
            )
            persona_content = (
                persona_content[:MAX_PERSONA_LENGTH]
                + "\n\n[PERSONA TRUNCADA PARA EVITAR ERROS DE SISTEMA]"
            )

        # SAFETY: Truncate instructions if too long
        MAX_INSTRUCTIONS_LENGTH = 5000
        if len(agent_instructions) > MAX_INSTRUCTIONS_LENGTH:
            logger.warning(
                f"Agent instructions too long ({len(agent_instructions)} chars), truncating"
            )
            agent_instructions = (
                agent_instructions[:MAX_INSTRUCTIONS_LENGTH]
                + "\n\n[INSTRUÇÕES TRUNCADAS]"
            )

        # Include playbook content if available
        playbook_section = ""
        if self.playbook_content:
            playbook_section = f"""

### KNOWLEDGE BASE
{self.playbook_content}
"""

        final_prompt = f"""
{persona_content}

### INSTRUÇÕES DO AGENTE
{agent_instructions}
{playbook_section}
### HISTÓRICO DA TAREFA ATUAL
{formatted_history}
### NOVA INSTRUÇÃO DO USUÁRIO
{message}
"""

        # Final safety check on complete prompt
        if len(final_prompt) > 40000:  # Conservative limit
            logger.warning(
                f"Final prompt very long ({len(final_prompt)} chars) - may cause system errors"
            )

        logger.info(f"Prompt final construído com sucesso ({len(final_prompt)} chars).")
        return final_prompt

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not self.agent_config:
            return []
        return self.agent_config.get("available_tools", [])

    def _load_agent_config(self) -> None:
        """Carrega configuração do agente a partir do definition.yaml."""
        definition_yaml_path = self.agent_home_path / "definition.yaml"
        if not definition_yaml_path.exists():
            raise AgentNotFoundError(f"definition.yaml not found: {definition_yaml_path}")

        try:
            with open(definition_yaml_path, "r", encoding="utf-8") as f:
                self.agent_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing definition.yaml: {e}")

    def _validate_agent_config(self) -> None:
        """Valida a configuração carregada do agente."""
        if self.agent_config is None:
            raise ConfigurationError("Agent config is None")

        # Check for either 'name' or 'id' field
        if "name" not in self.agent_config and "id" not in self.agent_config:
            raise ConfigurationError(
                "Required field 'name' or 'id' missing in agent configuration"
            )

    def _load_agent_persona(self) -> None:
        """Carrega o conteúdo da persona do agente."""
        persona_prompt_path = self.agent_config.get("persona_prompt_path", "persona.md")
        persona_path = self.agent_home_path / persona_prompt_path

        if not persona_path.exists():
            raise AgentNotFoundError(f"Persona file not found: {persona_path}")

        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                self.persona_content = f.read()

        except Exception as e:
            raise ConfigurationError(f"Error loading agent persona: {e}")

    def _load_agent_playbook(self) -> None:
        """Carrega o conteúdo do playbook do agente (opcional)."""
        playbook_path = self.agent_home_path / "playbook.yaml"
        
        if not playbook_path.exists():
            logger.debug(f"Playbook file not found: {playbook_path} (optional)")
            self.playbook = {}
            self.playbook_content = ""
            return

        try:
            with open(playbook_path, "r", encoding="utf-8") as f:
                playbook_raw_content = f.read()
                self.playbook = yaml.safe_load(playbook_raw_content)
                self.playbook_content = self._format_playbook_for_prompt(self.playbook)
                logger.debug(f"Playbook loaded successfully from: {playbook_path}")

        except yaml.YAMLError as e:
            logger.warning(f"Error parsing playbook.yaml: {e}")
            self.playbook = {}
            self.playbook_content = ""
        except Exception as e:
            logger.warning(f"Error loading agent playbook: {e}")
            self.playbook = {}
            self.playbook_content = ""

    def _format_playbook_for_prompt(self, playbook_data: Dict[str, Any]) -> str:
        """Formata o playbook para inclusão no prompt."""
        if not playbook_data:
            return ""
        
        formatted_sections = []
        
        # Best Practices section
        best_practices = playbook_data.get("best_practices", [])
        if best_practices:
            formatted_sections.append("## BEST PRACTICES")
            for bp in best_practices:
                bp_text = f"• **{bp.get('title', 'Untitled')}** ({bp.get('id', 'N/A')})\n"
                bp_text += f"  {bp.get('description', 'No description')}"
                if bp.get('category'):
                    bp_text += f"\n  Category: {bp['category']}"
                if bp.get('priority'):
                    bp_text += f" | Priority: {bp['priority']}"
                formatted_sections.append(bp_text)
        
        # Anti-patterns section
        anti_patterns = playbook_data.get("anti_patterns", [])
        if anti_patterns:
            formatted_sections.append("\n## ANTI-PATTERNS TO AVOID")
            for ap in anti_patterns:
                ap_text = f"• **{ap.get('title', 'Untitled')}** ({ap.get('id', 'N/A')})\n"
                ap_text += f"  {ap.get('description', 'No description')}"
                if ap.get('category'):
                    ap_text += f"\n  Category: {ap['category']}"
                if ap.get('severity'):
                    ap_text += f" | Severity: {ap['severity']}"
                formatted_sections.append(ap_text)
        
        # Guidelines section (if exists)
        guidelines = playbook_data.get("guidelines", {})
        if guidelines:
            formatted_sections.append("\n## GUIDELINES")
            for guideline_type, guideline_content in guidelines.items():
                if isinstance(guideline_content, list):
                    formatted_sections.append(f"**{guideline_type.replace('_', ' ').title()}:**")
                    for item in guideline_content:
                        formatted_sections.append(f"• {item}")
                elif isinstance(guideline_content, dict):
                    formatted_sections.append(f"**{guideline_type.replace('_', ' ').title()}:**")
                    for key, value in guideline_content.items():
                        if isinstance(value, list):
                            formatted_sections.append(f"  {key.replace('_', ' ').title()}:")
                            for item in value:
                                formatted_sections.append(f"  • {item}")
        
        return "\n".join(formatted_sections)

    def _resolve_persona_placeholders(self) -> None:
        """Resolve placeholders dinâmicos no conteúdo da persona."""
        if self.persona_content is None:
            return

        processed_content = self.persona_content

        # Get agent information for placeholder resolution
        agent_id = self.agent_config.get("name") or self.agent_config.get(
            "id", "Unknown_Agent"
        )

        # Extract friendly name from persona title if available
        friendly_name = self._extract_persona_title(self.persona_content) or agent_id

        # Ensure we have valid string values for replacements
        agent_id = agent_id if agent_id else "Unknown_Agent"
        agent_description = self.agent_config.get(
            "description", f"{agent_id} specialized agent"
        )
        agent_description = (
            agent_description if agent_description else f"{agent_id} specialized agent"
        )

        # Define common placeholder mappings
        placeholders = {
            "Contexto": friendly_name,  # Replace "Contexto" with friendly name
            "{{agent_id}}": agent_id,
            "{{agent_name}}": friendly_name,
            "{{agent_description}}": agent_description,
            # Note: environment and project placeholders would need to be passed in if needed
        }

        # Apply placeholder replacements only with valid strings
        for placeholder, replacement in placeholders.items():
            if replacement and isinstance(replacement, str):
                processed_content = processed_content.replace(placeholder, replacement)

        self.persona_content = processed_content
        logger.debug(
            f"Resolved placeholders in persona for agent: {agent_id} (friendly: {friendly_name})"
        )

    def _extract_persona_title(self, persona_content: str) -> Optional[str]:
        """Extract friendly name from persona title."""
        # Look for "# Persona: [Title]" pattern
        title_match = re.search(r"^#\s*Persona:\s*(.+)$", persona_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Clean up common patterns
            title = re.sub(r"Agent$", "", title)  # Remove trailing "Agent"
            title = title.strip()
            return title

        return None

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """
        Formata o histórico da conversa em uma string legível.
        Limita o histórico para evitar prompts muito longos que causam erros de sistema.
        """
        if not history:
            return "Nenhum histórico de conversa para esta tarefa ainda."

        # Limitar histórico para evitar "Argument list too long"
        # Manter apenas as últimas 5 interações para contexto
        MAX_HISTORY_TURNS = 5
        recent_history = (
            history[-MAX_HISTORY_TURNS:]
            if len(history) > MAX_HISTORY_TURNS
            else history
        )

        formatted_lines = []
        for turn in recent_history:
            # Use the correct field names as saved by agent_executor
            user_input = turn.get("user_input", "")
            ai_response = turn.get("ai_response", "")

            # Truncar mensagens muito longas
            MAX_MESSAGE_LENGTH = 1000
            if len(user_input) > MAX_MESSAGE_LENGTH:
                user_input = user_input[:MAX_MESSAGE_LENGTH] + "... [truncado]"
            if len(ai_response) > MAX_MESSAGE_LENGTH:
                ai_response = ai_response[:MAX_MESSAGE_LENGTH] + "... [truncado]"

            formatted_lines.append(f"Usuário: {user_input}\nIA: {ai_response}")

        # Adicionar indicador se histórico foi truncado
        if len(history) > MAX_HISTORY_TURNS:
            formatted_lines.insert(
                0,
                f"[Mostrando últimas {MAX_HISTORY_TURNS} de {len(history)} interações]",
            )

        return "\n---\n".join(formatted_lines)
