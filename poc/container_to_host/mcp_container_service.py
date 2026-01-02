"""
MCP Container Service - Gerenciamento On-Demand de containers MCP.

Este serviço é responsável por:
1. Verificar se MCPs estão rodando (health check)
2. Iniciar MCPs parados (docker compose up)
3. Parar MCPs inativos (docker compose down)
4. Atualizar status no mcp_registry

Roda no host, tem acesso direto ao Docker.
"""

import os
import subprocess
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Set
from pymongo.database import Database
import requests

logger = logging.getLogger(__name__)

# Caminho base onde estão os docker-compose files
BASE_PATH = os.environ.get("PRIMOIA_BASE_PATH", "/mnt/ramdisk/primoia-main/primoia")


class MCPContainerService:
    """
    Serviço para gerenciar ciclo de vida de containers MCP.
    Roda no host, tem acesso direto ao Docker.

    TODOS os MCPs são on-demand. Não há MCPs "sempre ligados".
    """

    def __init__(self, db: Database, default_shutdown_minutes: int = 30):
        """
        Inicializa o serviço.

        Args:
            db: Database MongoDB
            default_shutdown_minutes: Minutos padrão de inatividade antes de shutdown
        """
        self.db = db
        self.mcp_registry = db["mcp_registry"]
        self.agents = db["agents"]
        self.agent_instances = db["agent_instances"]
        self.default_shutdown_minutes = default_shutdown_minutes
        self.base_path = BASE_PATH

    def ensure_running(self, mcp_name: str, timeout: int = 60) -> bool:
        """
        Garante que um MCP está rodando. Fluxo completo:

        1. Busca MCP no mcp_registry
        2. Faz health check via host_url
        3. Se healthy → atualiza timestamps e retorna True
        4. Se não healthy → executa docker-compose up -d
        5. Aguarda health check passar (retry com timeout)
        6. Atualiza status para 'healthy' e timestamps
        7. Retorna True se conseguiu, False se timeout

        Args:
            mcp_name: Nome do MCP (ex: "crm", "billing")
            timeout: Timeout em segundos para aguardar startup

        Returns:
            bool: True se MCP está rodando, False se falhou
        """
        mcp = self.mcp_registry.find_one({"name": mcp_name})
        if not mcp:
            logger.error(f"MCP '{mcp_name}' não encontrado no mcp_registry")
            return False

        # 1. Verificar se já está healthy
        if self.health_check(mcp_name):
            logger.info(f"✅ MCP '{mcp_name}' já está healthy")
            self.update_timestamps(mcp_name)
            return True

        # 2. Precisa iniciar - atualizar status para 'starting'
        logger.info(f"🔄 MCP '{mcp_name}' não está healthy, iniciando...")
        self.mcp_registry.update_one(
            {"name": mcp_name},
            {"$set": {"status": "starting"}}
        )

        # 3. Executar docker-compose up
        if not self.start_container(mcp_name):
            logger.error(f"❌ Falha ao iniciar container para MCP '{mcp_name}'")
            self.mcp_registry.update_one(
                {"name": mcp_name},
                {"$set": {"status": "unhealthy"}}
            )
            return False

        # 4. Aguardar health check passar (retry)
        start_time = time.time()
        retry_count = 0
        while time.time() - start_time < timeout:
            retry_count += 1
            if self.health_check(mcp_name):
                logger.info(f"✅ MCP '{mcp_name}' iniciado com sucesso após {retry_count} tentativas")
                self.mcp_registry.update_one(
                    {"name": mcp_name},
                    {"$set": {"status": "healthy"}}
                )
                self.update_timestamps(mcp_name)
                return True
            logger.debug(f"⏳ Aguardando MCP '{mcp_name}' (tentativa {retry_count})...")
            time.sleep(2)  # Retry a cada 2 segundos

        # 5. Timeout - falhou
        logger.error(f"❌ Timeout aguardando MCP '{mcp_name}' ficar healthy após {timeout}s")
        self.mcp_registry.update_one(
            {"name": mcp_name},
            {"$set": {"status": "unhealthy"}}
        )
        return False

    def health_check(self, mcp_name: str) -> bool:
        """
        Verifica se MCP está respondendo via host_url.

        Usa host_url do registry (ex: http://localhost:13145/sse)
        e substitui /sse por /health para o check.

        Args:
            mcp_name: Nome do MCP

        Returns:
            bool: True se healthy, False caso contrário
        """
        mcp = self.mcp_registry.find_one({"name": mcp_name})
        if not mcp:
            logger.warning(f"MCP '{mcp_name}' não encontrado no registry")
            return False

        # Usar host_url (acessível do host onde Watcher roda)
        host_url = mcp.get("host_url")
        if not host_url:
            logger.warning(f"MCP '{mcp_name}' não tem host_url configurado")
            return False

        # Derivar URL de health do host_url
        health_url = host_url.replace("/sse", "/health")

        try:
            response = requests.get(health_url, timeout=5)
            is_healthy = response.status_code == 200
            if is_healthy:
                logger.debug(f"Health check OK para '{mcp_name}': {health_url}")
            return is_healthy
        except requests.exceptions.ConnectionError:
            logger.debug(f"Health check falhou para '{mcp_name}': Connection refused")
            return False
        except requests.exceptions.Timeout:
            logger.debug(f"Health check timeout para '{mcp_name}'")
            return False
        except requests.RequestException as e:
            logger.debug(f"Health check falhou para '{mcp_name}': {e}")
            return False

    def start_container(self, mcp_name: str) -> bool:
        """
        Inicia container via docker-compose up -d.

        Usa docker_compose_path do registry (caminho relativo ao BASE_PATH).

        Args:
            mcp_name: Nome do MCP

        Returns:
            bool: True se iniciou com sucesso, False caso contrário
        """
        mcp = self.mcp_registry.find_one({"name": mcp_name})
        if not mcp:
            return False

        compose_path = mcp.get("docker_compose_path")
        if not compose_path:
            logger.error(f"MCP '{mcp_name}' não tem docker_compose_path configurado")
            return False

        # Montar caminho absoluto
        full_path = os.path.join(self.base_path, compose_path)

        if not os.path.exists(full_path):
            logger.error(f"Arquivo não encontrado: {full_path}")
            return False

        try:
            logger.info(f"🚀 Iniciando MCP '{mcp_name}': docker compose -f {full_path} up -d")
            result = subprocess.run(
                ["docker", "compose", "-f", full_path, "up", "-d"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=os.path.dirname(full_path)  # Executar no diretório do compose
            )

            if result.returncode != 0:
                logger.error(f"docker compose up falhou para '{mcp_name}':\n{result.stderr}")
                return False

            logger.info(f"docker compose up OK para '{mcp_name}'")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout executando docker compose up para '{mcp_name}'")
            return False
        except FileNotFoundError:
            logger.error("docker não encontrado no PATH")
            return False
        except Exception as e:
            logger.error(f"Erro ao iniciar container '{mcp_name}': {e}")
            return False

    def stop_container(self, mcp_name: str) -> bool:
        """
        Para container via docker-compose down.

        Args:
            mcp_name: Nome do MCP

        Returns:
            bool: True se parou com sucesso, False caso contrário
        """
        mcp = self.mcp_registry.find_one({"name": mcp_name})
        if not mcp:
            return False

        compose_path = mcp.get("docker_compose_path")
        if not compose_path:
            logger.error(f"MCP '{mcp_name}' não tem docker_compose_path configurado")
            return False

        full_path = os.path.join(self.base_path, compose_path)

        if not os.path.exists(full_path):
            logger.error(f"Arquivo não encontrado: {full_path}")
            return False

        try:
            logger.info(f"⏹️ Parando MCP '{mcp_name}': docker compose -f {full_path} down")
            result = subprocess.run(
                ["docker", "compose", "-f", full_path, "down"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(full_path)
            )

            if result.returncode == 0:
                self.mcp_registry.update_one(
                    {"name": mcp_name},
                    {"$set": {"status": "stopped", "last_heartbeat": None}}
                )
                logger.info(f"✅ MCP '{mcp_name}' parado com sucesso")
                return True

            logger.error(f"docker compose down falhou para '{mcp_name}':\n{result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout executando docker compose down para '{mcp_name}'")
            return False
        except Exception as e:
            logger.error(f"Erro ao parar container '{mcp_name}': {e}")
            return False

    def update_timestamps(self, mcp_name: str):
        """
        Atualiza last_used e shutdown_after no registry.

        Args:
            mcp_name: Nome do MCP
        """
        mcp = self.mcp_registry.find_one({"name": mcp_name})
        if not mcp:
            return

        shutdown_minutes = mcp.get("auto_shutdown_minutes", self.default_shutdown_minutes)
        now = datetime.now(timezone.utc)
        shutdown_after = now + timedelta(minutes=shutdown_minutes)

        self.mcp_registry.update_one(
            {"name": mcp_name},
            {"$set": {
                "last_used": now,
                "shutdown_after": shutdown_after,
                "last_heartbeat": now
            }}
        )
        logger.debug(f"Timestamps atualizados para '{mcp_name}': shutdown_after={shutdown_after}")

    def get_mcps_for_agent(self, agent_id: str, instance_id: str = None) -> List[str]:
        """
        Retorna lista de MCPs necessários para um agente/instância.

        Combina:
        - agents.mcp_configs (do template)
        - agent_instances.mcp_configs (extras da instância)

        Args:
            agent_id: ID do agente
            instance_id: ID da instância (opcional)

        Returns:
            Lista de nomes de MCPs necessários
        """
        mcp_names: Set[str] = set()

        # 1. MCPs do template do agente
        agent = self.agents.find_one({"agent_id": agent_id})
        if agent:
            # Tentar buscar de definition.mcp_configs ou diretamente de mcp_configs
            definition = agent.get("definition", {})
            agent_mcps = definition.get("mcp_configs", []) or agent.get("mcp_configs", [])
            if agent_mcps:
                mcp_names.update(agent_mcps)
                logger.debug(f"MCPs do template '{agent_id}': {agent_mcps}")

        # 2. MCPs extras da instância
        if instance_id:
            instance = self.agent_instances.find_one({"instance_id": instance_id})
            if instance:
                instance_mcps = instance.get("mcp_configs", [])
                if instance_mcps:
                    mcp_names.update(instance_mcps)
                    logger.debug(f"MCPs extras da instância '{instance_id}': {instance_mcps}")

        return list(mcp_names)

    def ensure_mcps_for_agent(self, agent_id: str, instance_id: str = None, timeout: int = 60) -> bool:
        """
        Garante que todos os MCPs necessários para um agente estão rodando.

        Args:
            agent_id: ID do agente
            instance_id: ID da instância (opcional)
            timeout: Timeout por MCP em segundos

        Returns:
            bool: True se todos os MCPs estão rodando, False se algum falhou
        """
        required_mcps = self.get_mcps_for_agent(agent_id, instance_id)

        if not required_mcps:
            logger.debug(f"Nenhum MCP necessário para agente '{agent_id}'")
            return True

        logger.info(f"🔌 MCPs necessários para '{agent_id}': {required_mcps}")

        failed_mcps = []
        for mcp_name in required_mcps:
            if not self.ensure_running(mcp_name, timeout=timeout):
                failed_mcps.append(mcp_name)

        if failed_mcps:
            logger.error(f"❌ Falha ao iniciar MCPs: {failed_mcps}")
            return False

        logger.info(f"✅ Todos os {len(required_mcps)} MCPs estão rodando")
        return True

    def get_expired_mcps(self) -> List[Dict]:
        """
        Retorna MCPs que podem ser desligados (shutdown_after < now).
        Usado pelo Conselheiro Zelador.

        Returns:
            Lista de documentos de MCPs expirados
        """
        now = datetime.now(timezone.utc)
        expired = list(self.mcp_registry.find({
            "status": "healthy",
            "shutdown_after": {"$lt": now}
        }))
        logger.debug(f"MCPs expirados: {[m['name'] for m in expired]}")
        return expired

    def cleanup_expired_mcps(self) -> int:
        """
        Para todos os MCPs expirados.
        Usado pelo Conselheiro Zelador ou por um cron job.

        Returns:
            Número de MCPs desligados
        """
        expired = self.get_expired_mcps()
        stopped_count = 0

        for mcp in expired:
            mcp_name = mcp["name"]
            logger.info(f"🧹 Desligando MCP expirado: {mcp_name}")
            if self.stop_container(mcp_name):
                stopped_count += 1

        if stopped_count > 0:
            logger.info(f"🧹 {stopped_count} MCPs desligados pelo cleanup")

        return stopped_count

    def get_status_summary(self) -> Dict:
        """
        Retorna resumo do status de todos os MCPs.

        Returns:
            Dict com contagens por status
        """
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        results = list(self.mcp_registry.aggregate(pipeline))

        summary = {
            "total": 0,
            "healthy": 0,
            "stopped": 0,
            "starting": 0,
            "unhealthy": 0,
            "unknown": 0
        }

        for r in results:
            status = r["_id"] or "unknown"
            count = r["count"]
            summary["total"] += count
            if status in summary:
                summary[status] = count

        return summary
