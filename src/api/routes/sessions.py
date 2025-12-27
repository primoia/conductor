# src/api/routes/sessions.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import os

from src.container import container

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionStartRequest(BaseModel):
    agent_id: str
    initial_input: str = None
    timeout: int = 1800  # 30 minutes timeout for long-running operations


class ExecuteContextualRequest(BaseModel):
    agent_id: str
    input_text: str
    timeout: int = 1800  # 30 minutes timeout for long-running operations
    clear_history: bool = False


class ClearHistoryRequest(BaseModel):
    agent_id: str


class TemplateInstallRequest(BaseModel):
    template_name: str = None


@router.post("/start", summary="Iniciar sessão interativa com agente")
def start_interactive_session(request: SessionStartRequest):
    """
    Inicia uma sessão interativa com um agente específico.
    """
    try:
        # Para este MVP, simulamos o início da sessão
        session_id = f"session_{request.agent_id}_{hash(request.initial_input or '')}"

        return {
            "status": "success",
            "session_id": session_id,
            "agent_id": request.agent_id,
            "initial_input": request.initial_input,
            "timeout": request.timeout,
            "message": f"Sessão iniciada com agente {request.agent_id}"
        }

    except Exception as e:
        logger.error(f"Erro ao iniciar sessão: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# [LEGACY - COMMENTED OUT] Código legado que não está sendo usado
# Não há registros na coleção tasks vindos deste endpoint
# @router.post("/execute/contextual", summary="Executar agente com contexto de conversação")
# def execute_agent_contextual(request: ExecuteContextualRequest):
#     """
#     Executa um agente mantendo contexto de conversação anterior.
#     """
#     try:
#         # Para este MVP, reutilizamos a lógica de execução stateless
#         # mas indicamos que mantemos histórico
#         from src.core.services.mongo_task_client import MongoTaskClient
#
#         if MongoTaskClient is None:
#             raise HTTPException(status_code=503, detail="MongoDB client não está disponível")
#
#         task_client = MongoTaskClient()
#
#         # Montar comando baseado no input_text
#         command = ["claude", "-p", request.input_text]
#
#         # Se clear_history for True, adicionar flag
#         if request.clear_history:
#             command.extend(["--clear-history"])
#
#         # Submete a tarefa
#         task_id = task_client.submit_task(
#             agent_id=request.agent_id,
#             command=command,
#             cwd=os.getcwd(),  # Usar diretório atual
#             timeout=request.timeout
#         )
#
#         # Aguarda o resultado
#         result_document = task_client.get_task_result(task_id=task_id, timeout=request.timeout)
#
#         return {
#             "status": "success",
#             "agent_id": request.agent_id,
#             "contextual": True,
#             "cleared_history": request.clear_history,
#             "result": result_document
#         }
#
#     except Exception as e:
#         logger.error(f"Erro na execução contextual: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}/history", summary="Limpar histórico de conversação")
def clear_agent_history(agent_id: str):
    """
    Limpa o histórico de conversação de um agente específico.
    """
    try:
        # Para este MVP, simulamos a limpeza do histórico
        return {
            "status": "success",
            "agent_id": agent_id,
            "message": f"Histórico do agente {agent_id} limpo com sucesso",
            "cleared_items": 0
        }

    except Exception as e:
        logger.error(f"Erro ao limpar histórico: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))