# src/api/routes/conversations.py
"""
🔥 NOVO: Rotas de API para o modelo de conversas globais.

Endpoints para gerenciar conversas independentes de agentes específicos,
permitindo colaboração de múltiplos agentes em uma única linha de raciocínio.

Ref: PLANO_REFATORACAO_CONVERSATION_ID.md - Fase 1
Data: 2025-11-01
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from src.core.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Instanciar o serviço de conversas
conversation_service = ConversationService()


# ==========================================
# Modelos Pydantic (Request/Response)
# ==========================================

class AgentInfo(BaseModel):
    """Informações de um agente participante."""
    agent_id: str = Field(..., description="ID do agente no banco")
    instance_id: str = Field(..., description="ID da instância do agente")
    name: str = Field(..., description="Nome do agente")
    emoji: Optional[str] = Field(None, description="Emoji do agente")


class CreateConversationRequest(BaseModel):
    """Request para criar nova conversa."""
    title: Optional[str] = Field(None, description="Título da conversa")
    active_agent: Optional[AgentInfo] = Field(None, description="Agente inicial")


class CreateConversationResponse(BaseModel):
    """Response com conversation_id criado."""
    conversation_id: str
    title: str
    created_at: str


class AddMessageRequest(BaseModel):
    """Request para adicionar mensagem à conversa."""
    user_input: Optional[str] = Field(None, description="Mensagem do usuário")
    agent_response: Optional[str] = Field(None, description="Resposta do agente")
    agent_info: Optional[AgentInfo] = Field(None, description="Informações do agente que respondeu")


class SetActiveAgentRequest(BaseModel):
    """Request para alterar agente ativo."""
    agent_info: AgentInfo


class Message(BaseModel):
    """Modelo de mensagem."""
    id: str
    type: str  # "user" ou "bot"
    content: str
    timestamp: str
    agent: Optional[Dict[str, Any]] = None  # Presente apenas em mensagens de bot


class ConversationDetail(BaseModel):
    """Detalhes completos de uma conversa."""
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    active_agent: Optional[Dict[str, Any]]
    participants: List[Dict[str, Any]]
    messages: List[Dict[str, Any]]


class ConversationSummary(BaseModel):
    """Sumário de conversa para listagem."""
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    participant_count: int


# ==========================================
# Endpoints
# ==========================================

@router.post("/", response_model=CreateConversationResponse, summary="Criar nova conversa")
def create_conversation(request: CreateConversationRequest):
    """
    Cria uma nova conversa.

    Args:
        request: Dados da conversa (título e agente inicial opcionais)

    Returns:
        conversation_id e metadados da conversa criada
    """
    try:
        agent_info_dict = request.active_agent.dict() if request.active_agent else None

        conversation_id = conversation_service.create_conversation(
            title=request.title,
            active_agent=agent_info_dict
        )

        # Buscar conversa criada para retornar dados completos
        conversation = conversation_service.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=500, detail="Erro ao criar conversa")

        return CreateConversationResponse(
            conversation_id=conversation['conversation_id'],
            title=conversation['title'],
            created_at=conversation['created_at']
        )

    except Exception as e:
        logger.error(f"❌ Erro ao criar conversa: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar conversa: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationDetail, summary="Obter conversa")
def get_conversation(
    conversation_id: str = Path(..., description="ID da conversa")
):
    """
    Obtém os detalhes completos de uma conversa, incluindo histórico de mensagens.

    Args:
        conversation_id: ID da conversa

    Returns:
        Dados completos da conversa
    """
    try:
        conversation = conversation_service.get_conversation_by_id(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversa não encontrada: {conversation_id}")

        return ConversationDetail(**conversation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversa: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar conversa: {str(e)}")


@router.post("/{conversation_id}/messages", summary="Adicionar mensagem à conversa")
def add_message(
    conversation_id: str = Path(..., description="ID da conversa"),
    request: AddMessageRequest = ...
):
    """
    Adiciona uma mensagem (usuário e/ou agente) à conversa.

    Args:
        conversation_id: ID da conversa
        request: Dados da mensagem

    Returns:
        Confirmação de sucesso
    """
    try:
        agent_info_dict = request.agent_info.dict() if request.agent_info else None

        success = conversation_service.add_message(
            conversation_id=conversation_id,
            user_input=request.user_input,
            agent_response=request.agent_response,
            agent_info=agent_info_dict
        )

        if not success:
            raise HTTPException(status_code=400, detail="Erro ao adicionar mensagem")

        return {"success": True, "message": "Mensagem adicionada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar mensagem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar mensagem: {str(e)}")


@router.put("/{conversation_id}/active-agent", summary="Alterar agente ativo")
def set_active_agent(
    conversation_id: str = Path(..., description="ID da conversa"),
    request: SetActiveAgentRequest = ...
):
    """
    Define qual agente estará ativo para a próxima resposta.

    Args:
        conversation_id: ID da conversa
        request: Informações do novo agente ativo

    Returns:
        Confirmação de sucesso
    """
    try:
        success = conversation_service.set_active_agent(
            conversation_id=conversation_id,
            agent_info=request.agent_info.dict()
        )

        if not success:
            raise HTTPException(status_code=400, detail="Erro ao alterar agente ativo")

        return {"success": True, "message": "Agente ativo atualizado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao alterar agente ativo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao alterar agente ativo: {str(e)}")


@router.get("/", summary="Listar conversas")
def list_conversations(
    limit: int = Query(20, ge=1, le=100, description="Número de conversas a retornar"),
    skip: int = Query(0, ge=0, description="Número de conversas a pular (paginação)")
):
    """
    Lista conversas recentes.

    Args:
        limit: Número máximo de conversas
        skip: Paginação (offset)

    Returns:
        Lista de conversas com sumários
    """
    try:
        conversations = conversation_service.list_conversations(limit=limit, skip=skip)

        # Mapear para sumários
        summaries = []
        for conv in conversations:
            summaries.append(ConversationSummary(
                conversation_id=conv['conversation_id'],
                title=conv['title'],
                created_at=conv['created_at'],
                updated_at=conv['updated_at'],
                message_count=len(conv.get('messages', [])),
                participant_count=len(conv.get('participants', []))
            ))

        return {
            "total": len(summaries),
            "conversations": summaries
        }

    except Exception as e:
        logger.error(f"❌ Erro ao listar conversas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar conversas: {str(e)}")


@router.delete("/{conversation_id}", summary="Deletar conversa")
def delete_conversation(
    conversation_id: str = Path(..., description="ID da conversa")
):
    """
    Deleta uma conversa e todo seu histórico.

    Args:
        conversation_id: ID da conversa

    Returns:
        Confirmação de sucesso
    """
    try:
        success = conversation_service.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Conversa não encontrada: {conversation_id}")

        return {"success": True, "message": "Conversa deletada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar conversa: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao deletar conversa: {str(e)}")


@router.get("/{conversation_id}/messages", summary="Obter mensagens da conversa")
def get_conversation_messages(
    conversation_id: str = Path(..., description="ID da conversa"),
    limit: Optional[int] = Query(None, ge=1, description="Limitar número de mensagens (mais recentes)")
):
    """
    Obtém as mensagens de uma conversa.

    Args:
        conversation_id: ID da conversa
        limit: Opcional, retorna apenas N mensagens mais recentes

    Returns:
        Lista de mensagens
    """
    try:
        messages = conversation_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit
        )

        return {
            "conversation_id": conversation_id,
            "total": len(messages),
            "messages": messages
        }

    except Exception as e:
        logger.error(f"❌ Erro ao obter mensagens: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao obter mensagens: {str(e)}")
