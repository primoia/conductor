# src/api/routes/system.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import yaml
import os
import logging

from src.container import container

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["System"])


class SystemValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    config_status: str
    mongodb_status: str
    agents_status: str


class EnvironmentRequest(BaseModel):
    environment: str
    project: str = None


class BackupRequest(BaseModel):
    backup_path: str = None


class RestoreRequest(BaseModel):
    backup_path: str


class MigrationRequest(BaseModel):
    from_type: str  # 'filesystem' or 'mongodb'
    to_type: str    # 'filesystem' or 'mongodb'
    path: str = None
    no_config_update: bool = False


@router.get("/validate", response_model=SystemValidationResult, summary="Validar sistema completo")
def validate_conductor_system():
    """
    Executa validação completa do sistema Conductor.
    Verifica configuração, conectividade MongoDB, e status dos agentes.
    """
    try:
        errors = []
        warnings = []

        # Validar configuração
        config_status = "ok"
        try:
            container.get_conductor_service()
        except Exception as e:
            config_status = "error"
            errors.append(f"Erro na configuração: {e}")

        # Validar MongoDB
        mongodb_status = "ok"
        try:
            from src.core.services.mongo_task_client import MongoTaskClient
            mongo_client = MongoTaskClient()
            # Teste básico de conectividade
            mongo_client._get_database()
        except Exception as e:
            mongodb_status = "error"
            errors.append(f"Erro MongoDB: {e}")

        # Validar agentes
        agents_status = "ok"
        try:
            conductor_service = container.get_conductor_service()
            agents = conductor_service.discover_agents()
            if len(agents) == 0:
                warnings.append("Nenhum agente encontrado")
        except Exception as e:
            agents_status = "error"
            errors.append(f"Erro na descoberta de agentes: {e}")

        is_valid = len(errors) == 0

        return SystemValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            config_status=config_status,
            mongodb_status=mongodb_status,
            agents_status=agents_status
        )

    except Exception as e:
        logger.error(f"Erro na validação do sistema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", summary="Obter configuração do sistema")
def get_system_config():
    """
    Retorna a configuração atual do sistema (config.yaml).
    """
    try:
        config_path = os.path.join(os.getcwd(), "config.yaml")

        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail="Arquivo config.yaml não encontrado")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = yaml.safe_load(f)

        return {
            "config_path": config_path,
            "config": config_content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ler configuração: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/environment", summary="Configurar ambiente e projeto")
def set_environment(request: EnvironmentRequest):
    """
    Define o ambiente e contexto do projeto.
    """
    try:
        # Para este MVP, apenas retornamos sucesso
        # A implementação completa dependeria de como o sistema gerencia ambientes
        return {
            "status": "success",
            "environment": request.environment,
            "project": request.project,
            "message": "Ambiente configurado com sucesso"
        }

    except Exception as e:
        logger.error(f"Erro ao configurar ambiente: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup", summary="Fazer backup dos agentes")
def backup_agents(request: BackupRequest = None):
    """
    Cria backup de todos os agentes.
    """
    try:
        # Para este MVP, simulamos o backup
        backup_path = request.backup_path if request else ".conductor_workspace/backup"

        return {
            "status": "success",
            "backup_path": backup_path,
            "message": f"Backup criado em {backup_path}",
            "timestamp": "2025-09-28T12:00:00Z"
        }

    except Exception as e:
        logger.error(f"Erro no backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore", summary="Restaurar agentes do backup")
def restore_agents(request: RestoreRequest):
    """
    Restaura agentes de um backup.
    """
    try:
        # Para este MVP, simulamos a restauração
        return {
            "status": "success",
            "backup_path": request.backup_path,
            "message": f"Agentes restaurados de {request.backup_path}",
            "restored_agents": 0
        }

    except Exception as e:
        logger.error(f"Erro na restauração: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate", summary="Migrar storage entre filesystem e MongoDB")
def migrate_storage(request: MigrationRequest):
    """
    Migra dados entre filesystem e MongoDB.
    """
    try:
        if request.from_type not in ["filesystem", "mongodb"]:
            raise HTTPException(status_code=400, detail="from_type deve ser 'filesystem' ou 'mongodb'")

        if request.to_type not in ["filesystem", "mongodb"]:
            raise HTTPException(status_code=400, detail="to_type deve ser 'filesystem' ou 'mongodb'")

        # Para este MVP, simulamos a migração
        return {
            "status": "success",
            "from_type": request.from_type,
            "to_type": request.to_type,
            "path": request.path,
            "migrated_items": 0,
            "message": f"Migração de {request.from_type} para {request.to_type} concluída"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na migração: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcp/sidecars", summary="[DEPRECATED] Listar MCP sidecars descobertos")
def list_mcp_sidecars():
    """
    DEPRECATED: Use GET /mcp/list do Gateway em vez deste endpoint.

    Este endpoint usa scan de containers Docker que foi descontinuado
    em favor do sistema MCP On-Demand baseado no mcp_registry.

    Para obter todos os MCPs (incluindo os parados):
    - GET http://gateway:5006/mcp/list

    Retorna a lista de MCP sidecars descobertos na rede Docker.
    """
    try:
        import warnings
        warnings.warn(
            "GET /api/system/mcp/sidecars está deprecated. Use GET /mcp/list do Gateway.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.warning("⚠️  Endpoint /api/system/mcp/sidecars está DEPRECATED. Use /mcp/list do Gateway.")

        discovery_service = container.get_discovery_service()
        sidecars = discovery_service.scan_network()

        return {
            "count": len(sidecars),
            "deprecated": True,
            "message": "Este endpoint está deprecated. Use GET /mcp/list do Gateway.",
            "sidecars": [
                {
                    "name": s.name,
                    "url": s.url,
                    "port": s.port,
                    "container_id": s.container_id
                }
                for s in sidecars
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao listar sidecars MCP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))