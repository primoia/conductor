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
                 collection: str = "claude_requests"):
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

    def execute_claude_command(self, command: List[str], cwd: str,
                              timeout: int = 180) -> tuple[str, int, float]:
        """
        Executar comando claude

        Returns:
            tuple: (result, exit_code, duration)
        """
        start_time = time.time()

        try:
            # Verificar se diretório existe
            if not os.path.isdir(cwd):
                return f"Diretório não encontrado: {cwd}", 1, time.time() - start_time

            # Executar comando
            logger.info(f"🔧 Executando: {' '.join(command)} em {cwd}")

            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )

            duration = time.time() - start_time
            output = result.stdout + result.stderr

            logger.info(f"✅ Comando concluído em {duration:.1f}s - código: {result.returncode}")

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
        """Processar um request individual"""
        request_id = request["_id"]
        command = request.get("command", [])
        cwd = request.get("cwd", ".")
        timeout = request.get("timeout", 180)

        logger.info(f"📨 Processando request: {request_id}")

        # Marcar como processando
        if not self.mark_as_processing(request_id):
            logger.warning(f"⚠️  Request {request_id} já está sendo processado")
            return False

        # Executar comando
        result, exit_code, duration = self.execute_claude_command(command, cwd, timeout)

        # Salvar resultado
        success = self.complete_request(request_id, result, exit_code, duration)

        if success:
            status_emoji = "✅" if exit_code == 0 else "❌"
            logger.info(f"{status_emoji} Request {request_id} processado com sucesso")
        else:
            logger.error(f"❌ Falha ao salvar resultado do request {request_id}")

        return success

    def run(self, poll_interval: float = 1.0):
        """
        Loop principal do watcher

        Args:
            poll_interval: Intervalo entre verificações em segundos
        """
        logger.info("🚀 Claude MongoDB Watcher iniciado")
        logger.info(f"🔍 Monitorando: {self.database_name}.{self.collection_name}")
        logger.info(f"⏱️  Poll interval: {poll_interval}s")

        while True:
            try:
                # Buscar requests pendentes
                requests = self.get_pending_requests()

                if requests:
                    logger.info(f"📋 Encontrados {len(requests)} requests pendentes")

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

        logger.info("👋 Claude MongoDB Watcher finalizado")

def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude MongoDB Watcher")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017",
                       help="URI de conexão MongoDB")
    parser.add_argument("--database", default="conductor",
                       help="Nome do database")
    parser.add_argument("--collection", default="claude_requests",
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