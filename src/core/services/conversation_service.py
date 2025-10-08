# src/core/services/conversation_service.py
"""
SAGA-003: Serviço para gerenciar conversas com instance_id isolado.
Permite múltiplas instâncias do mesmo agente com contextos independentes.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

class ConversationService:
    """Gerencia conversas isoladas por instance_id no MongoDB."""

    def __init__(self):
        """Inicializa conexão com MongoDB."""
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        db_name = os.getenv('MONGO_DATABASE', 'conductor_state')

        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.conversations = self.db['agent_conversations']

        logger.info(f"ConversationService initialized with db: {db_name}")

    def get_conversation_history(
        self,
        instance_id: str,
        agent_name: str
    ) -> List[Dict[str, Any]]:
        """
        Recupera o histórico de conversa para uma instância específica.

        Args:
            instance_id: ID único da instância do agente
            agent_name: Nome do agente

        Returns:
            Lista de mensagens no formato [{"role": "user", "content": "...", "timestamp": "..."}]
        """
        try:
            doc = self.conversations.find_one({"instance_id": instance_id})

            if not doc:
                logger.info(f"No conversation history found for instance_id: {instance_id}")
                return []

            # Validar que o agente corresponde
            if doc.get("agent_name") != agent_name:
                logger.warning(
                    f"Agent mismatch: instance {instance_id} belongs to {doc.get('agent_name')}, "
                    f"not {agent_name}"
                )
                return []

            history = doc.get("conversation_history", [])
            logger.info(f"Retrieved {len(history)} messages for instance {instance_id}")
            return history

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

    def append_to_conversation(
        self,
        instance_id: str,
        agent_name: str,
        user_message: str,
        assistant_response: str
    ) -> bool:
        """
        Adiciona uma nova interação ao histórico da conversa.

        Args:
            instance_id: ID único da instância
            agent_name: Nome do agente
            user_message: Mensagem do usuário
            assistant_response: Resposta do assistente

        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            timestamp = datetime.utcnow().isoformat()

            # Criar as mensagens
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
            result = self.conversations.update_one(
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
                logger.info(f"Creating new conversation for instance {instance_id}")
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
                    self.conversations.insert_one(doc)
                    logger.info(f"Created new conversation for instance {instance_id}")
                except DuplicateKeyError:
                    # Race condition: outro processo criou entre nosso check e insert
                    # Tentar novamente o update
                    self.conversations.update_one(
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

            logger.info(f"Appended conversation for instance {instance_id}")
            return True

        except Exception as e:
            logger.error(f"Error appending to conversation: {e}")
            return False

    def clear_conversation(self, instance_id: str) -> bool:
        """
        Limpa o histórico de uma conversa específica.

        Args:
            instance_id: ID único da instância

        Returns:
            True se limpou com sucesso, False caso contrário
        """
        try:
            result = self.conversations.delete_one({"instance_id": instance_id})
            logger.info(f"Cleared conversation for instance {instance_id} (deleted: {result.deleted_count})")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False

    def get_conversation_metadata(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera apenas os metadados de uma conversa.

        Args:
            instance_id: ID único da instância

        Returns:
            Dict com metadados ou None se não encontrar
        """
        try:
            doc = self.conversations.find_one(
                {"instance_id": instance_id},
                {"metadata": 1, "agent_name": 1, "_id": 0}
            )
            return doc
        except Exception as e:
            logger.error(f"Error retrieving metadata: {e}")
            return None
