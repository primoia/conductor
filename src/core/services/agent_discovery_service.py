# src/core/services/agent_discovery_service.py
import time
from typing import List, Optional
from src.core.services.storage_service import StorageService
from src.core.domain import AgentDefinition


class AgentDiscoveryService:
    """Responsável por descobrir e listar agentes."""

    def __init__(self, storage_service: StorageService):
        self._storage = storage_service.get_repository()
        # Cache simples para descoberta de agentes (5 minutos)
        self._cache = {}
        self._cache_timeout = 300  # 5 minutos em segundos

    def discover_agents(self) -> List[AgentDefinition]:
        """Descobre e retorna todas as definições de agentes disponíveis."""
        # Verificar cache
        current_time = time.time()
        cache_key = "all_agents"
        
        if (cache_key in self._cache and 
            current_time - self._cache[cache_key]['timestamp'] < self._cache_timeout):
            return self._cache[cache_key]['data']
        
        # Cache miss ou expirado - buscar dados
        agent_ids = self._storage.list_agents()
        definitions = []
        
        for agent_id in agent_ids:
            definition = self.get_agent_definition(agent_id)
            if definition:
                definitions.append(definition)
        
        # Atualizar cache
        self._cache[cache_key] = {
            'data': definitions,
            'timestamp': current_time
        }
        
        return definitions

    def clear_cache(self):
        """Limpa o cache de descoberta de agentes."""
        self._cache.clear()

    def get_agent_definition(self, agent_id: str) -> Optional[AgentDefinition]:
        """Carrega a definição de um agente específico."""
        # Verificar cache individual
        current_time = time.time()
        cache_key = f"agent_{agent_id}"
        
        if (cache_key in self._cache and 
            current_time - self._cache[cache_key]['timestamp'] < self._cache_timeout):
            return self._cache[cache_key]['data']
        
        # Cache miss - buscar dados
        definition_data = self._storage.load_definition(agent_id)
        
        if not definition_data:
            return None
        
        # Filter only valid fields for AgentDefinition
        from src.core.constants import AgentFields, Defaults
        
        filtered_data = {k: v for k, v in definition_data.items() if k in AgentFields.VALID_FIELDS}
        
        # Ensure required fields have defaults
        filtered_data.setdefault('name', agent_id)
        filtered_data.setdefault('version', Defaults.AGENT_VERSION)
        filtered_data.setdefault('schema_version', Defaults.SCHEMA_VERSION)
        filtered_data.setdefault('description', f'Agent {agent_id}')
        filtered_data.setdefault('author', Defaults.AGENT_AUTHOR)
        filtered_data.setdefault('tags', [])
        filtered_data.setdefault('capabilities', [])
        filtered_data.setdefault('allowed_tools', [])
        
        # Create agent definition
        agent_definition = AgentDefinition(**filtered_data, agent_id=agent_id)
        
        # Atualizar cache
        self._cache[cache_key] = {
            'data': agent_definition,
            'timestamp': current_time
        }
        
        return agent_definition

    def get_conversation_history(self, agent_id: str) -> List[dict]:
        """Carrega o histórico de conversas de um agente."""
        return self._storage.load_history(agent_id)

    def clear_conversation_history(self, agent_id: str) -> bool:
        """Limpa o histórico de conversas de um agente."""
        try:
            # Use repository method to clear history (works for both filesystem and MongoDB)
            success = self._storage.clear_history(agent_id)

            # Optionally clear session conversation data if present
            try:
                session_data = self._storage.load_session(agent_id)
                # Remove any conversation-related fields from session
                conversation_fields = ["conversation_history", "last_messages", "chat_history"]
                for field in conversation_fields:
                    if field in session_data:
                        del session_data[field]
                self._storage.save_session(agent_id, session_data)
            except Exception:
                # Don't fail completely if session clearing fails
                pass

            return success
        except Exception:
            return False

    def agent_exists(self, agent_id: str) -> bool:
        """Verifica se um agente existe no sistema."""
        try:
            agents = self.discover_agents()
            return any(agent.agent_id == agent_id for agent in agents)
        except Exception:
            return False

    def get_similar_agent_names(self, agent_id: str, max_suggestions: int = 3) -> List[str]:
        """Retorna sugestões de agentes similares baseado no nome fornecido."""
        try:
            agents = self.discover_agents()
            agent_names = [agent.agent_id for agent in agents]
            
            # Simple similarity based on common substrings and case-insensitive matching
            suggestions = []
            agent_id_lower = agent_id.lower()
            
            # First, look for exact case-insensitive matches
            for name in agent_names:
                if name.lower() == agent_id_lower:
                    suggestions.append(name)
            
            # Then, look for partial matches
            if len(suggestions) < max_suggestions:
                for name in agent_names:
                    if (agent_id_lower in name.lower() or name.lower() in agent_id_lower) and name not in suggestions:
                        suggestions.append(name)
                        if len(suggestions) >= max_suggestions:
                            break
            
            # Finally, look for similar patterns (same length, similar characters)
            if len(suggestions) < max_suggestions:
                for name in agent_names:
                    if name not in suggestions and len(name) == len(agent_id):
                        # Count matching characters in same positions
                        matches = sum(1 for a, b in zip(agent_id_lower, name.lower()) if a == b)
                        if matches >= len(agent_id) * 0.6:  # 60% similarity
                            suggestions.append(name)
                            if len(suggestions) >= max_suggestions:
                                break
            
            return suggestions[:max_suggestions]
        except Exception:
            return []

    def build_meta_agent_context(self, message: str, meta: bool = False, new_agent_id: str = None) -> str:
        """Constrói contexto enhanced para meta-agents."""
        context_parts = []

        # Add new agent ID if specified
        if new_agent_id:
            context_parts.append(f"NEW_AGENT_ID={new_agent_id}")

        # Add meta flag context only if meta is explicitly True or new_agent_id is provided
        if meta or new_agent_id:
            if meta:
                context_parts.append("AGENT_TYPE=meta")
            else:
                context_parts.append("AGENT_TYPE=project")

        # Build final message
        if context_parts:
            context_header = "\n".join(context_parts)
            enhanced_message = f"{context_header}\n\n{message}"
            return enhanced_message
        else:
            return message

    def get_agent_output_scope(self, agent_id: str) -> List[str]:
        """Obtém o escopo de output de um agente."""
        try:
            agent_definition = self.get_agent_definition(agent_id)
            if agent_definition and hasattr(agent_definition, 'capabilities'):
                # Look for output scope in capabilities
                for capability in agent_definition.capabilities:
                    if isinstance(capability, dict) and 'output_scope' in capability:
                        return capability['output_scope']
            return []  # No restrictions by default
        except Exception:
            return []

    def save_agent_state(self, agent_id: str) -> bool:
        """Salva o estado de um agente."""
        try:
            # This could be expanded to save additional state information
            # For now, we'll just ensure the agent directory exists
            agent_home_path = self._storage.get_agent_home_path(agent_id)
            import os
            os.makedirs(agent_home_path, exist_ok=True)
            return True
        except Exception:
            return False

    def list_all_agent_definitions(self) -> List['AgentDefinition']:
        """Lista todas as definições de agente (compatibilidade com AgentService legado)."""
        return self.discover_agents()

    def get_full_prompt(self, agent_id: str, sample_message: str = "Mensagem de exemplo", meta: bool = False, new_agent_id: str = None, current_message: str = None, include_history: bool = True, save_to_file: bool = False) -> str:
        """
        Gera o prompt completo que será usado pelo LLM, combinando:
        - Persona do agente
        - Instruções específicas
        - Histórico da conversa
        - Mensagem atual do usuário (incluindo a última mensagem do REPL se fornecida)
        
        Esta é a função unificada usada tanto para exibir o prompt quanto para enviá-lo ao LLM.
        
        Args:
            agent_id: ID do agente
            sample_message: Mensagem de amostra (default "Mensagem de exemplo")
            meta: Flag indicando se é meta agent
            new_agent_id: ID do novo agente (para meta agents)
            current_message: Mensagem atual do REPL (sobrescreve sample_message se fornecida)
            save_to_file: Se True, salva o prompt em arquivo .md
        
        Returns:
            String com o prompt completo
        """
        try:
            # Import here to avoid circular imports
            from src.core.prompt_engine import PromptEngine
            from src.container import container
            import os
            from datetime import datetime

            # Use current_message if provided, otherwise use sample_message
            user_message = current_message if current_message is not None else sample_message

            # For meta agents, build the enhanced context first
            if meta:
                enhanced_message = self.build_meta_agent_context(
                    user_message, meta, new_agent_id
                )
            else:
                enhanced_message = user_message

            # Get agent home path through the storage service
            agent_home_path = self._storage.get_agent_home_path(agent_id)

            # Get prompt format from configuration
            config_service = container.get_configuration_service()
            prompt_format = config_service.get_prompt_format()

            # Create and configure the PromptEngine - SEMPRE usa o real, não mock
            prompt_engine = PromptEngine(agent_home_path, prompt_format)
            prompt_engine.load_context()

            # Get conversation history (last interactions saved) - only if requested
            if include_history:
                conversation_history = self.get_conversation_history(agent_id)
            else:
                conversation_history = []

            # Build the complete prompt using the configured format
            complete_prompt = prompt_engine.build_prompt_with_format(conversation_history, enhanced_message, include_history)
            
            # Add metadata header for clarity when displaying
            if save_to_file:
                metadata_header = f"""# PROMPT COMPLETO PARA {agent_id.upper()}
# Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Histórico: {len(conversation_history)} interações anteriores
# Meta Agent: {'Sim' if meta else 'Não'}
# Novo Agent ID: {new_agent_id if new_agent_id else 'N/A'}
# Mensagem Atual: "{enhanced_message[:100]}{'...' if len(enhanced_message) > 100 else ''}"

---

"""
                
                final_prompt_with_metadata = metadata_header + complete_prompt
                
                try:
                    # Create prompts directory if it doesn't exist
                    prompts_dir = os.path.join(os.getcwd(), "prompts")
                    os.makedirs(prompts_dir, exist_ok=True)
                    
                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"prompt_{agent_id}_{timestamp}.md"
                    filepath = os.path.join(prompts_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(final_prompt_with_metadata)
                    
                    print(f"✅ Prompt salvo em: {filepath}")
                    
                except Exception as save_error:
                    print(f"⚠️ Erro ao salvar prompt: {save_error}")
            
            return complete_prompt  # Retorna sem metadata para uso no LLM
            
        except Exception as e:
            # Fallback: try to show as much as possible
            try:
                user_message = current_message if current_message is not None else sample_message
                
                # For meta agents, build the enhanced context first
                if meta:
                    enhanced_message = self.build_meta_agent_context(
                        user_message, meta, new_agent_id
                    )
                else:
                    enhanced_message = user_message
                
                fallback_parts = []
                fallback_parts.append(f"❌ Erro ao gerar prompt completo: {e}")
                fallback_parts.append("")
                fallback_parts.append("=== ENHANCED USER INPUT (disponível) ===")
                fallback_parts.append(enhanced_message)
                fallback_parts.append("")
                
                # Try to load at least the persona if possible
                try:
                    from src.core.prompt_engine import PromptEngine
                    from src.container import container

                    agent_home_path = self._storage.get_agent_home_path(agent_id)
                    config_service = container.get_configuration_service()
                    prompt_format = config_service.get_prompt_format()
                    prompt_engine = PromptEngine(agent_home_path, prompt_format)
                    prompt_engine.load_context()
                    
                    fallback_parts.append("=== PERSONA DO AGENTE (disponível) ===")
                    fallback_parts.append(prompt_engine.persona_content[:1000] + "..." if len(prompt_engine.persona_content) > 1000 else prompt_engine.persona_content)
                    fallback_parts.append("")
                    
                    agent_instructions = prompt_engine.agent_config.get("prompt", "")
                    if agent_instructions:
                        fallback_parts.append("=== INSTRUÇÕES DO AGENTE (disponível) ===")
                        fallback_parts.append(agent_instructions[:500] + "..." if len(agent_instructions) > 500 else agent_instructions)
                        fallback_parts.append("")
                    
                except Exception as inner_e:
                    fallback_parts.append(f"❌ Não foi possível carregar persona/instruções: {inner_e}")
                
                fallback_parts.append("=== ESTRUTURA COMPLETA DO PROMPT ===")
                fallback_parts.append("O prompt completo normalmente incluiria:")
                fallback_parts.append("- Persona do agente (carregada de persona.md)")
                fallback_parts.append("- Instruções específicas (do definition.yaml)")
                fallback_parts.append("- Histórico de conversas (se houver)")
                fallback_parts.append("- Esta mensagem do usuário")
                
                return "\n".join(fallback_parts)
                
            except Exception as fallback_error:
                user_message = current_message if current_message is not None else sample_message
                return f"❌ Erro crítico ao gerar prompt: {e} (fallback: {fallback_error})\nMensagem original: {user_message}"