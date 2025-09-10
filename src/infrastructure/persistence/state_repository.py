import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from src.ports.state_repository import IStateRepository as StateRepository
from src.core.exceptions import StatePersistenceError

logger = logging.getLogger(__name__)


class FileStateRepository(StateRepository):
    """
    Implementação do StateRepository que usa arquivos state.json.
    """

    def __init__(self, base_path: str = ".conductor_workspace"):
        self.base_path = Path(base_path)
        self.agents_path = self.base_path / "agents"
        self.agents_path.mkdir(parents=True, exist_ok=True)

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # O load_state agora recebe apenas o agent_id e carrega o JSON completo do agente
        agent_file_path = self.agents_path / f"{agent_id}.json"
        try:
            if agent_file_path.exists():
                with open(agent_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            # Retorna um estado inicial padrão se o arquivo não existir
            return {"definition": {"name": "", "version": "", "schema_version": "", "description": "", "author": "", "tags": [], "capabilities": [], "allowed_tools": []}}
        except Exception as e:
            logger.error(f"Failed to load agent state from {agent_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to load agent state from {agent_file_path}: {e}"
            )

    def save_state(
        self, agent_id: str, state_data: Dict[str, Any]
    ) -> bool:
        # O save_state agora salva o JSON completo do agente
        agent_file_path = self.agents_path / f"{agent_id}.json"
        try:
            self.agents_path.mkdir(parents=True, exist_ok=True)
            with open(agent_file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save agent state to {agent_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to save agent state to {agent_file_path}: {e}"
            )

    def list_agents(self) -> List[str]:
        """Lista os IDs de todos os agentes disponíveis no backend de armazenamento."""
        agent_ids = []
        for item in self.agents_path.iterdir():
            if item.is_file() and item.suffix == ".json":
                agent_ids.append(item.stem)
        return agent_ids


class MongoStateRepository(StateRepository):
    """
    Implementação do StateRepository que usa MongoDB como backend de persistência.

    Requer a biblioteca pymongo e a variável de ambiente MONGO_URI.
    """

    def __init__(
        self,
        database_name: str = "conductor_state",
        collection_name: str = "agent_states",
    ):
        """
        Inicializa o repositório MongoDB.

        Args:
            database_name: Nome do banco de dados (default: "conductor_state")
            collection_name: Nome da coleção (default: "agent_states")
        """
        try:
            import pymongo
        except ImportError:
            raise ImportError(
                "pymongo is required for MongoStateRepository. "
                "Install it with: pip install pymongo"
            )

        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError(
                "MONGO_URI environment variable is required for MongoStateRepository. "
                "Set it to your MongoDB connection string."
            )

        try:
            self.client = pymongo.MongoClient(mongo_uri)
            self.database = self.client[database_name]
            self.collection = self.database[collection_name]

            # Test connection
            self.client.admin.command("ping")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    def _generate_document_id(self, agent_home_path: str, state_file_name: str) -> str:
        """
        Gera um ID único para o documento baseado no caminho do agente.

        Args:
            agent_home_path: Caminho do diretório home do agente
            state_file_name: Nome do arquivo de estado

        Returns:
            ID único para o documento
        """
        # Usa o caminho normalizado como identificador único
        normalized_path = os.path.normpath(agent_home_path)
        return f"{normalized_path}_{state_file_name}"

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # Ajustar assinatura para corresponder à IStateRepository
        # O _generate_document_id precisará ser ajustado ou removido se não for mais necessário
        # Implementação real para MongoDB
        document_id = self._generate_document_id(agent_id, "state.json") # Assumindo state.json como nome padrão
        document = self.collection.find_one({"_id": document_id})
        if document:
            document.pop("_id", None)
            return document
        return {"definition": {"name": "", "version": "", "schema_version": "", "description": "", "author": "", "tags": [], "capabilities": [], "allowed_tools": []}}

    def save_state(
        self, agent_id: str, state_data: Dict[str, Any]
    ) -> bool:
        # Ajustar assinatura para corresponder à IStateRepository
        # Implementação real para MongoDB
        document_id = self._generate_document_id(agent_id, "state.json") # Assumindo state.json como nome padrão
        document_data = state_data.copy()
        document_data.update({"_id": document_id, "updated_at": datetime.now().isoformat()})
        result = self.collection.update_one(
            {"_id": document_id}, {"$set": document_data}, upsert=True
        )
        return result.acknowledged

    def list_agents(self) -> List[str]:
        """Lista os IDs de todos os agentes disponíveis no backend de armazenamento."""
        # Implementação real para MongoDB
        # Retorna os agent_ids de todos os documentos na coleção
        return [doc["agent_id"] for doc in self.collection.find({}, {"agent_id": 1})]

    def close(self):
        """Fecha a conexão com o MongoDB."""
        if hasattr(self, "client"):
            self.client.close()
