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

    def __init__(self, agent_home_path: str, prompt_format: str = "xml", instance_id: Optional[str] = None, screenplay_id: Optional[str] = None):
        """
        Inicializa o PromptEngine com o caminho para o diretório principal do agente.

        Args:
            agent_home_path: Caminho para o diretório do agente
            prompt_format: Formato do prompt ("xml" ou "text")
            instance_id: ID da instância do agente (para contexto isolado)
            screenplay_id: ID do screenplay (opcional, se não fornecido busca pela instance)
        """
        self.agent_home_path = Path(agent_home_path)
        self.agent_config: Dict[str, Any] = {}
        self.persona_content: str = ""
        self.playbook: Dict[str, Any] = {}
        self.playbook_content: str = ""
        self.prompt_format = prompt_format  # "xml" or "text"
        self.is_mongodb = str(agent_home_path).startswith("mongodb://")
        self.instance_id = instance_id
        self.screenplay_id = screenplay_id  # Store screenplay_id directly
        self.screenplay_content: str = ""
        self.conversation_context: str = ""
        self.conversation_delegation: Dict[str, Any] = {}  # auto_delegate settings + squad
        self.task_state_context: list = []  # World state from task observations

        # Extract agent_id from MongoDB path
        if self.is_mongodb:
            # mongodb://agents/{agent_id} -> {agent_id}
            self.agent_id = str(agent_home_path).split("/")[-1]
        else:
            self.agent_id = None
        self.conversation_history_cache = []  # Cache do histórico de conversas

        logger.debug(f"PromptEngine inicializado para o caminho: {agent_home_path} (MongoDB: {self.is_mongodb}, Format: {self.prompt_format})")

    def load_context(self, conversation_id: Optional[str] = None) -> None:
        """
        Carrega e processa todos os artefatos de contexto do agente.
        Esta é a principal função de inicialização.

        Args:
            conversation_id: ID da conversa para carregar contexto específico e histórico de mensagens
        """
        self._load_agent_config()
        self._validate_agent_config()
        self._load_agent_persona()
        self._load_agent_playbook()
        self._resolve_persona_placeholders()
        self._load_screenplay_context()
        self._load_conversation_context(conversation_id)
        self._load_conversation_history(conversation_id)  # ← NOVO: Carregar histórico de mensagens
        self._load_task_state_context()  # ← NOVO: Carregar estado de tasks observadas

    def build_prompt(self, conversation_history: List[Dict], message: str, include_history: bool = True) -> str:
        """Constrói o prompt final usando o contexto já carregado."""
        if not self.persona_content or not self.agent_config:
            raise ValueError(
                "Contexto não foi carregado. Chame load_context() primeiro."
            )

        # Se conversation_history estiver vazio mas temos cache, usar o cache
        if not conversation_history and self.conversation_history_cache:
            conversation_history = self.conversation_history_cache
            logger.debug(f"Usando histórico do cache: {len(conversation_history)} mensagens")

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

        # Delegation section for text format
        delegation_text = ""
        if self.conversation_delegation.get("auto_delegate"):
            delegation_text = self._build_delegation_text()

        final_prompt = f"""
{persona_content}

### INSTRUÇÕES DO AGENTE
{agent_instructions}
{playbook_section}{delegation_text}
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
        """Carrega o contexto do screenplay associado à instância atual ou pelo ID direto."""
        self.screenplay_content = ""

        # Determinar screenplay_id
        screenplay_id = self.screenplay_id  # Primeiro tenta usar o ID direto

        if not screenplay_id and self.instance_id:
            # Se não tem screenplay_id direto, busca pela instance
            try:
                import os
                from pymongo import MongoClient

                mongo_uri = os.getenv("MONGO_URI")
                if not mongo_uri:
                    logger.debug("MONGO_URI não configurada, pulando carregamento do screenplay")
                    return

                client = MongoClient(mongo_uri)
                db = client.conductor_state

                instance_doc = db.agent_instances.find_one({"instance_id": self.instance_id})
                if instance_doc and "screenplay_id" in instance_doc:
                    screenplay_id = instance_doc["screenplay_id"]
                else:
                    logger.debug(f"Nenhum screenplay_id associado à instância {self.instance_id}")
                    return
            except Exception as e:
                logger.warning(f"Falha ao buscar screenplay_id pela instância: {e}")
                return

        if not screenplay_id:
            logger.debug("Nenhum screenplay_id disponível para carregar contexto")
            return

        # Carregar screenplay do MongoDB
        try:
            import os
            from pymongo import MongoClient
            from bson.objectid import ObjectId

            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                logger.debug("MONGO_URI não configurada")
                return

            client = MongoClient(mongo_uri)
            db = client.conductor_state

            screenplay_doc = db.screenplays.find_one({
                "_id": ObjectId(screenplay_id),
                "isDeleted": {"$ne": True}
            })

            if screenplay_doc and "content" in screenplay_doc:
                self.screenplay_content = screenplay_doc["content"]
                logger.info(f"✅ Contexto do screenplay '{screenplay_id}' carregado ({len(self.screenplay_content)} chars).")
            else:
                logger.debug(f"Screenplay '{screenplay_id}' não encontrado ou sem conteúdo")

        except Exception as e:
            logger.warning(f"Falha ao carregar contexto do screenplay: {e}")

    def _load_conversation_context(self, conversation_id: Optional[str] = None) -> None:
        """Carrega o contexto da conversa atual (bug, feature, problema específico)."""
        self.conversation_context = ""
        if not conversation_id:
            # Tentar carregar do instance_id se disponível
            if not self.instance_id:
                return

            try:
                import os
                from pymongo import MongoClient

                mongo_uri = os.getenv("MONGO_URI")
                if not mongo_uri:
                    logger.debug("MONGO_URI não configurada, pulando carregamento do contexto da conversa")
                    return

                client = MongoClient(mongo_uri)
                db = client.conductor_state

                # Buscar conversation_id pela instance
                instance_doc = db.agent_instances.find_one({"instance_id": self.instance_id})
                if not instance_doc or "conversation_id" not in instance_doc:
                    logger.debug(f"Nenhum conversation_id associado à instância {self.instance_id}")
                    return

                conversation_id = instance_doc["conversation_id"]
            except Exception as e:
                logger.warning(f"Falha ao buscar conversation_id pela instância: {e}")
                return

        if not conversation_id:
            return

        try:
            import os
            from pymongo import MongoClient

            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                return

            client = MongoClient(mongo_uri)
            db = client.conductor_state

            # Buscar contexto da conversa
            conversation_doc = db.conversations.find_one({"conversation_id": conversation_id})
            if conversation_doc and "context" in conversation_doc and conversation_doc["context"]:
                self.conversation_context = conversation_doc["context"]
                logger.info(f"Contexto da conversa '{conversation_id}' carregado ({len(self.conversation_context)} chars).")
            else:
                logger.debug(f"Conversa '{conversation_id}' não possui contexto definido")

            # Load delegation settings if auto_delegate is enabled
            if conversation_doc and conversation_doc.get("auto_delegate"):
                squad_agents = self._load_squad_agents(db, conversation_id)
                self.conversation_delegation = {
                    "auto_delegate": True,
                    "max_chain_depth": conversation_doc.get("max_chain_depth"),
                    "squad": squad_agents,
                }
                logger.info(
                    f"Delegation enabled for '{conversation_id}': "
                    f"{len(squad_agents)} agents in squad"
                )

        except Exception as e:
            logger.warning(f"Falha ao carregar contexto da conversa: {e}")

    def _load_squad_agents(self, db, conversation_id: str) -> list:
        """Load agent info for all agents instantiated in this conversation."""
        try:
            agent_ids = db.agent_instances.distinct(
                "agent_id", {"conversation_id": conversation_id}
            )
            if not agent_ids:
                return []

            agents = list(db.agents.find(
                {"agent_id": {"$in": agent_ids}},
                {"agent_id": 1, "definition.name": 1, "definition.description": 1,
                 "definition.emoji": 1, "group": 1, "_id": 0},
            ))
            result = []
            for a in agents:
                defn = a.get("definition", {})
                result.append({
                    "agent_id": a["agent_id"],
                    "name": defn.get("name", a["agent_id"]),
                    "description": defn.get("description", ""),
                    "emoji": defn.get("emoji", ""),
                    "squad": a.get("group", ""),
                })
            return result
        except Exception as e:
            logger.warning(f"Failed to load squad agents: {e}")
            return []

    def _build_delegation_xml(self) -> str:
        """Build <delegation> XML section with squad info and delegation instructions."""
        squad = self.conversation_delegation.get("squad", [])
        max_depth = self.conversation_delegation.get("max_chain_depth")

        # Filter out self from the squad list
        other_agents = [a for a in squad if a["agent_id"] != self.agent_id]
        if not other_agents:
            return ""

        agents_xml = ""
        for a in other_agents:
            agents_xml += (
                f'            <agent id="{a["agent_id"]}" '
                f'name="{a["name"]}" '
                f'squad="{a["squad"]}">'
                f'{a["description"]}'
                f'</agent>\n'
            )

        depth_note = ""
        if max_depth:
            depth_note = f"\n            Chain depth limit: {max_depth} cycles."

        return f"""
        <delegation>
            <mode>auto_delegate</mode>
            <available_agents>
{agents_xml}            </available_agents>
            <instructions>
                You are part of an agent SQUAD. The user's instruction is
                addressed to the TEAM, not to you specifically.

                STEP 1 — DECOMPOSE: Break the user's request into a numbered
                list of distinct sub-tasks. Each sub-task should map to a
                single specialist. Output this list in your response so the
                user can see the pipeline.

                STEP 2 — TRIAGE: For EACH sub-task, identify which agent
                (including yourself) is the best fit based on the
                available_agents descriptions. If the FIRST sub-task belongs
                to another agent, delegate IMMEDIATELY without doing any work.
                If it belongs to you, proceed to STEP 3.

                STEP 3 — EXECUTE: Perform ONLY the first sub-task that matches
                your expertise. Do NOT proceed to subsequent sub-tasks that
                belong to other agents. Stop after completing your part.

                STEP 4 — HANDOFF: Delegate the NEXT sub-task to the
                appropriate agent. In the 'input' field, include:
                (a) the result of your completed work,
                (b) the remaining pipeline of sub-tasks so the next agent
                    can continue the chain.

                When the user explicitly mentions another agent or specialist
                (e.g. "use the critic", "ask DevOps"), you MUST delegate.

                To delegate, end your response with:

                [DELEGATE]
                target_agent_id: AgentId_Here
                input: Clear instructions for the next agent
                [/DELEGATE]

                Rules:
                - ALWAYS decompose multi-part requests before acting.
                - Execute ONLY your sub-task, then hand off. Never do another agent's job.
                - Delegate when another agent's description matches the sub-task better.
                - Never delegate back to yourself.
                - Provide enough context in 'input' for the next agent to work autonomously.
                - Include the remaining pipeline so the chain continues to completion.
                - If no agent fits a sub-task, do it yourself or ask the human.{depth_note}
            </instructions>
        </delegation>"""

    def _build_delegation_text(self) -> str:
        """Build delegation section for text-format prompts."""
        squad = self.conversation_delegation.get("squad", [])
        other_agents = [a for a in squad if a["agent_id"] != self.agent_id]
        if not other_agents:
            return ""

        agents_list = "\n".join(
            f"  - {a['agent_id']} ({a['name']}): {a['description']}"
            for a in other_agents
        )
        max_depth = self.conversation_delegation.get("max_chain_depth")
        depth_note = f"\n  Chain depth limit: {max_depth} cycles." if max_depth else ""

        return f"""
