# src/core/prompt_engine.py
import os
import yaml
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.dom.minidom

from src.core.exceptions import AgentNotFoundError, ConfigurationError

logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Guardião central de todo o contexto de um agente.
    Responsável por carregar, processar e construir prompts.
    """

    def __init__(self, agent_home_path: str, prompt_format: str = "xml", instance_id: Optional[str] = None):
        """
        Inicializa o PromptEngine com o caminho para o diretório principal do agente.
        """
        self.agent_home_path = Path(agent_home_path)
        self.agent_config: Dict[str, Any] = {}
        self.persona_content: str = ""
        self.playbook: Dict[str, Any] = {}
        self.playbook_content: str = ""
        self.prompt_format = prompt_format  # "xml" or "text"
        self.is_mongodb = str(agent_home_path).startswith("mongodb://")
        self.instance_id = instance_id
        self.screenplay_content: str = ""

        # Extract agent_id from MongoDB path
        if self.is_mongodb:
            # mongodb://agents/{agent_id} -> {agent_id}
            self.agent_id = str(agent_home_path).split("/")[-1]
        else:
            self.agent_id = None

        logger.debug(f"PromptEngine inicializado para o caminho: {agent_home_path} (MongoDB: {self.is_mongodb}, Format: {self.prompt_format})")

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
        self._load_screenplay_context()

    def build_prompt(self, conversation_history: List[Dict], message: str, include_history: bool = True) -> str:
        """Constrói o prompt final usando o contexto já carregado."""
        if not self.persona_content or not self.agent_config:
            raise ValueError(
                "Contexto não foi carregado. Chame load_context() primeiro."
            )

        if include_history:
            formatted_history = self._format_history(conversation_history)
        else:
            formatted_history = "Execução isolada - sem histórico de conversas anteriores."
        # Get instructions from definition with fallbacks
        agent_instructions = (
            self.agent_config.get("prompt", "") or
            self.agent_config.get("instructions", "") or
            self.agent_config.get("description", "") or
            ""
        )

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

        # Save prompt to disk for debugging/analysis
        self._save_prompt_to_disk(final_prompt, "text")

        return final_prompt

    def build_prompt_with_format(self, conversation_history: List[Dict], message: str, include_history: bool = True) -> str:
        """
        Constrói o prompt final usando o formato configurado (XML ou texto).
        Este método substitui build_prompt() para suportar ambos os formatos.
        """
        if self.prompt_format == "xml":
            return self.build_xml_prompt(conversation_history, message, include_history)
        else:
            return self.build_prompt(conversation_history, message, include_history)

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not self.agent_config:
            return []
        return self.agent_config.get("available_tools", [])

    def _load_agent_config(self) -> None:
        """Carrega configuração do agente a partir do definition.yaml ou MongoDB."""
        if self.is_mongodb:
            # Load from MongoDB storage
            try:
                from src.container import container
                storage_service = container.get_storage_service()
                repository = storage_service.get_repository()
                config_data = repository.load_definition(self.agent_id)

                if not config_data:
                    raise AgentNotFoundError(f"Definition not found for agent: {self.agent_id}")

                self.agent_config = config_data

                # DEBUG: Log definition structure for debugging empty instructions
                logger.debug(f"MongoDB definition loaded for {self.agent_id}: {list(config_data.keys()) if config_data else 'None'}")
                if config_data:
                    logger.debug(f"Available fields: prompt={bool(config_data.get('prompt'))}, instructions={bool(config_data.get('instructions'))}, description={bool(config_data.get('description'))}")
            except Exception as e:
                raise ConfigurationError(f"Error loading agent definition from MongoDB: {e}")
        else:
            # Load from filesystem
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
        if self.is_mongodb:
            # Load from MongoDB storage
            try:
                from src.container import container
                storage_service = container.get_storage_service()
                repository = storage_service.get_repository()
                persona_content = repository.load_persona(self.agent_id)

                if not persona_content:
                    raise AgentNotFoundError(f"Persona not found for agent: {self.agent_id}")

                self.persona_content = persona_content
            except Exception as e:
                raise ConfigurationError(f"Error loading agent persona from MongoDB: {e}")
        else:
            # Load from filesystem
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
        if self.is_mongodb:
            # Load from MongoDB storage
            try:
                from src.container import container
                storage_service = container.get_storage_service()
                repository = storage_service.get_repository()
                playbook_data = repository.load_playbook(self.agent_id)

                if playbook_data:
                    self.playbook = playbook_data
                    self.playbook_content = self._format_playbook_for_prompt(self.playbook)
                    logger.debug(f"Playbook loaded successfully from MongoDB for agent: {self.agent_id}")
                else:
                    logger.debug(f"Playbook not found for agent: {self.agent_id} (optional)")
                    self.playbook = {}
                    self.playbook_content = ""
            except Exception as e:
                logger.warning(f"Error loading agent playbook from MongoDB: {e}")
                self.playbook = {}
                self.playbook_content = ""
        else:
            # Load from filesystem
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

    def _load_screenplay_context(self) -> None:
        """Carrega o contexto do screenplay associado à instância atual."""
        self.screenplay_content = ""
        if not self.instance_id:
            return

        try:
            import os
            from pymongo import MongoClient
            from bson.objectid import ObjectId
            
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                logger.debug("MONGO_URI não configurada, pulando carregamento do screenplay")
                return
                
            client = MongoClient(mongo_uri)
            db = client.conductor_state

            instance_doc = db.agent_instances.find_one({"instance_id": self.instance_id})
            if not instance_doc or "screenplay_id" not in instance_doc:
                logger.debug(f"Nenhum screenplay_id associado à instância {self.instance_id}")
                return

            screenplay_id = instance_doc["screenplay_id"]
            screenplay_doc = db.screenplays.find_one({"_id": ObjectId(screenplay_id)})

            if screenplay_doc and "content" in screenplay_doc:
                self.screenplay_content = screenplay_doc["content"]
                logger.info(f"Contexto do screenplay '{screenplay_id}' carregado.")

        except Exception as e:
            logger.warning(f"Falha ao carregar contexto do screenplay: {e}")

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

        # FILTER: Remove mensagens deletadas (soft delete)
        # Retrocompatibilidade: mensagens sem o campo isDeleted são tratadas como ativas
        active_history = [turn for turn in history if not turn.get("isDeleted", False)]

        # Limitar histórico para evitar "Argument list too long"
        # Manter apenas as últimas 100 interações para contexto
        MAX_HISTORY_TURNS = 100
        recent_history = (
            active_history[-MAX_HISTORY_TURNS:]
            if len(active_history) > MAX_HISTORY_TURNS
            else active_history
        )

        # SAFETY: Ensure chronological order (oldest first, newest last)
        # Sort by timestamp if available, otherwise keep original order
        try:
            # Try to sort by timestamp if available
            recent_history = sorted(recent_history, key=lambda x: x.get("timestamp", 0) or 0)
        except (TypeError, ValueError):
            # If sorting fails, keep original order but log warning
            logger.warning("Could not sort history by timestamp, keeping original order")

        formatted_lines = []
        for turn in recent_history:
            # Get user input with fallbacks
            user_input = (
                turn.get("user_input", "") or
                turn.get("prompt", "") or
                turn.get("user", "") or
                ""
            )

            # Get AI response with fallbacks
            ai_response = (
                turn.get("ai_response", "") or
                turn.get("response", "") or
                turn.get("assistant", "") or
                turn.get("output", "") or
                turn.get("summary", "") or  # ← Fallback para summary
                ""
            )

            # Truncar mensagens muito longas
            MAX_MESSAGE_LENGTH = 1000
            if len(user_input) > MAX_MESSAGE_LENGTH:
                user_input = user_input[:MAX_MESSAGE_LENGTH] + "... [truncado]"
            if len(ai_response) > MAX_MESSAGE_LENGTH:
                ai_response = ai_response[:MAX_MESSAGE_LENGTH] + "... [truncado]"

            # Add timestamp context if available
            timestamp = turn.get("timestamp", "")
            timestamp_info = ""
            if timestamp:
                try:
                    # Convert timestamp to readable format
                    if isinstance(timestamp, (int, float)):
                        from datetime import datetime
                        timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                    else:
                        timestamp_str = str(timestamp)[:16]  # Truncate if too long
                    timestamp_info = f" [{timestamp_str}]"
                except:
                    pass

            formatted_lines.append(f"Usuário{timestamp_info}: {user_input}\nIA: {ai_response}")

        # Adicionar indicador se histórico foi truncado
        if len(active_history) > MAX_HISTORY_TURNS:
            formatted_lines.insert(
                0,
                f"[Mostrando últimas {MAX_HISTORY_TURNS} de {len(active_history)} interações]",
            )

        return "\n---\n".join(formatted_lines)

    # --- XML Prompt Generation ---

    def _escape_xml_cdata(self, content: str) -> str:
        """Escapa o conteúdo para ser seguro dentro de uma seção CDATA."""
        if not isinstance(content, str):
            content = str(content)
        # A sequência ']]>' não pode aparecer dentro de um CDATA.
        # A forma de escapar é dividi-la em duas seções CDATA.
        return content.replace(']]>', ']]]]><![CDATA[>')

    def _format_history_xml(self, history: List[Dict[str, Any]]) -> str:
        """Formata o histórico da conversa como uma série de tags XML."""
        if not history:
            return "<history/>"

        # FILTER: Remove mensagens deletadas (soft delete)
        # Retrocompatibilidade: mensagens sem o campo isDeleted são tratadas como ativas
        active_history = [turn for turn in history if not turn.get("isDeleted", False)]

        MAX_HISTORY_TURNS = 100
        recent_history = (
            active_history[-MAX_HISTORY_TURNS:]
            if len(active_history) > MAX_HISTORY_TURNS
            else active_history
        )

        # SAFETY: Ensure chronological order (oldest first, newest last)
        # Sort by timestamp if available, otherwise keep original order
        try:
            # Try to sort by timestamp if available
            recent_history = sorted(recent_history, key=lambda x: x.get("timestamp", 0) or 0)
        except (TypeError, ValueError):
            # If sorting fails, keep original order but log warning
            logger.warning("Could not sort history by timestamp, keeping original order")
        
        xml_turns = []
        
        # Process history in pairs (user + assistant) for ConversationService format
        if recent_history and recent_history[0].get("role"):
            # ConversationService format: process in pairs
            i = 0
            while i < len(recent_history):
                turn = recent_history[i]
                
                # DEBUG: Log history structure
                logger.debug(f"History turn {i}: keys={list(turn.keys())}, role={turn.get('role')}")
                
                if turn.get("role") == "user":
                    user_input = turn.get("content", "")
                    ai_response = ""
                    
                    # Look for corresponding assistant response
                    if i + 1 < len(recent_history) and recent_history[i + 1].get("role") == "assistant":
                        ai_response = recent_history[i + 1].get("content", "")
                        i += 2  # Skip both user and assistant
                    else:
                        i += 1  # Only skip user
                    
                    # Get timestamp from user turn
                    timestamp = turn.get("timestamp", "")
                    timestamp_attr = f' timestamp="{timestamp}"' if timestamp else ""
                    
                    user_input = self._escape_xml_cdata(user_input)
                    ai_response = self._escape_xml_cdata(ai_response)
                    
                    xml_turns.append(f"""    <turn{timestamp_attr}>
            <user><![CDATA[{user_input}]]></user>
            <assistant><![CDATA[{ai_response}]]></assistant>
        </turn>""")
                else:
                    i += 1  # Skip non-user turns
        else:
            # Legacy format: process each turn individually
            for i, turn in enumerate(recent_history):
                # DEBUG: Log history structure
                logger.debug(f"History turn {i}: keys={list(turn.keys())}, user_input={bool(turn.get('user_input'))}, ai_response={bool(turn.get('ai_response'))}, summary={bool(turn.get('summary'))}")
                
                # Legacy format fallbacks
                user_input = (
                    turn.get("user_input", "") or
                    turn.get("prompt", "") or
                    turn.get("user", "") or
                    ""
                )

                ai_response = (
                    turn.get("ai_response", "") or
                    turn.get("response", "") or
                    turn.get("assistant", "") or
                    turn.get("output", "") or
                    turn.get("summary", "") or  # ← Fallback para summary
                    ""
                )

                user_input = self._escape_xml_cdata(user_input)
                ai_response = self._escape_xml_cdata(ai_response)

                # Get timestamp for context
                timestamp = turn.get("timestamp", "")
                timestamp_attr = f' timestamp="{timestamp}"' if timestamp else ""

                xml_turns.append(f"""    <turn{timestamp_attr}>
            <user><![CDATA[{user_input}]]></user>
            <assistant><![CDATA[{ai_response}]]></assistant>
        </turn>""")
        
        return "\n".join(xml_turns)

    def build_xml_prompt(self, conversation_history: List[Dict], message: str, include_history: bool = True) -> str:
        """Constrói o prompt final usando uma estrutura XML otimizada."""
        if not self.persona_content or not self.agent_config:
            raise ValueError("Contexto não foi carregado. Chame load_context() primeiro.")

        # Carrega e escapa os conteúdos
        persona_cdata = self._escape_xml_cdata(self.persona_content)

        # Get instructions with fallbacks
        agent_instructions = (
            self.agent_config.get("prompt", "") or
            self.agent_config.get("instructions", "") or
            self.agent_config.get("description", "") or
            ""
        )
        instructions_cdata = self._escape_xml_cdata(agent_instructions)
        playbook_cdata = self._escape_xml_cdata(self.playbook_content)
        message_cdata = self._escape_xml_cdata(message)
        
        # Carrega e escapa o conteúdo do screenplay
        screenplay_cdata = ""
        if hasattr(self, 'screenplay_content') and self.screenplay_content:
            screenplay_cdata = self._escape_xml_cdata(self.screenplay_content)
        
        # Formata o histórico
        history_xml = self._format_history_xml(conversation_history) if include_history else "<history/>"

        # Monta a seção do screenplay se disponível
        screenplay_section = ""
        if screenplay_cdata:
            screenplay_section = f"""        <screenplay>
            <![CDATA[{screenplay_cdata}]]>
        </screenplay>"""

        # Monta o prompt XML final
        final_prompt = f"""<prompt>
    <system_context>
        <persona>
            <![CDATA[{persona_cdata}]]>
        </persona>
        <instructions>
            <![CDATA[{instructions_cdata}]]>
        </instructions>
        <playbook>
            <![CDATA[{playbook_cdata}]]>
        </playbook>{screenplay_section}
    </system_context>
    <conversation_history>
{history_xml}
    </conversation_history>
    <user_request>
        <![CDATA[{message_cdata}]]>
    </user_request>
