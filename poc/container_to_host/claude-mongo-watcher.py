#!/usr/bin/env python3
"""
Universal MongoDB Watcher - Monitora requests de LLMs via MongoDB
Roda na sua sessão autenticada e executa comandos claude, gemini ou cursor-agent

VERSÃO PARALELIZADA - Suporta execução simultânea de múltiplas tasks
"""

import os
import sys
import time
import subprocess
import logging
import signal
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future
from collections import defaultdict

try:
    from pymongo import MongoClient
    from bson import ObjectId
except ImportError:
    print("❌ PyMongo não encontrado. Instale com: pip install pymongo")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ Requests não encontrado. Instale com: pip install requests")
    sys.exit(1)

import json
import tempfile

# ============================================================================
# MCP Container Service - Gerenciamento On-Demand de MCPs
# ============================================================================
try:
    from mcp_container_service import MCPContainerService
    MCP_ON_DEMAND_AVAILABLE = True
except ImportError:
    MCP_ON_DEMAND_AVAILABLE = False
    MCPContainerService = None

# Host onde os MCPs estão rodando (gateway) - usado como fallback
MCP_HOST = os.environ.get("MCP_HOST", "localhost")

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
                 collection: str = "tasks",
                 gateway_url: str = "http://localhost:5006",
                 max_workers: int = 5,
                 fifo_mode: str = "per_agent"):
        """
        Inicializa o watcher MongoDB universal com suporte a paralelização

        Args:
            mongo_uri: URI de conexão MongoDB
            database: Nome do database
            collection: Nome da collection
            gateway_url: URL do conductor-gateway para atualização de estatísticas
            max_workers: Número máximo de workers paralelos (padrão: 5)
            fifo_mode: Modo FIFO - "strict" (uma task por vez), "per_agent" (FIFO por agente),
                      "relaxed" (qualquer task pendente). Padrão: "per_agent"
        """
        self.mongo_uri = mongo_uri
        self.database_name = database
        self.collection_name = collection
        self.gateway_url = gateway_url.rstrip('/')
        self.max_workers = max_workers
        self.fifo_mode = fifo_mode

        # Controle de paralelização
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TaskWorker")
        self.active_futures: Set[Future] = set()
        self.futures_lock = threading.Lock()

        # Controle FIFO por agente
        self.agent_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self.processing_agents: Set[str] = set()
        self.processing_agents_lock = threading.Lock()

        # Métricas de paralelização
        self.metrics = {
            "total_tasks_processed": 0,
            "total_tasks_failed": 0,
            "total_execution_time": 0.0,
            "concurrent_tasks_count": 0,
            "max_concurrent_tasks": 0,
            "tasks_by_agent": defaultdict(int),
            "errors_by_agent": defaultdict(int)
        }
        self.metrics_lock = threading.Lock()

        # Controle de shutdown
        self.shutdown_requested = False
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[database]
            self.collection = self.db[collection]

            # Testar conexão
            self.client.admin.command('ping')
            logger.info(f"✅ Conectado ao MongoDB: {mongo_uri}")

            # Criar índices se não existirem
            self._create_indexes()

            # Inicializar MCP Container Service (on-demand)
            if MCP_ON_DEMAND_AVAILABLE:
                self.mcp_service = MCPContainerService(self.db)
                logger.info("✅ MCP Container Service inicializado (on-demand habilitado)")
            else:
                self.mcp_service = None
                logger.warning("⚠️  MCP Container Service não disponível (on-demand desabilitado)")

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

            # Índice composto para queries otimizadas (agent_id + status + created_at)
            self.collection.create_index([("agent_id", 1), ("status", 1), ("created_at", 1)])

            # TTL Index para limpeza automática após 24h
            self.collection.create_index("created_at", expireAfterSeconds=86400)

            logger.info("📊 Índices MongoDB criados/verificados")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao criar índices: {e}")

    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Busca um agent pelo agent_id na collection agents."""
        try:
            agents_collection = self.db["agents"]
            return agents_collection.find_one({"agent_id": agent_id})
        except Exception as e:
            logger.error(f"❌ Erro ao buscar agent '{agent_id}': {e}")
            return None

    def emit_task_event(self, event_type: str, task_data: Dict):
        """
        Emite evento de task para o Gateway via HTTP.
        O Gateway então faz broadcast via WebSocket para todos os clientes.

        Args:
            event_type: Tipo do evento (task_started, task_completed, task_error)
            task_data: Dados da task do MongoDB
        """
        try:
            agent_id = task_data.get("agent_id", "unknown")

            # Buscar dados do agente
            agent_data = self.get_agent(agent_id) or {}
            definition = agent_data.get("definition", {})
            agent_name = definition.get("name", agent_id)
            agent_emoji = definition.get("emoji", "🤖")

            # Extrair resultado resumido (primeiros 200 chars)
            result = task_data.get("result", "")
            result_summary = (result[:200] + "...") if len(result) > 200 else result

            # Montar payload do evento
            payload = {
                "type": event_type,
                "data": {
                    "task_id": str(task_data.get("_id", "")),
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "agent_emoji": agent_emoji,
                    "instance_id": task_data.get("instance_id"),
                    "conversation_id": task_data.get("conversation_id"),
                    "screenplay_id": task_data.get("screenplay_id"),
                    "status": task_data.get("status", "unknown"),
                    "duration_ms": int((task_data.get("duration") or 0) * 1000),
                    "exit_code": task_data.get("exit_code"),
                    "result_summary": result_summary,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

            # Log payload para debug
            logger.info(f"📡 [EVENT] Payload: screenplay_id={payload['data'].get('screenplay_id')}, conversation_id={payload['data'].get('conversation_id')}, instance_id={payload['data'].get('instance_id')}")

            # Enviar para o Gateway
            url = f"{self.gateway_url}/api/internal/task-event"
            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                logger.info(f"📡 [EVENT] Evento {event_type} emitido para {agent_name}")
            else:
                logger.warning(f"⚠️ [EVENT] Falha ao emitir evento: {response.status_code}")

        except requests.exceptions.Timeout:
            logger.warning(f"⏰ [EVENT] Timeout ao emitir evento {event_type}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"🔌 [EVENT] Gateway não disponível para emitir evento {event_type}")
        except Exception as e:
            logger.warning(f"⚠️ [EVENT] Erro ao emitir evento {event_type}: {e}")

    def _signal_handler(self, signum, frame):
        """Handler para sinais de shutdown (SIGTERM, SIGINT)"""
        logger.info(f"🛑 Sinal {signum} recebido. Iniciando graceful shutdown...")
        self.shutdown_requested = True

    def _can_process_agent(self, agent_id: str) -> bool:
        """
        Verifica se podemos processar uma task deste agente baseado no modo FIFO

        Args:
            agent_id: ID do agente

        Returns:
            bool: True se pode processar, False caso contrário
        """
        # FIFO DESABILITADO - Permitir execução paralela sem restrições
        # TODO: Implementar FIFO por agent_id + cwd para evitar conflitos no mesmo diretório
        # enquanto permite paralelismo em diretórios diferentes
        return True

        # --- CÓDIGO FIFO ORIGINAL (comentado) ---
        # if self.fifo_mode == "strict":
        #     # Modo strict: apenas uma task por vez em todo o sistema
        #     with self.processing_agents_lock:
        #         return len(self.processing_agents) == 0
        #
        # elif self.fifo_mode == "per_agent":
        #     # Modo per_agent: uma task por agente
        #     with self.processing_agents_lock:
        #         return agent_id not in self.processing_agents
        #
        # else:  # "relaxed"
        #     # Modo relaxed: sem restrição FIFO
        #     return True

    def _mark_agent_processing(self, agent_id: str):
        """Marca um agente como processando"""
        with self.processing_agents_lock:
            self.processing_agents.add(agent_id)
            with self.metrics_lock:
                self.metrics["concurrent_tasks_count"] += 1
                if self.metrics["concurrent_tasks_count"] > self.metrics["max_concurrent_tasks"]:
                    self.metrics["max_concurrent_tasks"] = self.metrics["concurrent_tasks_count"]

    def _unmark_agent_processing(self, agent_id: str):
        """Remove marca de processamento de um agente"""
        with self.processing_agents_lock:
            self.processing_agents.discard(agent_id)
            with self.metrics_lock:
                self.metrics["concurrent_tasks_count"] = max(0, self.metrics["concurrent_tasks_count"] - 1)

    def _update_metrics(self, agent_id: str, success: bool, duration: float):
        """Atualiza métricas de execução"""
        with self.metrics_lock:
            self.metrics["total_tasks_processed"] += 1
            if not success:
                self.metrics["total_tasks_failed"] += 1
                self.metrics["errors_by_agent"][agent_id] += 1
            self.metrics["total_execution_time"] += duration
            self.metrics["tasks_by_agent"][agent_id] += 1

    def get_metrics(self) -> Dict:
        """Retorna métricas atuais"""
        with self.metrics_lock:
            return {
                **self.metrics,
                "tasks_by_agent": dict(self.metrics["tasks_by_agent"]),
                "errors_by_agent": dict(self.metrics["errors_by_agent"]),
                "average_execution_time": (
                    self.metrics["total_execution_time"] / self.metrics["total_tasks_processed"]
                    if self.metrics["total_tasks_processed"] > 0 else 0
                ),
                "success_rate": (
                    100 * (self.metrics["total_tasks_processed"] - self.metrics["total_tasks_failed"])
                    / self.metrics["total_tasks_processed"]
                    if self.metrics["total_tasks_processed"] > 0 else 100
                )
            }

    def generate_mcp_config(self, mcp_configs: List[str], host: str = None) -> Optional[str]:
        """
        Gera arquivo temporário de configuração MCP para Claude CLI.

        Args:
            mcp_configs: Lista de nomes de MCP (ex: ["prospector", "database"])
            host: Host onde os MCPs estão rodando (padrão: MCP_HOST)

        Returns:
            str: Caminho do arquivo temporário de configuração, ou None se lista vazia
        """
        if not mcp_configs:
            return None

        host = host or MCP_HOST
        mcp_servers = {}

        for mcp_name in mcp_configs:
            if mcp_name in MCP_PORTS:
                port = MCP_PORTS[mcp_name]
                mcp_servers[mcp_name] = {
                    "type": "sse",
                    "url": f"http://{host}:{port}/sse"
                }
                logger.info(f"🔌 [MCP] Adicionando MCP '{mcp_name}' em http://{host}:{port}/sse")
            else:
                logger.warning(f"⚠️  [MCP] MCP '{mcp_name}' não encontrado em MCP_PORTS, ignorando")

        if not mcp_servers:
            logger.warning("⚠️  [MCP] Nenhum MCP válido encontrado para configurar")
            return None

        config = {"mcpServers": mcp_servers}

        # Criar arquivo temporário (não deletar automaticamente, Claude precisa ler)
        fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="mcp_config_")
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"📄 [MCP] Config gerada em {temp_path}: {json.dumps(config)}")
            return temp_path
        except Exception as e:
            logger.error(f"❌ [MCP] Erro ao criar arquivo de config: {e}")
            return None

    def fetch_mcp_config_from_gateway(
        self,
        agent_id: str = None,
        instance_id: str = None,
        gateway_url: str = None
    ) -> Optional[str]:
        """
        Busca configuração MCP do Gateway Registry e cria arquivo temporário.

        O Gateway retorna o formato mcpServers pronto para Claude CLI,
        combinando MCPs do agente template + instância.

        Args:
            agent_id: ID do agente template
            instance_id: ID da instância (opcional)
            gateway_url: URL base do Gateway (padrão: GATEWAY_URL ou localhost:14199)

        Returns:
            str: Caminho do arquivo temporário de configuração, ou None se erro/vazio
        """
        if not agent_id and not instance_id:
            logger.warning("⚠️  [MCP] Nenhum agent_id ou instance_id fornecido")
            return None

        # URL do Gateway
        gateway_url = gateway_url or os.environ.get("GATEWAY_URL", "http://localhost:14199")

        # Montar query params
        params = []
        if agent_id:
            params.append(f"agent_id={agent_id}")
        if instance_id:
            params.append(f"instance_id={instance_id}")

        url = f"{gateway_url}/mcp/config?{'&'.join(params)}"
        logger.info(f"🔌 [MCP] Buscando config do Gateway: {url}")

        try:
            import requests
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"⚠️  [MCP] Gateway retornou {response.status_code}: {response.text}")
                return None

            mcp_config = response.json()

            # Verificar se há MCPs configurados
            if not mcp_config.get("mcpServers"):
                logger.info(f"📭 [MCP] Nenhum MCP configurado para agent={agent_id}, instance={instance_id}")
                return None

            # Criar arquivo temporário
            fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="mcp_gateway_config_")
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(mcp_config, f, indent=2)
                logger.info(f"📄 [MCP] Config do Gateway salva em {temp_path}")
                logger.info(f"📄 [MCP] MCPs: {list(mcp_config['mcpServers'].keys())}")
                return temp_path
            except Exception as e:
                logger.error(f"❌ [MCP] Erro ao criar arquivo de config: {e}")
                return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  [MCP] Erro ao conectar no Gateway: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ [MCP] Erro inesperado ao buscar config: {e}")
            return None

    def log_metrics(self):
        """Imprime métricas no log"""
        metrics = self.get_metrics()
        logger.info("=" * 80)
        logger.info("📊 MÉTRICAS DE PARALELIZAÇÃO")
        logger.info("=" * 80)
        logger.info(f"   Total de tasks processadas: {metrics['total_tasks_processed']}")
        logger.info(f"   Total de tasks com erro: {metrics['total_tasks_failed']}")
        logger.info(f"   Taxa de sucesso: {metrics['success_rate']:.1f}%")
        logger.info(f"   Tempo total de execução: {metrics['total_execution_time']:.2f}s")
        logger.info(f"   Tempo médio por task: {metrics['average_execution_time']:.2f}s")
        logger.info(f"   Tasks concorrentes agora: {metrics['concurrent_tasks_count']}")
        logger.info(f"   Pico de tasks simultâneas: {metrics['max_concurrent_tasks']}")
        logger.info(f"   Tasks por agente: {dict(metrics['tasks_by_agent'])}")
        if metrics['errors_by_agent']:
            logger.info(f"   Erros por agente: {dict(metrics['errors_by_agent'])}")
        logger.info("=" * 80)

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

    def update_agent_statistics(self, instance_id: str, duration_ms: float, exit_code: int) -> bool:
        """
        Atualiza as estatísticas de um agente via API do conductor-gateway

        Args:
            instance_id: ID da instância do agente
            duration_ms: Duração da execução em milissegundos
            exit_code: Código de saída (0 = sucesso, outro = erro)

        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        try:
            url = f"{self.gateway_url}/api/agents/instances/{instance_id}/statistics"
            payload = {
                "task_duration": duration_ms,
                "exit_code": exit_code,
                "increment_count": True
            }

            logger.info(f"📊 [STATISTICS] Atualizando estatísticas via API:")
            logger.info(f"   - URL: {url}")
            logger.info(f"   - Instance ID: {instance_id}")
            logger.info(f"   - Duration: {duration_ms}ms")
            logger.info(f"   - Exit Code: {exit_code}")

            response = requests.patch(url, json=payload, timeout=5)

            if response.status_code == 200:
                response_data = response.json()
                stats = response_data.get("statistics", {})
                logger.info(f"✅ [STATISTICS] Estatísticas atualizadas com sucesso:")
                logger.info(f"   - Task Count: {stats.get('task_count', 'N/A')}")
                logger.info(f"   - Total Time: {stats.get('total_execution_time', 'N/A')}ms")
                logger.info(f"   - Average Time: {stats.get('average_execution_time', 'N/A'):.2f}ms")
                logger.info(f"   - Success Rate: {stats.get('success_rate', 'N/A'):.1f}%")
                return True
            elif response.status_code == 404:
                logger.warning(f"⚠️ [STATISTICS] Instância não encontrada: {instance_id}")
                return False
            else:
                logger.error(f"❌ [STATISTICS] Erro ao atualizar estatísticas:")
                logger.error(f"   - Status Code: {response.status_code}")
                logger.error(f"   - Response: {response.text[:500]}")
                return False

        except requests.exceptions.Timeout:
            logger.error(f"⏰ [STATISTICS] Timeout ao atualizar estatísticas para {instance_id}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 [STATISTICS] Erro de conexão com gateway: {self.gateway_url}")
            logger.error(f"   - Verifique se o conductor-gateway está rodando")
            return False
        except Exception as e:
            logger.error(f"❌ [STATISTICS] Erro inesperado ao atualizar estatísticas: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def execute_llm_request(self, provider: str, prompt: str, cwd: str,
                              timeout: int = 1800,
                              mcp_configs: List[str] = None,
                              agent_id: str = None,
                              instance_id: str = None) -> tuple[str, int, float]:
        """
        Executar request para LLM (Claude, Gemini ou Cursor-Agent) baseado no provider.

        Args:
            provider: "claude", "gemini" ou "cursor-agent"
            prompt: Prompt XML completo já formatado
            cwd: Diretório de trabalho
            timeout: Timeout em segundos
            mcp_configs: Lista de nomes de MCP para configurar (ex: ["prospector", "database"])
            agent_id: ID do agente (para lógica específica de MCPs)
            instance_id: ID da instância do agente (para MCP config do Gateway)

        Returns:
            tuple: (result, exit_code, duration)
        """
        start_time = time.time()
        mcp_config_path = None  # Track temp file for cleanup

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
            logger.info(f"   agent_id: {agent_id}")
            logger.info(f"   provider: {provider}")
            logger.info(f"   mcp_configs: {mcp_configs}")

            # Verificar se cursor-agent existe no PATH
            import shutil
            cursor_path = shutil.which("cursor-agent")
            logger.info(f"   cursor-agent path: {cursor_path if cursor_path else '❌ NÃO ENCONTRADO'}")

            # Buscar MCP config do Gateway Registry
            mcp_config_path = None
            if provider == "claude":
                mcp_config_path = self.fetch_mcp_config_from_gateway(
                    agent_id=agent_id,
                    instance_id=instance_id
                )

            # Montar comando baseado no provider
            if provider == "claude":
                command = ["claude", "--print", "--dangerously-skip-permissions"]

                # Usar MCP config do Gateway se disponível
                if mcp_config_path:
                    command.extend(["--mcp-config", mcp_config_path])
                    logger.info(f"🔌 [MCP] Claude CLI receberá --mcp-config {mcp_config_path}")
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

        finally:
            # Cleanup: remover arquivo temporário de config MCP
            if mcp_config_path and os.path.exists(mcp_config_path):
                try:
                    os.unlink(mcp_config_path)
                    logger.debug(f"🧹 [MCP] Arquivo temporário removido: {mcp_config_path}")
                except Exception as cleanup_err:
                    logger.warning(f"⚠️  [MCP] Falha ao remover arquivo temporário: {cleanup_err}")

    def _process_request_wrapper(self, request: Dict):
        """
        Wrapper para processar task com controle de agente e métricas
        Executado dentro de uma thread do ThreadPoolExecutor
        """
        agent_id = request.get("agent_id", "unknown")
        thread_name = threading.current_thread().name

        try:
            # Marcar agente como processando
            self._mark_agent_processing(agent_id)
            logger.info(f"🚀 [{thread_name}] Iniciando processamento da task do agente {agent_id}")

            # Processar a task
            success = self.process_request(request)

            return success

        except Exception as e:
            logger.error(f"❌ [{thread_name}] Erro ao processar task: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

        finally:
            # Desmarcar agente
            self._unmark_agent_processing(agent_id)
            logger.info(f"🏁 [{thread_name}] Finalizou processamento do agente {agent_id}")

    def process_request(self, request: Dict) -> bool:
        """Processar uma task individual"""
        request_id = request["_id"]
        agent_id = request.get("agent_id", "unknown")
        thread_name = threading.current_thread().name

        # ========================================================================
        # 🔍 PROVA EXPLÍCITA: Lendo instance_id da task
        # ========================================================================
        logger.info(f"🔍 [{thread_name}] [DEBUG] Lendo campos da task do MongoDB:")
        logger.info(f"   - Task _id: {request_id}")
        logger.info(f"   - Chaves disponíveis na task: {list(request.keys())}")
        logger.info(f"   - Campo 'instance_id' existe? {'instance_id' in request}")

        instance_id = request.get("instance_id")  # ID da instância do agente

        logger.info(f"   - instance_id LIDO: {repr(instance_id)}")
        logger.info(f"   - instance_id TIPO: {type(instance_id)}")
        logger.info(f"   - instance_id é None? {instance_id is None}")
        logger.info(f"   - instance_id é truthy? {bool(instance_id)}")
        logger.info("========================================================================")
        # ========================================================================

        provider = request.get("provider", "claude")
        cwd = request.get("cwd", ".")
        timeout = request.get("timeout", 1800)  # ✅ Alinhado com default da API (1800s = 30 minutos)
        mcp_configs = request.get("mcp_configs", [])  # Lista de MCPs (ex: ["prospector", "database"])

        # Buscar campo 'prompt' com XML completo
        prompt = request.get("prompt", "")

        if not prompt:
            logger.error(f"❌ [{thread_name}] Task {request_id} não possui campo 'prompt'")
            self.complete_request(request_id, "Erro: campo 'prompt' obrigatório não encontrado", 1, 0.0)
            self._update_metrics(agent_id, False, 0.0)
            return False

        logger.info("=" * 80)
        logger.info(f"📨 [{thread_name}] PROCESSANDO NOVA TASK")
        logger.info(f"   ID: {request_id}")
        logger.info(f"   Agent ID: {agent_id}")
        logger.info(f"   Instance ID: {instance_id}")
        logger.info(f"   Provider: {provider}")
        logger.info(f"   CWD: {cwd}")
        logger.info(f"   Timeout: {timeout}s")
        logger.info(f"   MCP Configs: {mcp_configs}")
        logger.info(f"   Prompt length: {len(prompt)} chars")
        logger.info("=" * 80)

        # ========================================================================
        # 🔌 MCP ON-DEMAND: Garantir que MCPs necessários estão rodando
        # ========================================================================
        if self.mcp_service:
            try:
                logger.info(f"🔌 [{thread_name}] Verificando MCPs on-demand para agente '{agent_id}'...")
                if not self.mcp_service.ensure_mcps_for_agent(agent_id, instance_id, timeout=60):
                    error_msg = f"Falha ao iniciar MCPs necessários para agente '{agent_id}'"
                    logger.error(f"❌ [{thread_name}] {error_msg}")
                    self.complete_request(request_id, error_msg, 1, 0.0)
                    self._update_metrics(agent_id, False, 0.0)

                    # Emitir evento de erro
                    request["status"] = "error"
                    request["result"] = error_msg
                    self.emit_task_event("task_error", request)
                    return False
                logger.info(f"✅ [{thread_name}] MCPs on-demand verificados/iniciados com sucesso")
            except Exception as e:
                error_msg = f"Erro ao verificar MCPs on-demand: {e}"
                logger.error(f"❌ [{thread_name}] {error_msg}")
                self.complete_request(request_id, error_msg, 1, 0.0)
                self._update_metrics(agent_id, False, 0.0)

                # Emitir evento de erro
                request["status"] = "error"
                request["result"] = error_msg
                self.emit_task_event("task_error", request)
                return False
        else:
            logger.debug(f"⏭️  [{thread_name}] MCP on-demand desabilitado, pulando verificação")
        # ========================================================================

        # Marcar como processando no MongoDB
        if not self.mark_as_processing(request_id):
            logger.warning(f"⚠️  [{thread_name}] Task {request_id} já está sendo processada")
            return False

        # 📡 Emitir evento task_picked (watcher pegou o job da fila)
        request["status"] = "processing"
        self.emit_task_event("task_picked", request)

        # Executar LLM request
        result, exit_code, duration = self.execute_llm_request(
            provider=provider,
            prompt=prompt,
            cwd=cwd,
            timeout=timeout,
            mcp_configs=mcp_configs,
            agent_id=agent_id,
            instance_id=instance_id
        )

        # Salvar resultado
        success = self.complete_request(request_id, result, exit_code, duration)

        # Atualizar métricas
        self._update_metrics(agent_id, success and exit_code == 0, duration)

        logger.info("=" * 80)
        if success:
            status_emoji = "✅" if exit_code == 0 else "❌"
            logger.info(f"{status_emoji} [{thread_name}] TASK COMPLETADA E SALVA NO MONGODB")
            logger.info(f"   ID: {request_id}")
            logger.info(f"   Agent ID: {agent_id}")
            logger.info(f"   Instance ID: {instance_id}")
            logger.info(f"   Exit code: {exit_code}")
            logger.info(f"   Duração: {duration:.2f}s")
            logger.info(f"   Resultado length: {len(result)} chars")

            # Atualizar estatísticas do agente via API
            if instance_id:
                duration_ms = duration * 1000  # Converter segundos para milissegundos
                stats_updated = self.update_agent_statistics(instance_id, duration_ms, exit_code)
                if stats_updated:
                    logger.info(f"📊 [{thread_name}] Estatísticas do agente atualizadas com sucesso")
                else:
                    logger.warning(f"⚠️  [{thread_name}] Falha ao atualizar estatísticas do agente (não-crítico)")
            else:
                logger.warning(f"⚠️  [{thread_name}] Task não possui instance_id, estatísticas não serão atualizadas")

            # 📡 Emitir evento task_completed ou task_error
            request["status"] = "completed" if exit_code == 0 else "error"
            request["result"] = result
            request["duration"] = duration
            request["exit_code"] = exit_code
            event_type = "task_completed" if exit_code == 0 else "task_error"
            self.emit_task_event(event_type, request)

        else:
            logger.error(f"❌ [{thread_name}] FALHA AO SALVAR RESULTADO NO MONGODB")
            logger.error(f"   ID: {request_id}")
            logger.error(f"   Agent ID: {agent_id}")
            logger.error(f"   Instance ID: {instance_id}")

            # 📡 Emitir evento task_error mesmo quando falha salvar
            request["status"] = "error"
            request["result"] = "Falha ao salvar resultado no MongoDB"
            self.emit_task_event("task_error", request)

        logger.info("=" * 80)

        return success

    def run(self, poll_interval: float = 1.0, metrics_interval: int = 60):
        """
        Loop principal do watcher com suporte a paralelização

        Args:
            poll_interval: Intervalo entre verificações em segundos
            metrics_interval: Intervalo para imprimir métricas em segundos
        """
        logger.info("=" * 80)
        logger.info("🚀 UNIVERSAL TASK WATCHER INICIADO (VERSÃO PARALELIZADA)")
        logger.info("=" * 80)
        logger.info(f"🔍 Monitorando collection: {self.database_name}.{self.collection_name}")
        logger.info(f"⏱️  Poll interval: {poll_interval}s")
        logger.info(f"🎯 Suporte: Claude, Gemini, Cursor-Agent")
        logger.info(f"🔧 Max workers: {self.max_workers}")
        logger.info(f"📊 Modo FIFO: {self.fifo_mode}")
        logger.info(f"📈 Métricas a cada: {metrics_interval}s")
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

        last_metrics_time = time.time()

        try:
            while not self.shutdown_requested:
                try:
                    # Buscar tasks pendentes
                    requests = self.get_pending_requests()

                    if requests:
                        logger.info(f"📋 Encontradas {len(requests)} tasks pendentes")

                        # Submeter tasks para processamento paralelo
                        for request in requests:
                            agent_id = request.get("agent_id", "unknown")

                            # FIFO DESABILITADO - Sem verificação de agente processando
                            # TODO: Reimplementar com FIFO por agent_id + cwd
                            # if not self._can_process_agent(agent_id):
                            #     logger.info(f"⏸️  Agente {agent_id} já está processando, aguardando...")
                            #     continue

                            # Verificar se há workers disponíveis
                            with self.futures_lock:
                                # Limpar futures completadas
                                self.active_futures = {f for f in self.active_futures if not f.done()}

                                if len(self.active_futures) >= self.max_workers:
                                    logger.info(f"⏸️  Máximo de {self.max_workers} workers atingido, aguardando...")
                                    break

                                # Submeter task para processamento
                                future = self.executor.submit(self._process_request_wrapper, request)
                                self.active_futures.add(future)

                            logger.info(f"✅ Task submetida para processamento (workers ativos: {len(self.active_futures)}/{self.max_workers})")

                    # Limpar futures completadas periodicamente
                    with self.futures_lock:
                        completed = [f for f in self.active_futures if f.done()]
                        if completed:
                            for future in completed:
                                try:
                                    future.result()  # Verificar exceções
                                except Exception as e:
                                    logger.error(f"❌ Erro em future: {e}")
                        self.active_futures = {f for f in self.active_futures if not f.done()}

                    # Imprimir métricas periodicamente
                    current_time = time.time()
                    if current_time - last_metrics_time >= metrics_interval:
                        self.log_metrics()
                        last_metrics_time = current_time

                    # Aguardar próximo ciclo
                    time.sleep(poll_interval)

                except KeyboardInterrupt:
                    logger.info("🛑 Shutdown solicitado pelo usuário (Ctrl+C)")
                    self.shutdown_requested = True
                    break
                except Exception as e:
                    logger.error(f"❌ Erro no loop principal: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    time.sleep(5)  # Aguardar mais tempo em caso de erro

        finally:
            # Graceful shutdown
            logger.info("=" * 80)
            logger.info("🛑 INICIANDO GRACEFUL SHUTDOWN")
            logger.info("=" * 80)

            # Aguardar tasks em execução
            with self.futures_lock:
                if self.active_futures:
                    logger.info(f"⏳ Aguardando {len(self.active_futures)} tasks em execução...")
                    for future in self.active_futures:
                        try:
                            future.result(timeout=30)  # Aguardar até 30s por task
                        except Exception as e:
                            logger.error(f"❌ Erro ao aguardar future: {e}")

            # Shutdown do executor
            logger.info("🔄 Finalizando ThreadPoolExecutor...")
            self.executor.shutdown(wait=True, cancel_futures=False)

            # Fechar conexão MongoDB
            logger.info("🔌 Fechando conexão MongoDB...")
            self.client.close()

            # Imprimir métricas finais
            logger.info("")
            logger.info("📊 MÉTRICAS FINAIS:")
            self.log_metrics()

            logger.info("=" * 80)
            logger.info("👋 Universal Task Watcher finalizado com sucesso")
            logger.info("=" * 80)

def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Universal MongoDB Watcher - Suporta Claude, Gemini e Cursor-Agent (VERSÃO PARALELIZADA)"
    )
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017",
                       help="URI de conexão MongoDB")
    parser.add_argument("--database", default="conductor_state",
                       help="Nome do database")
    parser.add_argument("--collection", default="tasks",
                       help="Nome da collection")
    parser.add_argument("--gateway-url", default="http://localhost:5006",
                       help="URL do conductor-gateway para atualização de estatísticas (padrão: porta 5006 do Docker)")
    parser.add_argument("--poll-interval", type=float, default=1.0,
                       help="Intervalo entre verificações em segundos (padrão: 1.0)")
    parser.add_argument("--max-workers", type=int, default=5,
                       help="Número máximo de workers paralelos (padrão: 5)")
    parser.add_argument("--fifo-mode", choices=["strict", "per_agent", "relaxed"], default="per_agent",
                       help="Modo FIFO: strict (uma task total), per_agent (FIFO por agente), relaxed (sem FIFO)")
    parser.add_argument("--metrics-interval", type=int, default=60,
                       help="Intervalo para imprimir métricas em segundos (padrão: 60)")

    args = parser.parse_args()

    try:
        watcher = UniversalMongoWatcher(
            mongo_uri=args.mongo_uri,
            database=args.database,
            collection=args.collection,
            gateway_url=args.gateway_url,
            max_workers=args.max_workers,
            fifo_mode=args.fifo_mode
        )

        watcher.run(
            poll_interval=args.poll_interval,
            metrics_interval=args.metrics_interval
        )

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()