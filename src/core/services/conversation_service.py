# src/core/services/conversation_service.py
"""
🔥 REFATORAÇÃO: Serviço para gerenciar conversas com conversation_id global.

Este serviço implementa o novo modelo de conversações onde:
- Uma conversa é independente de agentes específicos
- Múltiplos agentes podem participar da mesma conversa
- Histórico é unificado e compartilhado entre agentes

Ref: PLANO_REFATORACAO_CONVERSATION_ID.md
Data: 2025-11-01
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
import uuid
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


class ConversationService:
    """
    Gerencia conversas com modelo conversation_id global.

    Uma conversa pode ter múltiplos agentes participantes e mantém
    um histórico unificado de todas as interações.
    """

    def __init__(self):
        """Inicializa conexão com MongoDB."""
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        db_name = os.getenv('MONGO_DATABASE', 'conductor_state')

        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

        # 🔥 NOVA COLLECTION: conversations (modelo refatorado)
        self.conversations = self.db['conversations']

        # 🔄 LEGACY: agent_conversations (manter para compatibilidade na Fase 1-2)
        self.legacy_conversations = self.db['agent_conversations']

        logger.info(f"ConversationService initialized with db: {db_name}")
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Cria índices para otimização de queries."""
        indexes = [
            ("conversation_id", {"unique": True}),
            ("participants.agent_id", {}),
            ("updated_at", {}),
            ("screenplay_id", {}),
        ]
        for key, kwargs in indexes:
            self._safe_create_index(self.conversations, key, **kwargs)

    def _safe_create_index(self, collection, key, **kwargs):
        """Create index silently, ignoring if it already exists."""
        try:
            collection.create_index(key, **kwargs)
        except Exception as e:
            # Ignore IndexKeySpecsConflict (code 86) - index already exists
            if hasattr(e, 'code') and e.code == 86:
                pass  # Index already exists, ignore silently
            else:
                logger.warning(f"⚠️ Falha ao criar índice {key}: {e}")

    # ==========================================
    # NOVO MODELO: Conversas Globais
    # ==========================================

    def create_conversation(
        self,
        title: Optional[str] = None,
        active_agent: Optional[Dict[str, Any]] = None,
        screenplay_id: Optional[str] = None,
        context: Optional[str] = None,
        allowed_agents: Optional[List[str]] = None,
        max_chain_depth: Optional[int] = 10,
        auto_delegate: bool = True,
    ) -> str:
        """
        Cria uma nova conversa.

        Args:
            title: Titulo da conversa (opcional, sera gerado se nao fornecido)
            active_agent: Metadados do agente inicial {agent_id, instance_id, name, emoji}
            screenplay_id: ID do roteiro ao qual esta conversa pertence (opcional)
            context: Contexto da conversa em markdown (bug, feature, etc.) (opcional)
            allowed_agents: Lista de agent_ids permitidos (squad da conversa). None = sem restricao.

        Returns:
            str: conversation_id (UUID)
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Gerar título padrão se não fornecido
        if not title:
            title = f"Conversa {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

        # Validar título (3-100 caracteres)
        if len(title) < 3 or len(title) > 100:
            raise ValueError("O título deve ter entre 3 e 100 caracteres")

        # 🔥 NOVO: Calcular display_order automaticamente
        # Buscar o maior display_order das conversas existentes para o mesmo screenplay_id
        query_filter = {}
        if screenplay_id:
            query_filter["screenplay_id"] = screenplay_id

        # Buscar conversa com maior display_order
        max_order_conversation = self.conversations.find_one(
            query_filter,
            {"display_order": 1},
            sort=[("display_order", -1)]
        )

        # Se existe conversa com display_order, incrementa; senão, inicia em 0
        display_order = 0
        if max_order_conversation and "display_order" in max_order_conversation:
            display_order = max_order_conversation["display_order"] + 1

        logger.info(f"🔢 [CREATE] Calculando display_order para nova conversa: {display_order}")

        conversation_doc = {
            "conversation_id": conversation_id,
            "title": title,
            "created_at": timestamp,
            "updated_at": timestamp,
            "active_agent": active_agent,
            "participants": [active_agent] if active_agent else [],
            "messages": [],
            "screenplay_id": screenplay_id,
            "context": context,  # Campo de contexto em markdown (pode ser null)
            "allowed_agents": allowed_agents,  # Squad da conversa (None = sem restricao)
            "display_order": display_order,  # Ordem de exibicao inicial
            "max_chain_depth": max_chain_depth,  # Per-conversation chain limit (None = use global)
            "auto_delegate": auto_delegate,  # Allow agents to auto-chain without human interaction
        }

        try:
            self.conversations.insert_one(conversation_doc)
            logger.info(f"✅ Conversa criada: {conversation_id} - '{title}'")
            return conversation_id
        except DuplicateKeyError:
            logger.error(f"❌ Conversation ID já existe: {conversation_id}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao criar conversa: {e}", exc_info=True)
            raise

    def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma conversa pelo ID.

        Args:
            conversation_id: ID da conversa

        Returns:
            Dict com dados da conversa ou None se não encontrada
        """
        try:
            conversation = self.conversations.find_one(
                {"conversation_id": conversation_id},
                {"_id": 0}  # Não retornar _id do MongoDB
            )

            if conversation:
                logger.info(f"📖 Conversa encontrada: {conversation_id} ({len(conversation.get('messages', []))} mensagens)")
            else:
                logger.warning(f"⚠️ Conversa não encontrada: {conversation_id}")

            return conversation
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversa: {e}", exc_info=True)
            return None

    def add_message(
        self,
        conversation_id: str,
        user_input: Optional[str] = None,
        agent_response: Optional[str] = None,
        agent_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Adiciona uma ou mais mensagens à conversa.

        Args:
            conversation_id: ID da conversa
            user_input: Mensagem do usuário (opcional)
            agent_response: Resposta do agente (opcional)
            agent_info: Metadados do agente {agent_id, instance_id, name, emoji}

        Returns:
            bool: True se adicionado com sucesso
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            new_messages = []

            # Adicionar mensagem do usuário
            if user_input:
                new_messages.append({
                    "id": str(uuid.uuid4()),
                    "type": "user",
                    "content": user_input,
                    "timestamp": timestamp
                })

            # Adicionar resposta do agente
            if agent_response and agent_info:
                new_messages.append({
                    "id": str(uuid.uuid4()),
                    "type": "bot",
                    "content": agent_response,
                    "timestamp": timestamp,
                    "agent": {
                        "agent_id": agent_info.get("agent_id"),
                        "instance_id": agent_info.get("instance_id"),
                        "name": agent_info.get("name"),
                        "emoji": agent_info.get("emoji")
                    }
                })

                # Adicionar agente aos participantes se ainda não estiver
                self._add_participant(conversation_id, agent_info)

            if not new_messages:
                logger.warning(f"⚠️ Nenhuma mensagem para adicionar")
                return False

            # Atualizar conversa
            result = self.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": {"$each": new_messages}},
                    "$set": {"updated_at": timestamp}
                }
            )

            if result.matched_count == 0:
                logger.error(f"❌ Conversa não encontrada: {conversation_id}")
                return False

            logger.info(f"✅ Adicionadas {len(new_messages)} mensagens à conversa {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao adicionar mensagem: {e}", exc_info=True)
            return False

    def set_active_agent(
        self,
        conversation_id: str,
        agent_info: Dict[str, Any]
    ) -> bool:
        """
        Define o agente ativo para a próxima resposta.

        Args:
            conversation_id: ID da conversa
            agent_info: Metadados do agente {agent_id, instance_id, name, emoji}

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            result = self.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$set": {
                        "active_agent": agent_info,
                        "updated_at": timestamp
                    }
                }
            )

            if result.matched_count == 0:
                logger.error(f"❌ Conversa não encontrada: {conversation_id}")
                return False

            logger.info(f"✅ Agente ativo atualizado: {agent_info.get('name')} ({agent_info.get('agent_id')})")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar agente ativo: {e}", exc_info=True)
            return False

    def _add_participant(self, conversation_id: str, agent_info: Dict[str, Any]):
        """
        Adiciona um agente à lista de participantes se ainda não estiver presente.

        Args:
            conversation_id: ID da conversa
            agent_info: Metadados do agente
        """
        try:
            # Verificar se agente já está nos participantes
            conversation = self.conversations.find_one(
                {
                    "conversation_id": conversation_id,
                    "participants.agent_id": agent_info.get("agent_id")
                }
            )

            if conversation:
                # Agente já é participante
                return

            # Adicionar agente aos participantes
            self.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$push": {"participants": agent_info}}
            )

            logger.info(f"✅ Participante adicionado: {agent_info.get('name')}")

        except Exception as e:
            logger.error(f"❌ Erro ao adicionar participante: {e}", exc_info=True)

    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém as mensagens de uma conversa.

        Args:
            conversation_id: ID da conversa
            limit: Limitar número de mensagens retornadas (mais recentes)

        Returns:
            Lista de mensagens
        """
        try:
            conversation = self.get_conversation_by_id(conversation_id)

            if not conversation:
                return []

            messages = conversation.get("messages", [])

            if limit and limit > 0:
                messages = messages[-limit:]

            return messages

        except Exception as e:
            logger.error(f"❌ Erro ao obter mensagens: {e}", exc_info=True)
            return []

    def list_conversations(
        self,
        limit: int = 20,
        skip: int = 0,
        screenplay_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista conversas recentes.

        Args:
            limit: Número máximo de conversas a retornar
            skip: Número de conversas a pular (paginação)
            screenplay_id: Filtrar conversas por roteiro (opcional)

        Returns:
            Lista de conversas
        """
        try:
            # Construir filtro
            query_filter = {}
            if screenplay_id:
                query_filter["screenplay_id"] = screenplay_id

            conversations = list(
                self.conversations
                .find(query_filter, {"_id": 0})
                .sort("updated_at", -1)
                .skip(skip)
                .limit(limit)
            )

            logger.info(f"📋 Listadas {len(conversations)} conversas" + (f" para screenplay {screenplay_id}" if screenplay_id else ""))
            return conversations

        except Exception as e:
            logger.error(f"❌ Erro ao listar conversas: {e}", exc_info=True)
            return []

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Deleta uma conversa.

        Args:
            conversation_id: ID da conversa

        Returns:
            bool: True se deletada com sucesso
        """
        try:
            result = self.conversations.delete_one({"conversation_id": conversation_id})

            if result.deleted_count > 0:
                logger.info(f"🗑️ Conversa deletada: {conversation_id}")
                return True
            else:
                logger.warning(f"⚠️ Conversa não encontrada para deletar: {conversation_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao deletar conversa: {e}", exc_info=True)
            return False

    def update_conversation_title(self, conversation_id: str, new_title: str) -> bool:
        """
        Atualiza o título de uma conversa.

        Args:
            conversation_id: ID da conversa
            new_title: Novo título (deve ter entre 3 e 100 caracteres)

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            # Validar título
            if len(new_title) < 3 or len(new_title) > 100:
                raise ValueError("O título deve ter entre 3 e 100 caracteres")

            timestamp = datetime.utcnow().isoformat()

            result = self.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$set": {
                        "title": new_title,
                        "updated_at": timestamp
                    }
                }
            )

            if result.matched_count == 0:
                logger.error(f"❌ Conversa não encontrada: {conversation_id}")
                return False

            logger.info(f"✅ Título atualizado para conversa {conversation_id}: '{new_title}'")
            return True

        except ValueError as e:
            logger.error(f"❌ Erro de validação: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar título: {e}", exc_info=True)
            return False

    def update_conversation_context(self, conversation_id: str, context: Optional[str]) -> bool:
        """
        Atualiza o contexto de uma conversa.

        Args:
            conversation_id: ID da conversa
            context: Novo contexto em markdown (pode ser None para limpar)

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            result = self.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$set": {
                        "context": context,
                        "updated_at": timestamp
                    }
                }
            )

            if result.matched_count == 0:
                logger.error(f"❌ Conversa não encontrada: {conversation_id}")
                return False

            logger.info(f"✅ Contexto atualizado para conversa {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar contexto: {e}", exc_info=True)
            return False

    def update_conversation_settings(
        self,
        conversation_id: str,
        max_chain_depth: Optional[int] = None,
        auto_delegate: Optional[bool] = None,
    ) -> bool:
        """
        Update conversation chain settings (max_chain_depth, auto_delegate).

        Args:
            conversation_id: ID da conversa
            max_chain_depth: Per-conversation chain limit (None = unchanged, 0 = reset to global)
            auto_delegate: Allow agents to auto-chain (None = unchanged)

        Returns:
            bool: True if updated successfully
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            updates: Dict[str, Any] = {"updated_at": timestamp}

            if max_chain_depth is not None:
                # 0 means "reset to global default" → store as None
                updates["max_chain_depth"] = max_chain_depth if max_chain_depth > 0 else None

            if auto_delegate is not None:
                updates["auto_delegate"] = auto_delegate

            if len(updates) == 1:
                # Only updated_at, nothing to change
                return True

            result = self.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": updates}
            )

            if result.matched_count == 0:
                logger.error(f"Conversa nao encontrada: {conversation_id}")
                return False

            logger.info(f"Settings updated for conversation {conversation_id}: {updates}")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar settings: {e}", exc_info=True)
            return False

    def update_conversation_order(self, order_updates: List[Dict[str, Any]]) -> int:
        """
        🔥 NOVO: Atualiza a ordem de exibição das conversas.

        Args:
            order_updates: Lista de dicionários com {conversation_id: str, display_order: int}

        Returns:
            int: Número de conversas atualizadas
        """
        try:
            updated_count = 0

            for update in order_updates:
                conversation_id = update.get("conversation_id")
                display_order = update.get("display_order")

                if not conversation_id or display_order is None:
                    logger.warning(f"⚠️ Update inválido ignorado: {update}")
                    continue

                result = self.conversations.update_one(
                    {"conversation_id": conversation_id},
                    {
                        "$set": {
                            "display_order": display_order,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )

                if result.matched_count > 0:
                    updated_count += 1

            logger.info(f"✅ Ordem atualizada para {updated_count}/{len(order_updates)} conversas")
            return updated_count

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar ordem das conversas: {e}", exc_info=True)
            raise

    # ==========================================
    # LEGACY: Compatibilidade com modelo antigo
    # ==========================================

    def get_conversation_history_legacy(
        self,
        instance_id: str,
        agent_name: str
    ) -> List[Dict[str, Any]]:
        """
        🔄 LEGACY: Recupera histórico no formato antigo (agent_conversations).

        Este método será removido na Fase 4 após migração completa.

        Args:
            instance_id: ID único da instância do agente
            agent_name: Nome do agente

        Returns:
            Lista de mensagens no formato antigo
        """
        try:
            doc = self.legacy_conversations.find_one({"instance_id": instance_id})

            if not doc:
                logger.info(f"No legacy history found for instance_id: {instance_id}")
                return []

            # Validar que o agente corresponde
            if doc.get("agent_name") != agent_name:
                logger.warning(
                    f"Agent mismatch: instance {instance_id} belongs to {doc.get('agent_name')}, "
                    f"not {agent_name}"
                )
                return []

            history = doc.get("conversation_history", [])
            logger.info(f"Retrieved {len(history)} messages from legacy for instance {instance_id}")
            return history

        except Exception as e:
            logger.error(f"Error retrieving legacy conversation history: {e}")
            return []

    def append_to_conversation_legacy(
        self,
        instance_id: str,
        agent_name: str,
        user_message: str,
        assistant_response: str
    ) -> bool:
        """
        🔄 LEGACY: Adiciona mensagem no formato antigo (agent_conversations).

        Este método será removido na Fase 4 após migração completa.
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            new_messages = [
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": timestamp
                },
                {
                    "role": "assistant",
                    "content": assistant_response,
                    "timestamp": timestamp
                }
            ]

            # Tentar atualizar documento existente
            result = self.legacy_conversations.update_one(
                {"instance_id": instance_id},
                {
                    "$push": {
                        "conversation_history": {"$each": new_messages}
                    },
                    "$set": {
                        "metadata.last_interaction": timestamp
                    },
                    "$inc": {
                        "metadata.total_messages": 2
                    }
                }
            )

            # Se não existir, criar novo documento
            if result.matched_count == 0:
                logger.info(f"Creating new legacy conversation for instance {instance_id}")
                doc = {
                    "instance_id": instance_id,
                    "agent_name": agent_name,
                    "conversation_history": new_messages,
                    "metadata": {
                        "created_at": timestamp,
                        "last_interaction": timestamp,
                        "total_messages": 2
                    }
                }

                try:
                    self.legacy_conversations.insert_one(doc)
                except DuplicateKeyError:
                    # Race condition: tentar update novamente
                    self.legacy_conversations.update_one(
                        {"instance_id": instance_id},
                        {
                            "$push": {
                                "conversation_history": {"$each": new_messages}
                            },
                            "$set": {
                                "metadata.last_interaction": timestamp
                            },
                            "$inc": {
                                "metadata.total_messages": 2
                            }
                        }
                    )

            logger.info(f"Appended to legacy conversation for instance {instance_id}")
            return True

        except Exception as e:
            logger.error(f"Error appending to legacy conversation: {e}")
            return False
