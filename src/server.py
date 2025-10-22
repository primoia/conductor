# projects/conductor/src/server.py
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os

# Adiciona a raiz do projeto ao path para que os imports funcionem
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importa o container de injeção de dependência que já existe
from src.container import container

# Import do MongoDB client com tratamento de erro
try:
    from src.core.services.mongo_task_client import MongoTaskClient
except ImportError as e:
    MongoTaskClient = None

# Import das novas rotas modularizadas
from src.api.routes.agents import router as agents_router
from src.api.routes.system import router as system_router
from src.api.routes.sessions import router as sessions_router
from src.api.routes.templates import router as templates_router
from src.api.routes.conductor_cli import router as conductor_cli_router

# Configura o logging e a aplicação FastAPI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Conductor API",
    description="API para interagir com o sistema de agentes do Conductor.",
    version="1.0.0"
)

# Legacy ExecuteRequest model for compatibility
class ExecuteRequest(BaseModel):
    user_input: str
    cwd: str = "/app"
    timeout: int = 600  # 10 minutes timeout for long-running operations

# Incluir todos os roteadores
app.include_router(conductor_cli_router)  # API genérica primeira
app.include_router(agents_router)
app.include_router(system_router)
app.include_router(sessions_router)
app.include_router(templates_router)

@app.on_event("startup")
def startup_event():
    """Evento que roda na inicialização do servidor."""
    logger.info("🚀 Conductor API iniciando...")
    try:
        container.get_conductor_service()
        logger.info("✅ Container de dependências inicializado com sucesso.")
    except Exception as e:
        logger.critical(f"❌ Falha ao inicializar o container de dependências: {e}", exc_info=True)

# As rotas de agentes foram movidas para src/api/routes/agents.py

# [DEPRECATED - COMMENTED OUT] Legacy endpoint - Use /conductor/execute instead
# Este endpoint usa assinatura antiga de submit_task com parâmetro 'command' que não existe mais
# @app.post("/agents/{agent_id}/execute", tags=["Agents"])
# def execute_agent(agent_id: str, request: ExecuteRequest):
#     """
#     [DEPRECATED] Legacy endpoint for agent execution via MongoDB Task Queue.
#     Use the new generic /conductor/execute endpoint instead.
#     """
#     if MongoTaskClient is None:
#         raise HTTPException(status_code=503, detail="MongoDB client não está disponível")
#
#     try:
#         task_client = MongoTaskClient()
#
#         # Constrói o comando dinamicamente
#         command = ["claude", "run", agent_id, "-i", request.user_input]
#
#         # O CWD deve ser o caminho no HOST, que o Watcher entende
#         # O Gateway será responsável por fornecer este caminho.
#         # Para este exemplo, vamos assumir que o request o contém.
#         # Se o CWD não for fornecido, pode-se usar um padrão ou lançar um erro.
#
#         logger.info(f"🚀 Submetendo tarefa para o agente '{agent_id}': {' '.join(command)}")
#         task_id = task_client.submit_task(
#             agent_id=agent_id,
#             command=command,
#             cwd=request.cwd,
#             timeout=request.timeout
#         )
#
#         result_document = task_client.get_task_result(
#             task_id=task_id,
#             timeout=request.timeout + 10  # Timeout do polling um pouco maior
#         )
#
#         logger.info(f"✅ Tarefa concluída para agente '{agent_id}': {task_id}")
#         return result_document
#
#     except Exception as e:
#         logger.error(f"❌ Erro na execução do agente '{agent_id}': {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
def health_check():
    """Endpoint de verificação de saúde."""
    return {"status": "ok"}