# projects/conductor/src/server.py
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
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


@app.post("/agents/execute-summary-via-mongo", tags=["Agents"])
def execute_summary_via_mongo():
    """
    Endpoint de teste que submete uma tarefa de resumo via MongoDB
    e aguarda o resultado via polling.
    """
    if MongoTaskClient is None:
        raise HTTPException(status_code=503, detail="MongoDB client não está disponível")

    try:
        task_client = MongoTaskClient()

        # Usando comando testado e bem-sucedido
        command = ["claude", "-p", "Resuma o arquivo README.md deste projeto em 3 frases."]
        cwd = "/mnt/ramdisk/develop/nex-web-backend"  # Usando o mesmo projeto do teste bem-sucedido

        logger.info(f"🚀 Submetendo tarefa MongoDB: {' '.join(command)}")

        # 1. Submete a tarefa
        task_id = task_client.submit_task(command=command, cwd=cwd)

        # 2. Aguarda o resultado
        result_document = task_client.get_task_result(task_id=task_id)

        logger.info(f"✅ Tarefa MongoDB concluída: {task_id}")
        return result_document

    except Exception as e:
        logger.error(f"❌ Erro no fluxo de execução via MongoDB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
def health_check():
    """Endpoint de verificação de saúde."""
    return {"status": "ok"}