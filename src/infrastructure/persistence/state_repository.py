import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from src.ports.state_repository import StateRepository
from src.core.exceptions import StatePersistenceError

logger = logging.getLogger(__name__)


class FileStateRepository(StateRepository):
    """
    Implementação do StateRepository que usa arquivos state.json.
    """

    def load_state(self, agent_home_path: str, state_file_name: str) -> Dict[str, Any]:
        state_file_path = os.path.join(agent_home_path, state_file_name)
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            # Retorna um estado inicial padrão se o arquivo não existir
            return {"conversation_history": []}
        except Exception as e:
            logger.error(f"Failed to load state from {state_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to load state from {state_file_path}: {e}"
            )

    def save_state(
        self, agent_home_path: str, state_file_name: str, state_data: Dict[str, Any]
    ) -> bool:
        state_file_path = os.path.join(agent_home_path, state_file_name)
        try:
            os.makedirs(os.path.dirname(state_file_path), exist_ok=True)
            with open(state_file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save state to {state_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to save state to {state_file_path}: {e}"
            )


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

    def load_state(self, agent_home_path: str, state_file_name: str) -> Dict[str, Any]:
        """
        Carrega o estado de um agente do MongoDB.

        Args:
            agent_home_path: Caminho do diretório home do agente
            state_file_name: Nome do arquivo de estado

        Returns:
            Dicionário com o estado ou estado inicial padrão se não existir
        """
        try:
            document_id = self._generate_document_id(agent_home_path, state_file_name)

            document = self.collection.find_one({"_id": document_id})

            if document:
                # Remove o _id do MongoDB antes de retornar
                document.pop("_id", None)
                return document
            else:
                # Retorna estado inicial padrão se o documento não existir
                return {"conversation_history": []}

        except Exception as e:
            logger.error(f"Failed to load state from MongoDB for {document_id}: {e}")
            raise StatePersistenceError(
                f"Failed to load state from MongoDB for {document_id}: {e}"
            )

    def save_state(
        self, agent_home_path: str, state_file_name: str, state_data: Dict[str, Any]
    ) -> bool:
        """
        Salva o estado de um agente no MongoDB.

        Args:
            agent_home_path: Caminho do diretório home do agente
            state_file_name: Nome do arquivo de estado
            state_data: Dados do estado para salvar

        Returns:
            True em caso de sucesso, False caso contrário
        """
        try:
            document_id = self._generate_document_id(agent_home_path, state_file_name)

            # Adiciona metadados do repositório
            document_data = state_data.copy()
            document_data.update(
                {
                    "_id": document_id,
                    "agent_home_path": agent_home_path,
                    "state_file_name": state_file_name,
                    "repository_type": "mongo",
                    "updated_at": datetime.now().isoformat(),
                }
            )

            # Usa upsert para criar ou atualizar o documento
            result = self.collection.update_one(
                {"_id": document_id}, {"$set": document_data}, upsert=True
            )

            return result.acknowledged

        except Exception as e:
            logger.error(f"Failed to save state to MongoDB for {document_id}: {e}")
            raise StatePersistenceError(
                f"Failed to save state to MongoDB for {document_id}: {e}"
            )

    def close(self):
        """Fecha a conexão com o MongoDB."""
        if hasattr(self, "client"):
            self.client.close()
