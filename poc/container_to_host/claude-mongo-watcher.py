#!/usr/bin/env python3
"""
Universal MongoDB Watcher - Monitora requests de LLMs via MongoDB
Roda na sua sessão autenticada e executa comandos claude, gemini ou cursor-agent
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

class UniversalMongoWatcher:
    def __init__(self,
                 mongo_uri: str = "mongodb://localhost:27017",
                 database: str = "conductor",
                 collection: str = "tasks"):
        """
        Inicializa o watcher MongoDB universal

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
        Executar request para LLM (Claude, Gemini ou Cursor-Agent) baseado no provider.

        Args:
            provider: "claude", "gemini" ou "cursor-agent"
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

            # Log do ambiente antes de montar comando
            logger.info("=" * 80)
            logger.info("🔍 DEBUG: Informações do ambiente")
            logger.info(f"   Python: {sys.executable}")
            logger.info(f"   CWD: {os.getcwd()}")
            logger.info(f"   Target CWD: {cwd}")
            logger.info(f"   USER: {os.environ.get('USER', 'N/A')}")
            logger.info(f"   HOME: {os.environ.get('HOME', 'N/A')}")
            logger.info(f"   PATH: {os.environ.get('PATH', 'N/A')[:200]}...")
            
            # Verificar se cursor-agent existe no PATH
            import shutil
            cursor_path = shutil.which("cursor-agent")
            logger.info(f"   cursor-agent path: {cursor_path if cursor_path else '❌ NÃO ENCONTRADO'}")
            
            # Montar comando baseado no provider
            if provider == "claude":
                command = ["claude", "--print", "--dangerously-skip-permissions"]
            elif provider == "gemini":
                # Usar a mesma implementação da GeminiCLIClient
                # Verificar se o prompt é muito longo para evitar "Argument list too long"
                MAX_PROMPT_LENGTH = 50000
                if len(prompt) > MAX_PROMPT_LENGTH:
                    logger.warning(f"⚠️  Prompt muito longo ({len(prompt)} chars), truncando para evitar erros de sistema")
                    prompt = prompt[:MAX_PROMPT_LENGTH] + "\n\n[PROMPT TRUNCADO PARA EVITAR ERRO DE SISTEMA]"
                
                # Gemini CLI usa -p para o prompt e --approval-mode yolo
                command = ["gemini", "-p", prompt, "--approval-mode", "yolo"]
            elif provider == "cursor-agent":
                command = ["cursor-agent", "--print", "--force"]
            else:
                return f"Provider '{provider}' não suportado. Suportados: claude, gemini, cursor-agent", 1, time.time() - start_time

            logger.info(f"🔧 Executando {provider} em {cwd}")
            logger.info(f"📋 Comando completo: {' '.join(command)}")
            logger.info(f"📏 Tamanho do prompt: {len(prompt)} chars")
            logger.info(f"📝 Primeiros 200 chars do prompt: {prompt[:200]}")
            logger.info("=" * 80)

            # Executar comando - todos usam stdin para o prompt
            logger.info("⏳ Iniciando subprocess.run()...")
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

            logger.info(f"✅ {provider} concluído em {duration:.1f}s - exit code: {result.returncode}")
            logger.info(f"📤 Stdout length: {len(result.stdout)} chars")
            logger.info(f"📤 Stderr length: {len(result.stderr)} chars")
            logger.info(f"📄 Primeiros 500 chars do output:\n{output[:500]}")
            logger.info("=" * 80)

            return output, result.returncode, duration

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"⏰ TIMEOUT após {timeout}s")
            logger.error(f"   Provider: {provider}")
            logger.error(f"   Comando: {' '.join(command)}")
            logger.error("=" * 80)
            return f"Comando excedeu tempo limite de {timeout}s", 124, duration

        except FileNotFoundError as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"❌ COMANDO NÃO ENCONTRADO: {e}")
            logger.error(f"   Provider: {provider}")
            logger.error(f"   Comando tentado: {' '.join(command)}")
            logger.error(f"   PATH: {os.environ.get('PATH', 'N/A')}")
            logger.error("=" * 80)
            return f"Comando não encontrado: {str(e)}", 127, duration

        except Exception as e:
            duration = time.time() - start_time
            logger.error("=" * 80)
            logger.error(f"❌ ERRO NA EXECUÇÃO: {type(e).__name__}")
            logger.error(f"   Mensagem: {str(e)}")
            logger.error(f"   Provider: {provider}")
            logger.error(f"   Comando: {' '.join(command) if 'command' in locals() else 'N/A'}")
            logger.error("=" * 80)
            import traceback
            logger.error(traceback.format_exc())
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

        logger.info("=" * 80)
        logger.info(f"📨 PROCESSANDO NOVA TASK")
        logger.info(f"   ID: {request_id}")
        logger.info(f"   Agent: {agent_id}")
        logger.info(f"   Provider: {provider}")
        logger.info(f"   CWD: {cwd}")
        logger.info(f"   Timeout: {timeout}s")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.info("=" * 80)

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

        logger.info("=" * 80)
        if success:
            status_emoji = "✅" if exit_code == 0 else "❌"
            logger.info(f"{status_emoji} TASK COMPLETADA E SALVA NO MONGODB")
            logger.info(f"   ID: {request_id}")
            logger.info(f"   Agent: {agent_id}")
            logger.info(f"   Exit code: {exit_code}")
            logger.info(f"   Duração: {duration:.2f}s")
            logger.info(f"   Resultado length: {len(result)} chars")
        else:
            logger.error(f"❌ FALHA AO SALVAR RESULTADO NO MONGODB")
            logger.error(f"   ID: {request_id}")
            logger.error(f"   Agent: {agent_id}")
        logger.info("=" * 80)

        return success

    def run(self, poll_interval: float = 1.0):
        """
        Loop principal do watcher

        Args:
            poll_interval: Intervalo entre verificações em segundos
        """
        logger.info("=" * 80)
        logger.info("🚀 UNIVERSAL TASK WATCHER INICIADO")
        logger.info("=" * 80)
        logger.info(f"🔍 Monitorando collection: {self.database_name}.{self.collection_name}")
        logger.info(f"⏱️  Poll interval: {poll_interval}s")
        logger.info("🎯 Suporte: Claude, Gemini, Cursor-Agent")
        logger.info("")
        logger.info("📋 AMBIENTE DE EXECUÇÃO:")
        logger.info(f"   Python: {sys.executable}")
        logger.info(f"   CWD: {os.getcwd()}")
        logger.info(f"   USER: {os.environ.get('USER', 'N/A')}")
        logger.info(f"   HOME: {os.environ.get('HOME', 'N/A')}")
        logger.info(f"   PATH: {os.environ.get('PATH', 'N/A')}")
        
        # Verificar CLIs disponíveis
        import shutil
        logger.info("")
        logger.info("🔍 CLIs DISPONÍVEIS NO PATH:")
        for cli in ["cursor-agent", "claude", "gemini"]:
            cli_path = shutil.which(cli)
            if cli_path:
                logger.info(f"   ✅ {cli}: {cli_path}")
            else:
                logger.info(f"   ❌ {cli}: NÃO ENCONTRADO")
        
        logger.info("=" * 80)

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

    parser = argparse.ArgumentParser(description="Universal MongoDB Watcher - Suporta Claude, Gemini e Cursor-Agent")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017",
                       help="URI de conexão MongoDB")
    parser.add_argument("--database", default="conductor_state",
                       help="Nome do database")
    parser.add_argument("--collection", default="tasks",
                       help="Nome da collection")
    parser.add_argument("--poll-interval", type=float, default=1.0,
                       help="Intervalo entre verificações (segundos)")

    args = parser.parse_args()

    try:
        watcher = UniversalMongoWatcher(
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