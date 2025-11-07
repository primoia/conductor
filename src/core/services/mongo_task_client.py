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

    def submit_task(self, task_id: str, agent_id: str, cwd: str, timeout: int = 600, provider: str = "claude", prompt: str = None, instance_id: str = None, is_councilor_execution: bool = False, councilor_config: dict = None, conversation_id: str = None, screenplay_id: str = None) -> str:
        """
        Insere uma nova tarefa na coleção e retorna seu ID.

        Args:
            agent_id: ID do agente que processará a task
            cwd: Diretório de trabalho para execução
            timeout: Timeout em segundos
            provider: "claude" ou "gemini"
            prompt: Prompt XML completo (persona + playbook + history + user_input)
            instance_id: ID da instância (REQUIRED: para separação de contextos)
            is_councilor_execution: Flag indicando se é execução de conselheiro
            councilor_config: Configuração do conselheiro (se aplicável)
            conversation_id: ID da conversa para contexto (REQUIRED)
            screenplay_id: ID do screenplay para contexto do projeto (REQUIRED)

        Returns:
            str: ID da task inserida
        """
        # 🔍 LOG DETALHADO PARA RASTREAR PROVIDER
        import traceback
        logger.info("🔍 [MONGO_TASK_CLIENT] submit_task chamado com:")
        logger.info(f"   - agent_id: {agent_id}")
        logger.info(f"   - provider: {provider}")
        logger.info(f"   - instance_id: {instance_id}")
        logger.info(f"   - conversation_id: {conversation_id}")
        logger.info(f"   - screenplay_id: {screenplay_id}")
        logger.info(f"   - cwd: {cwd}")
        logger.info(f"   - timeout: {timeout}")
        
        # Capturar stack trace para ver quem chamou
        stack = traceback.extract_stack()
        caller = stack[-2] if len(stack) > 1 else None
        if caller:
            logger.info(f"   - Chamado por: {caller.filename}:{caller.lineno} em {caller.name}()")

        # 🔥 VALIDAÇÕES OBRIGATÓRIAS - NÃO PERMITIR INSERIR SEM ESSES CAMPOS
        # Exceção: Conselheiros (councilor_execution) podem executar sem conversation_id/screenplay_id
        validation_errors = []

        if not prompt:
            validation_errors.append("❌ Campo 'prompt' é obrigatório e não pode ser None ou vazio")

        # Para execuções normais (não conselheiros), todos os campos são obrigatórios
        if not is_councilor_execution:
            if not instance_id:
                validation_errors.append("❌ Campo 'instance_id' é obrigatório e não pode ser None. Cada execução deve ter um instance_id único.")

            if not conversation_id:
                validation_errors.append("❌ Campo 'conversation_id' é obrigatório e não pode ser None. Cada execução deve estar associada a uma conversa.")

            if not screenplay_id:
                validation_errors.append("❌ Campo 'screenplay_id' é obrigatório e não pode ser None. Cada execução deve estar associada a um screenplay (contexto do projeto).")

        if validation_errors:
            error_message = "\n".join([
                "🚨 ERRO: Tentativa de inserir task na coleção MongoDB com campos obrigatórios faltando:",
                *validation_errors,
                "\n📍 Stack trace:",
                f"   Chamado por: {caller.filename}:{caller.lineno} em {caller.name}()" if caller else "   Desconhecido",
                f"\n💡 Dica: Para chat/execuções normais, esses campos são OBRIGATÓRIOS.",
                f"   Apenas conselheiros (is_councilor_execution=True) podem executar sem conversation_id/screenplay_id."
            ])
            logger.error(error_message)
            raise ValueError(error_message)

        task_document = {
            "_id": ObjectId(task_id),  # 🔥 Use task_id from gateway
            "agent_id": agent_id,
            "provider": provider,
            "prompt": prompt,  # 🔥 CAMPO PRINCIPAL: Prompt XML completo
            "cwd": cwd,
            "timeout": timeout,
            "status": "pending",
            "instance_id": instance_id,  # 🔥 REQUIRED: ID da instância para separação de contextos
            "conversation_id": conversation_id,  # 🔥 REQUIRED: ID da conversa para contexto
            "screenplay_id": screenplay_id,  # 🔥 REQUIRED: ID do screenplay para contexto do projeto
            "context": {},  # SAGA-004: Context object for additional metadata
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "result": "",
            "exit_code": None,
            "duration": None,
            # Campos específicos para conselheiros
            "is_councilor_execution": is_councilor_execution,
            "councilor_config": councilor_config if is_councilor_execution else None,
            "severity": None,  # Será definido após análise do resultado
        }

        result = self.collection.insert_one(task_document)
        logger.info(f"📤 Tarefa submetida ao MongoDB com ID: {task_id}")
        return task_id

    def get_task_result(self, task_id: str, poll_interval: float = 2.0, timeout: int = 600) -> dict:
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

    def analyze_severity(self, result: str) -> str:
        """
        Analisa o resultado de uma execução para determinar sua severidade.

        Args:
            result: Resultado da execução (output do agente)

        Returns:
            str: "success", "warning" ou "error"
        """
        if not result:
            return "success"

        lower_result = result.lower()

        # Palavras-chave que indicam erro
        error_keywords = ['crítico', 'erro', 'falha', 'critical', 'error', 'fail', 'exception']
        if any(keyword in lower_result for keyword in error_keywords):
            return 'error'

        # Palavras-chave que indicam warning
        warning_keywords = ['alerta', 'atenção', 'warning', 'aviso', 'vulnerab', 'deprecated']
        if any(keyword in lower_result for keyword in warning_keywords):
            return 'warning'

        return 'success'

    def update_task_severity(self, task_id: str, severity: str) -> bool:
        """
        Atualiza o campo severity de uma task após análise do resultado.

        Args:
            task_id: ID da task
            severity: Severidade determinada ("success", "warning", "error")

        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "severity": severity,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar severity da task {task_id}: {e}")
            return False

    def get_councilor_executions(self, agent_id: str, limit: int = 10) -> list:
        """
        Obtém execuções recentes de um conselheiro.

        Args:
            agent_id: ID do agente conselheiro
            limit: Número máximo de execuções a retornar

        Returns:
            list: Lista de documentos de execução
        """
        try:
            cursor = self.collection.find({
                "agent_id": agent_id,
                "is_councilor_execution": True
            }).sort("created_at", -1).limit(limit)

            executions = []
            for doc in cursor:
                # Converter ObjectId para string
                doc['_id'] = str(doc['_id'])

                # Converter datetime para ISO string
                for field in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                    if field in doc and doc[field]:
                        doc[field] = doc[field].isoformat()

                # Mapear campos para formato esperado pelo frontend
                doc['execution_id'] = doc['_id']
                doc['councilor_id'] = doc['agent_id']
                doc['started_at'] = doc.get('created_at')
                doc['output'] = doc.get('result', '')
                doc['error'] = doc.get('result', '') if doc.get('status') == 'error' else None
                doc['duration_ms'] = int(doc.get('duration', 0) * 1000) if doc.get('duration') else None

                executions.append(doc)

            return executions

        except Exception as e:
            logger.error(f"❌ Erro ao buscar execuções do conselheiro {agent_id}: {e}")
            return []

    def get_councilor_stats(self, agent_id: str) -> dict:
        """
        Calcula estatísticas de execução de um conselheiro.

        Args:
            agent_id: ID do agente conselheiro

        Returns:
            dict: Estatísticas (total_executions, success_rate, last_execution)
        """
        try:
            # Contar total de execuções
            total = self.collection.count_documents({
                "agent_id": agent_id,
                "is_councilor_execution": True,
                "status": {"$in": ["completed", "error"]}
            })

            if total == 0:
                return {
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "last_execution": None
                }

            # Contar sucessos (severity = success)
            successes = self.collection.count_documents({
                "agent_id": agent_id,
                "is_councilor_execution": True,
                "severity": "success"
            })

            # Calcular taxa de sucesso
            success_rate = round((successes / total) * 100, 1) if total > 0 else 0.0

            # Buscar última execução
            last_exec = self.collection.find_one(
                {"agent_id": agent_id, "is_councilor_execution": True},
                sort=[("created_at", -1)]
            )

            last_execution = None
            if last_exec and 'created_at' in last_exec:
                last_execution = last_exec['created_at'].isoformat()

            return {
                "total_executions": total,
                "success_rate": success_rate,
                "last_execution": last_execution
            }

        except Exception as e:
            logger.error(f"❌ Erro ao calcular stats do conselheiro {agent_id}: {e}")
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "last_execution": None
            }

    def ensure_councilor_indexes(self):
        """Cria índices para otimizar queries de conselheiros."""
        try:
            # Índice composto para queries de conselheiros
            self.collection.create_index([
                ("agent_id", 1),
                ("is_councilor_execution", 1),
                ("created_at", -1)
            ])

            # Índice para severity
            self.collection.create_index("severity")

            logger.info("✅ Índices de conselheiros criados com sucesso.")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao criar índices de conselheiros: {e}")