### DELEGATION (auto_delegate=ON)
You are part of an agent SQUAD. The user's instruction is addressed to
the TEAM, not to you specifically.
{agents_list}

STEP 1 — DECOMPOSE: Break the user's request into a numbered list of
distinct sub-tasks. Each sub-task should map to a single specialist.
Output this list so the user can see the pipeline.

STEP 2 — TRIAGE: For EACH sub-task, identify which agent (including
yourself) is the best fit. If the FIRST sub-task belongs to another
agent, delegate IMMEDIATELY. If it belongs to you, proceed.

STEP 3 — EXECUTE: Perform ONLY the first sub-task that matches your
expertise. Do NOT proceed to subsequent sub-tasks that belong to other
agents. Stop after completing your part.

STEP 4 — HANDOFF: Delegate the NEXT sub-task to the appropriate agent.
In 'input', include: (a) the result of your work, (b) the remaining
pipeline of sub-tasks so the next agent can continue the chain.

When the user mentions a specialist, you MUST delegate.

To delegate, end your response with:

[DELEGATE]
target_agent_id: AgentId_Here
input: Clear instructions for the next agent
[/DELEGATE]

Rules:
- ALWAYS decompose multi-part requests before acting.
- Execute ONLY your sub-task, then hand off. Never do another agent's job.
- Delegate when another agent's description matches the sub-task better.
- Never delegate back to yourself.
- Provide enough context for the next agent to work autonomously.
- Include the remaining pipeline so the chain continues to completion.
- If no agent fits a sub-task, do it yourself or ask the human.{depth_note}
"""

    def _load_conversation_history(self, conversation_id: Optional[str] = None) -> None:
        """
        Carrega o histórico completo de mensagens da conversa do MongoDB.
        Este histórico é usado no build_prompt() para incluir todas as mensagens anteriores.

        Args:
            conversation_id: ID da conversa para buscar mensagens
        """
        self.conversation_history_cache = []

        if not conversation_id:
            logger.debug("Nenhum conversation_id fornecido, histórico vazio")
            return

        try:
            import os
            from pymongo import MongoClient

            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                logger.debug("MONGO_URI não configurada, não é possível carregar histórico")
                return

            client = MongoClient(mongo_uri)
            db = client.conductor_state

            # Buscar conversa
            conversation_doc = db.conversations.find_one({"conversation_id": conversation_id})
            if not conversation_doc:
                logger.debug(f"Conversa '{conversation_id}' não encontrada")
                return

            # Carregar mensagens da conversa
            messages = conversation_doc.get("messages", [])

            # Filtrar mensagens não deletadas e não ocultas
            active_messages = [msg for msg in messages
                               if not msg.get("isDeleted", False)
                               and not msg.get("isHidden", False)
                               and msg.get("status") != "pending"]

            # Converter formato das mensagens para o esperado pelo _format_history()
            # Formato esperado: [{"role": "user", "content": "...", "timestamp": ...}, {"role": "assistant", "content": "..."}]
            self.conversation_history_cache = active_messages

            logger.info(f"✅ Histórico de conversa '{conversation_id}' carregado: {len(active_messages)} mensagens")
            if active_messages:
                logger.debug(f"   - Primeira mensagem: {active_messages[0].get('role', 'unknown')} - {active_messages[0].get('content', '')[:50]}...")
                logger.debug(f"   - Última mensagem: {active_messages[-1].get('role', 'unknown')} - {active_messages[-1].get('content', '')[:50]}...")

        except Exception as e:
            logger.warning(f"Falha ao carregar histórico da conversa: {e}")
            self.conversation_history_cache = []

    def _load_task_state_context(self) -> None:
        """
        Carrega estado de tasks observadas pelo agente via API de observações.
        O estado é injetado no prompt como <world_state> XML.
        """
        self.task_state_context = []

        # Precisa de agent_id para consultar observações
        agent_id = self.agent_config.get('id') or self.agent_config.get('name') or self.agent_id
        if not agent_id:
            logger.debug("Nenhum agent_id disponível para carregar task state context")
            return

        try:
            import os
            import httpx

            # URL da API de observações (Conductor API)
            conductor_api_url = os.getenv("CONDUCTOR_API_URL", "http://conductor-api:8000")
            timeout = float(os.getenv("OBSERVATION_TIMEOUT_SECONDS", "10"))

            # Consultar estado consolidado via API síncrona
            with httpx.Client(timeout=timeout) as client:
                response = client.get(f"{conductor_api_url}/observations/{agent_id}/state")

                if response.status_code == 200:
                    state = response.json()
                    self.task_state_context = state.get('capabilities', [])

                    if self.task_state_context:
                        logger.info(f"✅ Task state context carregado para '{agent_id}': {len(self.task_state_context)} capabilities")
                    else:
                        logger.debug(f"Nenhuma observação encontrada para agente '{agent_id}'")
                elif response.status_code == 404:
                    # Agente não tem observações - comportamento normal
                    logger.debug(f"Agente '{agent_id}' não possui observações registradas")
                else:
                    logger.warning(f"Falha ao carregar task state: HTTP {response.status_code}")

        except httpx.TimeoutException:
            logger.warning(f"Timeout ao consultar observações para agente '{agent_id}'")
        except httpx.RequestError as e:
            logger.warning(f"Erro de conexão ao consultar observações: {e}")
        except Exception as e:
            logger.warning(f"Falha ao carregar task state context: {e}")

    def _build_world_state_xml(self) -> str:
        """
        Constrói a representação XML do world_state para injeção no prompt.

        Returns:
            String XML do world_state ou string vazia se não houver dados
        """
        if not self.task_state_context:
            return ""

        capabilities_xml = []
        for cap in self.task_state_context:
            # Construir XML de subtasks se existirem
            subtasks_xml = ""
            if cap.get('subtasks'):
                subtask_items = []
                for st in cap['subtasks']:
                    subtask_items.append(
                        f'                <subtask id="{st.get("id", 0)}" status="{st.get("status", "unknown")}">'
                        f'{self._escape_xml_cdata(st.get("name", ""))} ({st.get("progress", 0)}%)</subtask>'
                    )
                subtasks_xml = f'\n            <subtasks>\n' + '\n'.join(subtask_items) + '\n            </subtasks>'

            # Extrair dados da source
            source = cap.get('source', {})
            source_xml = (
                f'            <source project_id="{source.get("project_id", 0)}" task_id="{source.get("task_id", 0)}">\n'
                f'                {self._escape_xml_cdata(source.get("task_name", ""))}\n'
                f'            </source>'
            )

            # Montar capability completa
            cap_xml = f'''        <capability name="{cap.get('name', 'unknown')}" progress="{cap.get('progress', 0)}%" status="{cap.get('status', 'unknown')}">
            <description>{self._escape_xml_cdata(cap.get('description', ''))}</description>
{source_xml}{subtasks_xml}
            <summary><![CDATA[{self._escape_xml_cdata(cap.get('summary', ''))}]]></summary>
        </capability>'''
            capabilities_xml.append(cap_xml)

        timestamp = datetime.utcnow().isoformat() + "Z"

        # Seção de referência de tools para que o agente saiba como consultar mais detalhes
        # Obter URL da Construction API do environment
        import os
        construction_api_url = os.getenv("CONSTRUCTION_API_URL", "http://verticals-construction-api-projects:8001")

        tools_reference = f'''        <tools_reference>
            <documentation>docs/features/WORLD_STATE_OBSERVATIONS.md</documentation>
            <construction_api base_url="{construction_api_url}" container="verticals-construction-api-projects">
                <description>API de gerenciamento de projetos e tasks (TODO list)</description>
                <endpoint method="GET" path="/api/v1/tasks/{{task_id}}" description="Detalhes completos de uma task (nome, descrição, status, datas, responsável, prioridade)" />
                <endpoint method="GET" path="/api/v1/tasks/{{task_id}}/subtasks" description="Lista subtasks diretas de uma task" />
                <endpoint method="GET" path="/api/v1/projects/{{project_id}}/tasks" description="Lista todas as tasks de um projeto" />
                <example>curl {construction_api_url}/api/v1/tasks/42</example>
            </construction_api>
            <mcp_tools>
                <tool name="get_agent_world_state" description="Retorna estado consolidado de todas as capabilities observadas" />
                <tool name="subscribe_agent_to_task" description="Inscreve o agente para observar uma nova task" />
                <tool name="unsubscribe_agent_from_task" description="Remove inscrição de uma task" />
                <tool name="list_agent_observations" description="Lista todas as tasks que o agente observa" />
            </mcp_tools>
            <usage_hint>Para detalhes de uma task, faça GET {construction_api_url}/api/v1/tasks/{{task_id}}</usage_hint>
        </tools_reference>'''

        return f'''        <world_state timestamp="{timestamp}">
{tools_reference}
{chr(10).join(capabilities_xml)}
        </world_state>'''

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

        # FILTER: Remove mensagens deletadas (soft delete) e ocultas (permanent hide)
        # Retrocompatibilidade: mensagens sem os campos isDeleted/isHidden são tratadas como ativas
        active_history = [turn for turn in history
                         if not turn.get("isDeleted", False)
                         and not turn.get("isHidden", False)
                         and turn.get("status") != "pending"]

        # 🔥 NOVO: Remover a última mensagem se for um "user" sem resposta do assistant
        # Isso acontece quando o input do usuário já foi inserido no history, mas o resultado ainda não foi processado
        if active_history:
            last_turn = active_history[-1]

            # Verificar se é uma mensagem de usuário (role-based ou legacy format)
            is_user_message = (
                last_turn.get("role") == "user" or
                last_turn.get("type") == "user" or
                bool(last_turn.get("user_input") or last_turn.get("prompt") or last_turn.get("user"))
            )

            # Verificar se a resposta do assistant está vazia
            has_empty_response = not bool(
                last_turn.get("ai_response") or
                last_turn.get("response") or
                last_turn.get("assistant") or
                last_turn.get("output") or
                last_turn.get("summary")
            )

            if is_user_message and has_empty_response:
                logger.info(f"🔍 [HISTORY] Removendo última mensagem do usuário sem resposta do assistant")
                active_history = active_history[:-1]

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
                turn.get("content", "") if turn.get("role") == "user" or turn.get("type") == "user" else ""
            )

            # Get AI response with fallbacks
            ai_response = (
                turn.get("ai_response", "") or
                turn.get("response", "") or
                turn.get("assistant", "") or
                turn.get("output", "") or
                turn.get("summary", "") or  # ← Fallback para summary
                turn.get("content", "") if turn.get("role") in ["assistant", "ai", "bot"] or turn.get("type") in ["assistant", "ai", "bot"] else ""
            )

            # 🔥 NOVO: Não incluir turns com assistant vazio no histórico (formato texto)
            # Isso acontece quando o input do usuário foi inserido mas a resposta ainda não foi processada
            if not ai_response:
                logger.debug(f"🔍 [HISTORY_TEXT] Pulando turn sem resposta do assistant")
                continue

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

        # FILTER: Remove mensagens deletadas (soft delete) e ocultas (permanent hide)
        # Retrocompatibilidade: mensagens sem os campos isDeleted/isHidden são tratadas como ativas
        active_history = [turn for turn in history
                         if not turn.get("isDeleted", False)
                         and not turn.get("isHidden", False)
                         and turn.get("status") != "pending"]

        # 🔥 NOVO: Remover a última mensagem se for um "user" sem resposta do assistant
        # Isso acontece quando o input do usuário já foi inserido no history, mas o resultado ainda não foi processado
        if active_history:
            last_turn = active_history[-1]

            # Verificar se é uma mensagem de usuário (role-based ou legacy format)
            is_user_message = (
                last_turn.get("role") == "user" or
                last_turn.get("type") == "user" or
                bool(last_turn.get("user_input") or last_turn.get("prompt") or last_turn.get("user"))
            )

            # Verificar se a resposta do assistant está vazia
            has_empty_response = not bool(
                last_turn.get("content") if last_turn.get("role") or last_turn.get("type") else
                last_turn.get("ai_response") or
                last_turn.get("response") or
                last_turn.get("assistant") or
                last_turn.get("output") or
                last_turn.get("summary")
            )

            if is_user_message and has_empty_response:
                logger.info(f"🔍 [HISTORY_XML] Removendo última mensagem do usuário sem resposta do assistant")
                active_history = active_history[:-1]

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
        # Suporte para "role" OU "type" (conversas usam "type", tasks usam "role")
        if recent_history and (recent_history[0].get("role") or recent_history[0].get("type")):
            # ConversationService format: process in pairs
            i = 0
            while i < len(recent_history):
                turn = recent_history[i]

                # Suporte para "role" ou "type"
                msg_role = turn.get("role") or turn.get("type")

                # DEBUG: Log history structure
                logger.debug(f"History turn {i}: keys={list(turn.keys())}, role/type={msg_role}")

                if msg_role == "user":
                    user_input = turn.get("content", "")
                    ai_response = ""

                    # Look for corresponding assistant response
                    if i + 1 < len(recent_history):
                        next_role = recent_history[i + 1].get("role") or recent_history[i + 1].get("type")
                        if next_role in ["assistant", "ai", "bot"]:
                            ai_response = recent_history[i + 1].get("content", "")
                            i += 2  # Skip both user and assistant
                        else:
                            i += 1  # Only skip user
                    else:
                        i += 1  # Only skip user

                    # 🔥 NOVO: Não incluir turns com assistant vazio no histórico
                    # Isso acontece quando o input do usuário foi inserido mas a resposta ainda não foi processada
                    if not ai_response:
                        logger.debug(f"🔍 [HISTORY_XML] Pulando turn sem resposta do assistant")
                        continue

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

                # 🔥 NOVO: Não incluir turns com assistant vazio no histórico (formato legacy)
                # Isso acontece quando o input do usuário foi inserido mas a resposta ainda não foi processada
                if not ai_response:
                    logger.debug(f"🔍 [HISTORY_XML_LEGACY] Pulando turn sem resposta do assistant")
                    continue

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

        # DEBUG: Log estado do histórico
        logger.info(f"🔍 [BUILD_XML] conversation_history recebido: {len(conversation_history) if conversation_history else 0} mensagens")
        logger.info(f"🔍 [BUILD_XML] conversation_history_cache: {len(self.conversation_history_cache) if self.conversation_history_cache else 0} mensagens")
        logger.info(f"🔍 [BUILD_XML] include_history: {include_history}")

        # Se conversation_history estiver vazio mas temos cache, usar o cache
        if not conversation_history and self.conversation_history_cache:
            conversation_history = self.conversation_history_cache
            logger.info(f"✅ [BUILD_XML] Usando histórico do cache para XML: {len(conversation_history)} mensagens")

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

        # Monta a seção do contexto da conversa se disponível
        conversation_context_section = ""
        if hasattr(self, 'conversation_context') and self.conversation_context:
            conversation_context_cdata = self._escape_xml_cdata(self.conversation_context)
            conversation_context_section = f"""        <conversation_context>
            <![CDATA[{conversation_context_cdata}]]>
        </conversation_context>"""

        # Monta a seção do world_state se disponível (estado de tasks observadas)
        world_state_section = ""
        if hasattr(self, 'task_state_context') and self.task_state_context:
            world_state_section = "\n" + self._build_world_state_xml()

        # Delegation section: when auto_delegate is enabled, inject squad awareness
        delegation_section = ""
        if self.conversation_delegation.get("auto_delegate"):
            delegation_section = self._build_delegation_xml()

        # SAGA-016: Inject live MCP mesh topology for Council agents
        mesh_section = ""
        try:
            from src.core.services.mcp_mesh_service import mesh_service
            mesh_data = mesh_service.get_mesh()
            if mesh_data.get("summary", {}).get("total", 0) > 0:
                mesh_context = mesh_service.get_mesh_context_for_prompt()
                mesh_section = f"\n        {mesh_context}"
        except Exception:
            pass  # Mesh not available yet - graceful degradation

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
        </playbook>{screenplay_section}{conversation_context_section}{delegation_section}{world_state_section}{mesh_section}
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
