# src/core/services/agent_discovery_service.py
from typing import List, Optional
from src.core.services.storage_service import StorageService
from src.core.domain import AgentDefinition


class AgentDiscoveryService:
    """Responsável por descobrir e listar agentes."""

    def __init__(self, storage_service: StorageService):
        self._storage = storage_service.get_repository()

    def discover_agents(self) -> List[AgentDefinition]:
        """Descobre e retorna todas as definições de agentes disponíveis."""
        agent_ids = self._storage.list_agents()
        definitions = []
        
        for agent_id in agent_ids:
            definition = self.get_agent_definition(agent_id)
            if definition:
                definitions.append(definition)
        
        return definitions

    def get_agent_definition(self, agent_id: str) -> Optional[AgentDefinition]:
        """Carrega a definição de um agente específico."""
        definition_data = self._storage.load_definition(agent_id)
        
        if not definition_data:
            return None
        
        # Remove agent_id from definition before creating AgentDefinition
        definition_data = definition_data.copy()
        definition_data.pop("agent_id", None)  # Remove agent_id if present
        
        # Add agent_id as optional parameter
        return AgentDefinition(**definition_data, agent_id=agent_id)

    def get_conversation_history(self, agent_id: str) -> List[dict]:
        """Carrega o histórico de conversas de um agente."""
        return self._storage.load_history(agent_id)

    def clear_conversation_history(self, agent_id: str) -> bool:
        """Limpa o histórico de conversas de um agente."""
        try:
            import os
            
            # Clear the history log file by truncating it
            agent_home_path = self._storage.get_agent_home_path(agent_id)
            history_file = os.path.join(agent_home_path, "history.log")
            
            # Truncate the file by opening in write mode
            with open(history_file, 'w', encoding='utf-8') as f:
                pass  # Just open and close to truncate
            
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
            
            return True
        except Exception:
            return False

    def agent_exists(self, agent_id: str) -> bool:
        """Verifica se um agente existe no sistema."""
        try:
            agents = self.discover_agents()
            return any(agent.agent_id == agent_id for agent in agents)
        except Exception:
            return False

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

    def get_full_prompt(self, agent_id: str, sample_message: str = "Mensagem de exemplo", meta: bool = False, new_agent_id: str = None, current_message: str = None, save_to_file: bool = False) -> str:
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
            
            # Create and configure the PromptEngine - SEMPRE usa o real, não mock
            prompt_engine = PromptEngine(agent_home_path)
            prompt_engine.load_context()
            
            # Get conversation history (last interactions saved)
            conversation_history = self.get_conversation_history(agent_id)
            
            # Build the complete prompt - SEMPRE o prompt real
            complete_prompt = prompt_engine.build_prompt(conversation_history, enhanced_message)
            
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
                    
                    agent_home_path = self._storage.get_agent_home_path(agent_id)
                    prompt_engine = PromptEngine(agent_home_path)
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