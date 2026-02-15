# src/api/routes/navigation.py
"""
Navigation State API - Persiste estado de navegação do usuário no MongoDB.

MODELO DE DADOS:
- Dois níveis de estado:
  1. Estado do ROTEIRO: user_id + screenplay_id → conversation_id (última conversa ativa)
  2. Estado da CONVERSA: user_id + screenplay_id + conversation_id → instance_id (último agente ativo)

Isso permite:
- Ao trocar de roteiro A → B, recuperar a última conversa do roteiro B
- Ao trocar de conversa X → Y → X, recuperar o último agente da conversa X
"""
from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from pymongo import MongoClient, ASCENDING
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/navigation", tags=["Navigation"])


class NavigationState(BaseModel):
    """Estado de navegação completo."""
    screenplay_id: str  # Obrigatório
    conversation_id: Optional[str] = None
    instance_id: Optional[str] = None


class NavigationStateResponse(BaseModel):
    """Resposta com estado de navegação."""
    screenplay_id: Optional[str] = None
    conversation_id: Optional[str] = None
    instance_id: Optional[str] = None
    updated_at: Optional[datetime] = None


class LastScreenplayResponse(BaseModel):
    """Resposta com último roteiro acessado."""
    screenplay_id: Optional[str] = None
    conversation_id: Optional[str] = None
    updated_at: Optional[datetime] = None


_mongo_client = None
_screenplay_states = None  # user_id + screenplay_id → conversation_id
_conversation_states = None  # user_id + screenplay_id + conversation_id → instance_id

def get_mongo_collections():
    """Obtém as collections do MongoDB para navigation states."""
    global _mongo_client, _screenplay_states, _conversation_states

    if _screenplay_states is not None:
        return _screenplay_states, _conversation_states

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/conductor_state?authSource=admin")
    _mongo_client = MongoClient(mongo_uri)
    db = _mongo_client.conductor_state

    # Collection para estado do roteiro (última conversa)
    _screenplay_states = db.screenplay_states
    _screenplay_states.create_index(
        [("user_id", ASCENDING), ("screenplay_id", ASCENDING)],
        unique=True,
        name="user_screenplay_unique"
    )
    _screenplay_states.create_index(
        [("user_id", ASCENDING), ("updated_at", ASCENDING)],
        name="user_last_accessed"
    )

    # Collection para estado da conversa (último agente)
    _conversation_states = db.conversation_states
    _conversation_states.create_index(
        [("user_id", ASCENDING), ("screenplay_id", ASCENDING), ("conversation_id", ASCENDING)],
        unique=True,
        name="user_screenplay_conversation_unique"
    )

    logger.info("[NAVIGATION] MongoDB collections initialized with indexes")
    return _screenplay_states, _conversation_states


def get_user_id(x_user_id: Optional[str] = None, x_session_id: Optional[str] = None) -> str:
    """
    Obtém o identificador do usuário.
    Prioridade: x_user_id > x_session_id > 'default'
    """
    if x_user_id:
        return x_user_id
    if x_session_id:
        return f"session_{x_session_id}"
    return "default"


