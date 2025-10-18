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
            self.db = self.client.conductor_state  # Database correto (SAGA-004)
            self.collection = self.db.tasks  # Coleção de tasks
            logger.info("✅ Conexão com MongoDB estabelecida com sucesso.")
        except ConnectionFailure as e:
            logger.critical(f"❌ Falha ao conectar com MongoDB: {e}")
            raise

    def submit_task(self, agent_id: str, cwd: str, timeout: int = 300, provider: str = "claude", prompt: str = None, instance_id: str = None) -> str:
        """
        Insere uma nova tarefa na coleção e retorna seu ID.

        Args:
            agent_id: ID do agente que processará a task
            cwd: Diretório de trabalho para execução
            timeout: Timeout em segundos
            provider: "claude" ou "gemini"
            prompt: Prompt XML completo (persona + playbook + history + user_input)
            instance_id: ID da instância (SAGA-004: para separação de contextos)

        Returns:
            str: ID da task inserida
        """
        # 🔍 LOG DETALHADO PARA RASTREAR PROVIDER
        import traceback
        logger.info("🔍 [MONGO_TASK_CLIENT] submit_task chamado com:")
        logger.info(f"   - agent_id: {agent_id}")
        logger.info(f"   - provider: {provider}")
        logger.info(f"   - instance_id: {instance_id}")
        logger.info(f"   - cwd: {cwd}")
        logger.info(f"   - timeout: {timeout}")
        
        # Capturar stack trace para ver quem chamou
        stack = traceback.extract_stack()
        caller = stack[-2] if len(stack) > 1 else None
        if caller:
            logger.info(f"   - Chamado por: {caller.filename}:{caller.lineno} em {caller.name}()")
        if not prompt:
            raise ValueError("Campo 'prompt' é obrigatório")

        task_document = {
            "agent_id": agent_id,
            "provider": provider,
            "prompt": prompt,  # 🔥 CAMPO PRINCIPAL: Prompt XML completo
            "cwd": cwd,
            "timeout": timeout,
            "status": "pending",
            "instance_id": instance_id,  # SAGA-004: ID da instância para separação de contextos
            "context": {},  # SAGA-004: Context object for additional metadata
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "result": "",
            "exit_code": None,
            "duration": None,
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