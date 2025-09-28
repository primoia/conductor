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
    logger.warning(f"MongoDB client não disponível: {e}")
    MongoTaskClient = None

# Configura o logging e a aplicação FastAPI
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="Conductor API",
    description="API para interagir com o sistema de agentes do Conductor.",
    version="1.0.0"
)

class ExecuteRequest(BaseModel):
    user_input: str
    cwd: str = "/app"  # Diretório padrão dentro do contêiner, pode ser sobrescrito
    timeout: int = 300

@app.on_event("startup")
def startup_event():
    """Evento que roda na inicialização do servidor."""
    logger.info("🚀 Conductor API iniciando...")
    try:
        container.get_conductor_service()
        logger.info("✅ Container de dependências inicializado com sucesso.")
    except Exception as e:
        logger.critical(f"❌ Falha ao inicializar o container de dependências: {e}", exc_info=True)

@app.get("/agents", tags=["Agents"])
def list_available_agents():
    """Lista todos os agentes disponíveis no sistema."""
    try:
        logger.info("Recebida requisição para listar agentes em GET /agents")
        conductor_service = container.get_conductor_service()
        agents = conductor_service.discover_agents()

        agent_list = [{"id": agent.agent_id, "name": getattr(agent, 'name', 'N/A')} for agent in agents]
        logger.info(f"Encontrados {len(agent_list)} agentes.")
        return {"total": len(agent_list), "agents": agent_list}

    except Exception as e:
        logger.error(f"Erro ao listar agentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a lista de agentes: {e}")


@app.post("/agents/{agent_id}/execute", tags=["Agents"])
def execute_agent(agent_id: str, request: ExecuteRequest):
    """
    Executa um agente específico de forma assíncrona via MongoDB Task Queue.
    """
    if MongoTaskClient is None:
        raise HTTPException(status_code=503, detail="MongoDB client não está disponível")

    try:
        task_client = MongoTaskClient()

        # Constrói o comando dinamicamente
        command = ["claude", "run", agent_id, "-i", request.user_input]

        # O CWD deve ser o caminho no HOST, que o Watcher entende
        # O Gateway será responsável por fornecer este caminho.
        # Para este exemplo, vamos assumir que o request o contém.
        # Se o CWD não for fornecido, pode-se usar um padrão ou lançar um erro.

        logger.info(f"🚀 Submetendo tarefa para o agente '{agent_id}': {' '.join(command)}")
        task_id = task_client.submit_task(
            command=command,
            cwd=request.cwd,
            timeout=request.timeout
        )

        result_document = task_client.get_task_result(
            task_id=task_id,
            timeout=request.timeout + 10  # Timeout do polling um pouco maior
        )

        logger.info(f"✅ Tarefa concluída para agente '{agent_id}': {task_id}")
        return result_document

    except Exception as e:
        logger.error(f"❌ Erro na execução do agente '{agent_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
def health_check():
    """Endpoint de verificação de saúde."""
    return {"status": "ok"}