</prompt>"""
        
        logger.info(f"Prompt XML final construído com sucesso ({len(final_prompt)} chars).")

        # Save prompt to disk for debugging/analysis
        self._save_prompt_to_disk(final_prompt, "xml", format_xml=True)

        return final_prompt

    def _save_prompt_to_disk(self, prompt_content: str, format_type: str, format_xml: bool = False) -> None:
        """
        Salva o prompt completo em disco para análise/debugging.

        Args:
            prompt_content: Conteúdo do prompt a ser salvo
            format_type: Tipo do formato ("text" ou "xml")
            format_xml: Se True, formata XML para melhor legibilidade
        """
        try:
            # Create prompts_log directory if it doesn't exist
            prompts_dir = Path("prompts_log")
            prompts_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp and agent info
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds precision
            agent_name = self.agent_config.get("name") or self.agent_config.get("id", "unknown")

            # Clean agent name for filename
            safe_agent_name = re.sub(r'[^\w\-_]', '_', agent_name)

            filename = f"{timestamp}_{safe_agent_name}_{format_type}.txt"
            filepath = prompts_dir / filename

            # Format XML if requested
            content_to_save = prompt_content
            if format_xml and format_type == "xml":
                try:
                    # Parse and format XML with proper indentation
                    dom = xml.dom.minidom.parseString(prompt_content)
                    content_to_save = dom.toprettyxml(indent="  ", encoding=None)
                    # Remove extra newlines that toprettyxml adds
                    content_to_save = '\n'.join([line for line in content_to_save.split('\n') if line.strip()])
                except Exception as xml_error:
                    logger.warning(f"Failed to format XML, saving as-is: {xml_error}")
                    content_to_save = prompt_content

            # Save prompt with metadata header
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# PROMPT LOG - {datetime.now().isoformat()}\n")
                f.write(f"# Agent: {agent_name}\n")
                f.write(f"# Format: {format_type}\n")
                f.write(f"# Formatted: {format_xml and format_type == 'xml'}\n")
                f.write(f"# Length: {len(prompt_content)} chars\n")
                f.write(f"# MongoDB: {self.is_mongodb}\n")
                f.write("# " + "="*70 + "\n\n")
                f.write(content_to_save)

            logger.debug(f"Prompt saved to: {filepath}")

        except Exception as e:
            # Don't let prompt saving errors break the main flow
            # Silently ignore permission errors in production
            logger.debug(f"Failed to save prompt to disk: {e}")
