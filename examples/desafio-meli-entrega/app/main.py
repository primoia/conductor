import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging_config import configure_logging
from app.api.v1 import items
from app.services.item_service import ItemNotFoundException

# Configura o sistema de logging
configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="Desafio Meli API")

# Inclui os routers da API
app.include_router(items.router, prefix="/api/v1")


@app.exception_handler(ItemNotFoundException)
async def item_not_found_exception_handler(request: Request, exc: ItemNotFoundException):
    """
    Handler para exceções de item não encontrado.
    
    Converte ItemNotFoundException em resposta HTTP 404.
    """
    logger.warning(f"Item not found: {exc.item_id}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"Item with ID '{exc.item_id}' not found"}
    )


logger.info("Desafio Meli API initialized")


@app.get("/", tags=["Health Check"])
def read_root():
    """
    Endpoint raiz para verificar a saúde da aplicação.
    """
    return {"message": "Hello, Architect! The foundation is solid."}
