# src/api/routes/templates.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/templates", tags=["Templates"])


class TemplateInstallRequest(BaseModel):
    template_name: str = None


@router.get("/", summary="Listar templates disponíveis")
def list_available_templates():
    """
    Lista todos os templates de agentes disponíveis para instalação.
    """
    try:
        # Para este MVP, retornamos uma lista simulada
        templates = [
            {
                "name": "basic-agent",
                "description": "Template básico para criação de agentes",
                "version": "1.0.0",
                "author": "Conductor Team"
            },
            {
                "name": "code-reviewer",
                "description": "Template para agente revisor de código",
                "version": "1.0.0",
                "author": "Conductor Team"
            },
            {
                "name": "documentation-writer",
                "description": "Template para agente escritor de documentação",
                "version": "1.0.0",
                "author": "Conductor Team"
            }
        ]

        return {
            "total": len(templates),
            "templates": templates
        }

    except Exception as e:
        logger.error(f"Erro ao listar templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/install", summary="Instalar template de agente")
def install_agent_templates(request: TemplateInstallRequest = None):
    """
    Instala um template de agente específico ou lista templates disponíveis.
    """
    try:
        if not request or not request.template_name:
            # Se não especificou template, retorna lista disponível
            return list_available_templates()

        # Para este MVP, simulamos a instalação
        return {
            "status": "success",
            "template_name": request.template_name,
            "message": f"Template '{request.template_name}' instalado com sucesso",
            "installed_path": f".conductor_workspace/agents/{request.template_name}",
            "files_created": [
                f"{request.template_name}.yaml",
                f"{request.template_name}/prompt.md",
                f"{request.template_name}/config.json"
            ]
        }

    except Exception as e:
        logger.error(f"Erro ao instalar template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))