@router.get("", response_model=NavigationStateResponse, summary="Obter estado de navegação")
def get_navigation_state(
    screenplay_id: Optional[str] = Query(None, description="ID do roteiro"),
    conversation_id: Optional[str] = Query(None, description="ID da conversa"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """
    Retorna o estado de navegação.

    Casos:
    1. screenplay_id + conversation_id → retorna instance_id da conversa
    2. screenplay_id → retorna conversation_id + instance_id do roteiro
    3. Nenhum → retorna último roteiro acessado com seu estado
    """
    try:
        user_id = get_user_id(x_user_id, x_session_id)
        screenplay_states, conversation_states = get_mongo_collections()

        # Caso 1: Buscar instance_id de uma conversa específica
        if screenplay_id and conversation_id:
            conv_state = conversation_states.find_one({
                "user_id": user_id,
                "screenplay_id": screenplay_id,
                "conversation_id": conversation_id
            })

            instance_id = conv_state.get("instance_id") if conv_state else None

            logger.info(f"[NAVIGATION] Estado conversa: user={user_id}, screenplay={screenplay_id}, conversation={conversation_id}, instance={instance_id}")

            return NavigationStateResponse(
                screenplay_id=screenplay_id,
                conversation_id=conversation_id,
                instance_id=instance_id,
                updated_at=conv_state.get("updated_at") if conv_state else None
            )

        # Caso 2: Buscar conversation_id de um roteiro específico
        if screenplay_id:
            sp_state = screenplay_states.find_one({
                "user_id": user_id,
                "screenplay_id": screenplay_id
            })

            if not sp_state:
                logger.info(f"[NAVIGATION] Nenhum estado para roteiro: user={user_id}, screenplay={screenplay_id}")
                return NavigationStateResponse(screenplay_id=screenplay_id)

            conv_id = sp_state.get("conversation_id")
            instance_id = None

            # Se tem conversation_id, buscar instance_id
            if conv_id:
                conv_state = conversation_states.find_one({
                    "user_id": user_id,
                    "screenplay_id": screenplay_id,
                    "conversation_id": conv_id
                })
                instance_id = conv_state.get("instance_id") if conv_state else None

            logger.info(f"[NAVIGATION] Estado roteiro: user={user_id}, screenplay={screenplay_id}, conversation={conv_id}, instance={instance_id}")

            return NavigationStateResponse(
                screenplay_id=screenplay_id,
                conversation_id=conv_id,
                instance_id=instance_id,
                updated_at=sp_state.get("updated_at")
            )

        # Caso 3: Buscar último roteiro acessado
        sp_state = screenplay_states.find_one(
            {"user_id": user_id},
            sort=[("updated_at", -1)]
        )

        if not sp_state:
            logger.info(f"[NAVIGATION] Nenhum estado encontrado para user={user_id}")
            return NavigationStateResponse()

        sp_id = sp_state.get("screenplay_id")
        conv_id = sp_state.get("conversation_id")
        instance_id = None

        # Se tem conversation_id, buscar instance_id
        if conv_id:
            conv_state = conversation_states.find_one({
                "user_id": user_id,
                "screenplay_id": sp_id,
                "conversation_id": conv_id
            })
            instance_id = conv_state.get("instance_id") if conv_state else None

        logger.info(f"[NAVIGATION] Último estado: user={user_id}, screenplay={sp_id}, conversation={conv_id}, instance={instance_id}")

        return NavigationStateResponse(
            screenplay_id=sp_id,
            conversation_id=conv_id,
            instance_id=instance_id,
            updated_at=sp_state.get("updated_at")
        )

    except Exception as e:
        logger.error(f"[NAVIGATION] Erro ao obter estado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last", response_model=LastScreenplayResponse, summary="Obter último roteiro acessado")
def get_last_screenplay(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """
    Retorna o último roteiro acessado pelo usuário com sua última conversa.
    """
    try:
        user_id = get_user_id(x_user_id, x_session_id)
        screenplay_states, _ = get_mongo_collections()

        state = screenplay_states.find_one(
            {"user_id": user_id},
            sort=[("updated_at", -1)]
        )

        if not state:
            logger.info(f"[NAVIGATION] Nenhum roteiro encontrado para user={user_id}")
            return LastScreenplayResponse()

        logger.info(f"[NAVIGATION] Último roteiro: user={user_id}, screenplay={state.get('screenplay_id')}, conversation={state.get('conversation_id')}")

        return LastScreenplayResponse(
            screenplay_id=state.get("screenplay_id"),
            conversation_id=state.get("conversation_id"),
            updated_at=state.get("updated_at")
        )

    except Exception as e:
        logger.error(f"[NAVIGATION] Erro ao obter último roteiro: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", response_model=NavigationStateResponse, summary="Salvar estado de navegação")
def save_navigation_state(
    state: NavigationState,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """
    Salva o estado de navegação.

    - Sempre salva screenplay_id + conversation_id na collection screenplay_states
    - Se conversation_id fornecido, salva instance_id na collection conversation_states
    """
    try:
        if not state.screenplay_id:
            raise HTTPException(status_code=400, detail="screenplay_id é obrigatório")

        user_id = get_user_id(x_user_id, x_session_id)
        screenplay_states, conversation_states = get_mongo_collections()

        now = datetime.utcnow()

        # 1. Salvar estado do roteiro (última conversa)
        screenplay_states.update_one(
            {
                "user_id": user_id,
                "screenplay_id": state.screenplay_id
            },
            {
                "$set": {
                    "conversation_id": state.conversation_id,
                    "updated_at": now
                },
                "$setOnInsert": {
                    "created_at": now
                }
            },
            upsert=True
        )

        # 2. Se tem conversation_id, salvar estado da conversa (último agente)
        if state.conversation_id:
            conversation_states.update_one(
                {
                    "user_id": user_id,
                    "screenplay_id": state.screenplay_id,
                    "conversation_id": state.conversation_id
                },
                {
                    "$set": {
                        "instance_id": state.instance_id,
                        "updated_at": now
                    },
                    "$setOnInsert": {
                        "created_at": now
                    }
                },
                upsert=True
            )

        logger.info(f"[NAVIGATION] Estado salvo: user={user_id}, screenplay={state.screenplay_id}, conversation={state.conversation_id}, instance={state.instance_id}")

        return NavigationStateResponse(
            screenplay_id=state.screenplay_id,
            conversation_id=state.conversation_id,
            instance_id=state.instance_id,
            updated_at=now
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NAVIGATION] Erro ao salvar estado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("", summary="Limpar estado de navegação")
def clear_navigation_state(
    screenplay_id: Optional[str] = Query(None, description="ID do roteiro"),
    conversation_id: Optional[str] = Query(None, description="ID da conversa"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """
    Limpa o estado de navegação.

    - screenplay_id + conversation_id: limpa estado da conversa
    - screenplay_id: limpa estado do roteiro e todas suas conversas
    - Nenhum: limpa todos os estados do usuário
    """
    try:
        user_id = get_user_id(x_user_id, x_session_id)
        screenplay_states, conversation_states = get_mongo_collections()

        deleted_count = 0

        if screenplay_id and conversation_id:
            # Limpar apenas estado da conversa
            result = conversation_states.delete_one({
                "user_id": user_id,
                "screenplay_id": screenplay_id,
                "conversation_id": conversation_id
            })
            deleted_count = result.deleted_count
            logger.info(f"[NAVIGATION] Estado conversa removido: user={user_id}, screenplay={screenplay_id}, conversation={conversation_id}")

        elif screenplay_id:
            # Limpar estado do roteiro e todas suas conversas
            r1 = screenplay_states.delete_one({
                "user_id": user_id,
                "screenplay_id": screenplay_id
            })
            r2 = conversation_states.delete_many({
                "user_id": user_id,
                "screenplay_id": screenplay_id
            })
            deleted_count = r1.deleted_count + r2.deleted_count
            logger.info(f"[NAVIGATION] Estado roteiro removido: user={user_id}, screenplay={screenplay_id}, deleted={deleted_count}")

        else:
            # Limpar todos os estados do usuário
            r1 = screenplay_states.delete_many({"user_id": user_id})
            r2 = conversation_states.delete_many({"user_id": user_id})
            deleted_count = r1.deleted_count + r2.deleted_count
            logger.info(f"[NAVIGATION] Todos estados removidos: user={user_id}, deleted={deleted_count}")

        return {
            "status": "success",
            "message": "Estado de navegação removido",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"[NAVIGATION] Erro ao remover estado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
