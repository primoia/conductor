# projects/conductor/src/core/services/mongo_task_client.py
import os
import time
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId

logger = logging.getLogger(__name__)

class MongoTaskClient:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("A variável de ambiente MONGO_URI não foi definida.")

        try:
            self.client = MongoClient(mongo_uri)
            # Testa a conexão
            self.client.admin.command('ping')
            self.db = self.client.conductor # Nome do database
            self.collection = self.db.tasks # Nome da coleção (padronizado)
            logger.info("✅ Conexão com MongoDB estabelecida com sucesso.")
        except ConnectionFailure as e:
            logger.critical(f"❌ Falha ao conectar com MongoDB: {e}")
            raise

    def submit_task(self, agent_id: str, command: list, cwd: str, timeout: int = 300, provider: str = "claude") -> str:
        """Insere uma nova tarefa na coleção e retorna seu ID."""
        task_document = {
            "agent_id": agent_id,
            "provider": provider,
            "command": command,
            "cwd": cwd,
            "timeout": timeout,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "result": "",  # Para compatibilidade com o watcher
            "exit_code": None,
            "duration": None,
            "metadata": {
                "original_user_input": " ".join(command) if command else "",
                "retry_count": 0
            }
        }
        result = self.collection.insert_one(task_document)
        task_id = str(result.inserted_id)
        logger.info(f"📤 Tarefa submetida ao MongoDB com ID: {task_id}")
        return task_id

    def get_task_result(self, task_id: str, poll_interval: float = 2.0, timeout: int = 300) -> dict:
        """
        Verifica o status de uma tarefa via polling até que ela seja concluída
        ou o tempo limite seja atingido.
        """
        start_time = time.time()
        logger.info(f"⏳ Aguardando resultado para a tarefa {task_id}...")

        while time.time() - start_time < timeout:
            task_document = self.collection.find_one({"_id": ObjectId(task_id)})

            if not task_document:
                raise ValueError(f"Tarefa com ID {task_id} não encontrada.")

            status = task_document.get("status")
            if status not in ["pending", "processing"]:
                logger.info(f"✅ Tarefa {task_id} concluída com status: {status}")
                # Converte ObjectId para string para ser serializável em JSON
                task_document['_id'] = str(task_document['_id'])
                # Converte datetime para string se presente
                if 'created_at' in task_document:
                    task_document['created_at'] = task_document['created_at'].isoformat()
                if 'started_at' in task_document:
                    task_document['started_at'] = task_document['started_at'].isoformat()
                if 'completed_at' in task_document:
                    task_document['completed_at'] = task_document['completed_at'].isoformat()
                return task_document

            time.sleep(poll_interval)

        raise TimeoutError(f"⏰ Tempo de espera excedido para a tarefa {task_id}")