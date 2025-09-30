#!/usr/bin/env python3
"""
Claude MongoDB Watcher - Monitora requests do Claude via MongoDB
Roda na sua sessão autenticada e executa comandos claude
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from pymongo import MongoClient
    from bson import ObjectId
except ImportError:
    print("❌ PyMongo não encontrado. Instale com: pip install pymongo")
    sys.exit(1)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/claude-mongo-watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClaudeMongoWatcher:
    def __init__(self,
                 mongo_uri: str = "mongodb://localhost:27017",
                 database: str = "conductor",
                 collection: str = "tasks"):
        """
        Inicializa o watcher MongoDB

        Args:
            mongo_uri: URI de conexão MongoDB
            database: Nome do database
            collection: Nome da collection
        """
        self.mongo_uri = mongo_uri
        self.database_name = database
        self.collection_name = collection

        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[database]
            self.collection = self.db[collection]

            # Testar conexão
            self.client.admin.command('ping')
            logger.info(f"✅ Conectado ao MongoDB: {mongo_uri}")

            # Criar índices se não existirem
            self._create_indexes()

        except Exception as e:
            logger.error(f"❌ Erro ao conectar MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Criar índices necessários"""
        try:
            # Índice para status (para queries rápidas)
            self.collection.create_index("status")

            # Índice para created_at (para ordenação)
            self.collection.create_index("created_at")

            # TTL Index para limpeza automática após 24h
            self.collection.create_index("created_at", expireAfterSeconds=86400)

            logger.info("📊 Índices MongoDB criados/verificados")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao criar índices: {e}")

    def get_pending_requests(self) -> List[Dict]:
        """Buscar requests pendentes"""
        try:
            return list(self.collection.find(
                {"status": "pending"},
                sort=[("created_at", 1)]
            ))
        except Exception as e:
            logger.error(f"❌ Erro ao buscar requests: {e}")
            return []

    def mark_as_processing(self, request_id: ObjectId) -> bool:
        """Marcar request como processando"""
        try:
            result = self.collection.update_one(
                {"_id": request_id, "status": "pending"},
                {
                    "$set": {
                        "status": "processing",
                        "started_at": datetime.now(timezone.utc)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Erro ao marcar como processing: {e}")
            return False

    def complete_request(self, request_id: ObjectId, result: str,
                        exit_code: int, duration: float) -> bool:
        """Completar request com resultado"""
        try:
            status = "completed" if exit_code == 0 else "error"

            update_result = self.collection.update_one(
                {"_id": request_id},
                {
                    "$set": {
                        "status": status,
                        "result": result,
                        "exit_code": exit_code,
                        "duration": duration,
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            return update_result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Erro ao completar request: {e}")
            return False

    def execute_llm_request(self, provider: str, prompt: str, cwd: str,
                              timeout: int = 300) -> tuple[str, int, float]:
        """
        Executar request para LLM (Claude ou Gemini) baseado no provider.

        Args:
            provider: "claude" ou "gemini"
            prompt: Prompt XML completo já formatado
            cwd: Diretório de trabalho
            timeout: Timeout em segundos

        Returns:
            tuple: (result, exit_code, duration)
        """
        start_time = time.time()

        try:
            # Verificar se diretório existe
            if not os.path.isdir(cwd):
                return f"Diretório não encontrado: {cwd}", 1, time.time() - start_time

            # Montar comando baseado no provider
            if provider == "claude":
                command = ["claude", "--print", "--dangerously-skip-permissions"]
            elif provider == "gemini":
                command = ["gemini", "--print"]  # Ajustar conforme CLI do Gemini
            else:
                return f"Provider '{provider}' não suportado", 1, time.time() - start_time

            logger.info(f"🔧 Executando {provider} em {cwd}")

            # Enviar prompt via stdin (não via argumento -p)
            result = subprocess.run(
                command,
                input=prompt,  # Prompt via stdin
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )

            duration = time.time() - start_time
            output = result.stdout + result.stderr

            logger.info(f"✅ {provider} concluído em {duration:.1f}s - código: {result.returncode}")

            return output, result.returncode, duration

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.warning(f"⏰ Timeout após {timeout}s")
            return f"Comando excedeu tempo limite de {timeout}s", 124, duration

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Erro na execução: {e}")
            return f"Erro na execução: {str(e)}", 1, duration

    def process_request(self, request: Dict) -> bool:
        """Processar uma task individual"""
        request_id = request["_id"]
        agent_id = request.get("agent_id", "unknown")
        provider = request.get("provider", "claude")
        cwd = request.get("cwd", ".")
        timeout = request.get("timeout", 300)  # ✅ Alinhado com default da API (300s)

        # Buscar campo 'prompt' com XML completo
        prompt = request.get("prompt", "")

        if not prompt:
            logger.error(f"❌ Task {request_id} não possui campo 'prompt'")
            self.complete_request(request_id, "Erro: campo 'prompt' obrigatório não encontrado", 1, 0.0)
            return False

        logger.info(f"📨 Processando task: {request_id} | Agent: {agent_id} | Provider: {provider}")

        # Marcar como processando
        if not self.mark_as_processing(request_id):
            logger.warning(f"⚠️  Task {request_id} já está sendo processada")
            return False

        # Executar LLM request
        result, exit_code, duration = self.execute_llm_request(
            provider=provider,
            prompt=prompt,
            cwd=cwd,
            timeout=timeout
        )

        # Salvar resultado
        success = self.complete_request(request_id, result, exit_code, duration)

        if success:
            status_emoji = "✅" if exit_code == 0 else "❌"
            logger.info(f"{status_emoji} Task {request_id} processada com sucesso | Agent: {agent_id}")
        else:
            logger.error(f"❌ Falha ao salvar resultado da task {request_id}")

        return success

    def run(self, poll_interval: float = 1.0):
        """
        Loop principal do watcher

        Args:
            poll_interval: Intervalo entre verificações em segundos
        """
        logger.info("🚀 Universal Task Watcher iniciado")
        logger.info(f"🔍 Monitorando collection: {self.database_name}.{self.collection_name}")
        logger.info(f"⏱️  Poll interval: {poll_interval}s")
        logger.info("🎯 Suporte: Claude (mais providers em breve)")

        while True:
            try:
                # Buscar tasks pendentes
                requests = self.get_pending_requests()

                if requests:
                    logger.info(f"📋 Encontradas {len(requests)} tasks pendentes")

                    for request in requests:
                        self.process_request(request)

                # Aguardar próximo ciclo
                time.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Shutdown solicitado pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                time.sleep(5)  # Aguardar mais tempo em caso de erro

        logger.info("👋 Universal Task Watcher finalizado")

def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude MongoDB Watcher")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017",
                       help="URI de conexão MongoDB")
    parser.add_argument("--database", default="conductor",
                       help="Nome do database")
    parser.add_argument("--collection", default="tasks",
                       help="Nome da collection")
    parser.add_argument("--poll-interval", type=float, default=1.0,
                       help="Intervalo entre verificações (segundos)")

    args = parser.parse_args()

    try:
        watcher = ClaudeMongoWatcher(
            mongo_uri=args.mongo_uri,
            database=args.database,
            collection=args.collection
        )

        watcher.run(poll_interval=args.poll_interval)

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()