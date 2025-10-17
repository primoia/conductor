# src/infrastructure/storage/mongo_repository.py
import json
import uuid
from typing import Dict, Any, List
from pymongo import MongoClient
from datetime import datetime

from src.ports.state_repository import IStateRepository


class MongoStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em MongoDB.

    Trabalha com tipos primitivos (Dict, str) e gerencia a persistência
    de baixo nível no MongoDB.
    """

    def __init__(self, connection_string: str, db_name: str = "conductor_state"):
        print("DEBUG: MongoStateRepository.__init__ começou")  # DEBUG

        # Auto-detect if running in Docker or not and adjust connection string
        import os
        is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "true"

        if not is_docker and "host.docker.internal" in connection_string:
            # Running outside Docker, replace host.docker.internal with localhost
            connection_string = connection_string.replace("host.docker.internal", "localhost")
            print(f"DEBUG: Detectado execução fora do Docker, usando localhost")  # DEBUG

        print(f"DEBUG: Connection string ajustada: {connection_string}")  # DEBUG

        # Add serverSelectionTimeoutMS to avoid hanging
        self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        print("DEBUG: MongoClient criado")  # DEBUG
        self.db = self.client[db_name]
        self.agents_collection = self.db["agents"]
        self.history_collection = self.db["history"]
        self.sessions_collection = self.db["sessions"]
        print("DEBUG: Collections configuradas")  # DEBUG

        # Try to create indexes, but don't fail if it doesn't work
        try:
            print("DEBUG: Criando índices...")  # DEBUG
            # Criar índice TTL na coleção de sessões, se não existir
            self.sessions_collection.create_index("createdAt", expireAfterSeconds=86400)

            # Criar índices para otimização
            self.agents_collection.create_index("agent_id")
            self.history_collection.create_index("agent_id")
            self.sessions_collection.create_index("agent_id")
            print("DEBUG: Índices criados com sucesso")  # DEBUG
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível criar índices no MongoDB: {e}")
            print("   O sistema continuará funcionando, mas pode ter performance reduzida")
            # Continue anyway - indexes are optional for basic operation

    def load_definition(self, agent_id: str) -> Dict:
        """Carrega a definição do agente como dicionário."""
        doc = self.agents_collection.find_one({"agent_id": agent_id})
        if not doc or "definition" not in doc:
            return {}
        return doc["definition"]

    def save_definition(self, agent_id: str, definition_data: Dict) -> bool:
        """Salva a definição do agente."""
        try:
            self.agents_collection.update_one(
                {"agent_id": agent_id},
                {"$set": {"definition": definition_data}},
                upsert=True
            )
            return True
        except Exception:
            return False

    def load_persona(self, agent_id: str) -> str:
        """Carrega a persona do agente como string."""
        doc = self.agents_collection.find_one({"agent_id": agent_id})
        if not doc or "persona" not in doc:
            return ""
        return doc["persona"].get("content", "")

    def save_persona(self, agent_id: str, persona_content: str) -> bool:
        """Salva a persona do agente."""
        try:
            self.agents_collection.update_one(
                {"agent_id": agent_id},
                {"$set": {"persona": {"content": persona_content}}},
                upsert=True
            )
            return True
        except Exception:
            return False

    def load_session(self, agent_id: str) -> Dict:
        """Carrega os dados da sessão como dicionário."""
        doc = self.sessions_collection.find_one({"agent_id": agent_id})
        if not doc:
            return {}
        return {
            "current_task_id": doc.get("current_task_id"),
            "state": doc.get("state", {})
        }

    def save_session(self, agent_id: str, session_data: Dict) -> bool:
        """Salva os dados da sessão."""
        try:
            doc = {
                "agent_id": agent_id,
                "current_task_id": session_data.get("current_task_id"),
                "state": session_data.get("state", {}),
                "createdAt": datetime.utcnow()
            }

            self.sessions_collection.replace_one(
                {"agent_id": agent_id},
                doc,
                upsert=True
            )
            return True
        except Exception:
            return False

    def load_knowledge(self, agent_id: str) -> Dict:
        """Carrega os dados de conhecimento como dicionário."""
        doc = self.agents_collection.find_one({"agent_id": agent_id})
        if not doc or "knowledge" not in doc:
            return {}
        return doc["knowledge"]

    def save_knowledge(self, agent_id: str, knowledge_data: Dict) -> bool:
        """Salva os dados de conhecimento."""
        try:
            self.agents_collection.update_one(
                {"agent_id": agent_id},
                {"$set": {"knowledge": knowledge_data}},
                upsert=True
            )
            return True
        except Exception:
            return False

    def load_playbook(self, agent_id: str) -> Dict:
        """Carrega os dados do playbook como dicionário."""
        doc = self.agents_collection.find_one({"agent_id": agent_id})
        if not doc or "playbook" not in doc:
            return {}
        return doc["playbook"]

    def save_playbook(self, agent_id: str, playbook_data: Dict) -> bool:
        """Salva os dados do playbook."""
        try:
            self.agents_collection.update_one(
                {"agent_id": agent_id},
                {"$set": {"playbook": playbook_data}},
                upsert=True
            )
            return True
        except Exception:
            return False

    def append_to_history(self, agent_id: str, history_entry: Dict, instance_id: str = None) -> bool:
        """
        Adiciona uma entrada ao histórico.

        Args:
            agent_id: ID do agente
            history_entry: Dados da entrada de histórico
            instance_id: ID da instância (para isolamento de contextos por sessão/UI)
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            doc = dict(history_entry)  # Copia o dict
            doc["agent_id"] = agent_id
            doc["createdAt"] = datetime.utcnow()

            # SAGA-004: Adicionar instance_id para separação de contextos
            if instance_id:
                doc["instance_id"] = instance_id
                logger.info(f"✅ [MONGO_REPOSITORY] instance_id adicionado ao documento: {instance_id}")
            else:
                logger.warning(f"⚠️ [MONGO_REPOSITORY] instance_id não fornecido para agent_id: {agent_id}")

            # Sempre força um _id único para evitar conflitos
            # Remove qualquer _id existente (vazio ou não) e gera um novo
            if "_id" in doc:
                del doc["_id"]

            # Gera um _id único usando UUID
            doc["_id"] = str(uuid.uuid4())

            logger.info("=" * 80)
            logger.info(f"💾 [MONGO_REPOSITORY] Inserindo documento no MongoDB:")
            logger.info(f"   - Collection: history")
            logger.info(f"   - agent_id: {agent_id}")
            logger.info(f"   - instance_id: {doc.get('instance_id', 'None')}")
            logger.info(f"   - _id: {doc['_id']}")
            logger.info(f"   - user_input: {doc.get('user_input', '')[:100]}...")
            logger.info(f"   - ai_response: {doc.get('ai_response', '')[:100]}...")
            logger.info("=" * 80)

            self.history_collection.insert_one(doc)
            
            logger.info(f"✅ [MONGO_REPOSITORY] Documento inserido com sucesso na collection 'history'!")
            return True
        except Exception as e:
            import json
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"MongoDB insert failed for agent {agent_id}: {e}")
            logger.error(f"Document data: {json.dumps(doc, indent=2, default=str)}")
            return False

    def load_history(self, agent_id: str) -> List[Dict]:
        """Carrega o histórico completo como lista de dicionários."""
        try:
            cursor = self.history_collection.find({"agent_id": agent_id}).sort("_id", 1)
            history_entries = []

            for doc in cursor:
                # Remove campos internos do MongoDB
                doc.pop("_id", None)
                doc.pop("createdAt", None)
                history_entries.append(doc)

            return history_entries
        except Exception:
            return []

    def clear_history(self, agent_id: str) -> bool:
        """Limpa o histórico completo de um agente."""
        try:
            result = self.history_collection.delete_many({"agent_id": agent_id})
            return True  # Retorna True mesmo se nenhum documento foi encontrado
        except Exception:
            return False

    def list_agents(self) -> List[str]:
        """Lista todos os agentes disponíveis."""
        try:
            # Busca agent_ids únicos em ambas coleções
            agents_ids = set()

            # Da coleção de agentes
            for doc in self.agents_collection.find({}, {"agent_id": 1}):
                if "agent_id" in doc:
                    agents_ids.add(doc["agent_id"])

            # Da coleção de histórico (pode ter agentes que não estão na principal)
            for doc in self.history_collection.distinct("agent_id"):
                if doc:
                    agents_ids.add(doc)

            return sorted(list(agents_ids))
        except Exception:
            return []

    def get_agent_home_path(self, agent_id: str) -> str:
        """Retorna um caminho conceitual para o agente no MongoDB."""
        return f"mongodb://agents/{agent_id}"