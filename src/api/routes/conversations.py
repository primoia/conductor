# src/api/routes/conversations.py
"""
🔥 NOVO: Rotas de API para o modelo de conversas globais.

Endpoints para gerenciar conversas independentes de agentes específicos,
permitindo colaboração de múltiplos agentes em uma única linha de raciocínio.

Ref: PLANO_REFATORACAO_CONVERSATION_ID.md - Fase 1
Data: 2025-11-01
"""

from fastapi import APIRouter, Body, HTTPException, Path, Query
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
    title: Optional[str] = Field(None, description="Titulo da conversa")
    active_agent: Optional[AgentInfo] = Field(None, description="Agente inicial")
    screenplay_id: Optional[str] = Field(None, description="ID do roteiro ao qual esta conversa pertence")
    context: Optional[str] = Field(None, description="Contexto da conversa em markdown (bug, feature, etc.)")
    allowed_agents: Optional[List[str]] = Field(None, description="Lista de agent_ids permitidos nesta conversa (squad). Se null, qualquer agente pode participar.")
    max_chain_depth: Optional[int] = Field(10, ge=1, le=100, description="Max autonomous chain cycles for this conversation. Default 10.")
    auto_delegate: bool = Field(True, description="If true, agents can auto-chain to other agents without waiting for human. Default true.")


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
    screenplay_id: Optional[str] = None
    context: Optional[str] = None
    allowed_agents: Optional[List[str]] = None
    max_chain_depth: Optional[int] = 10
    auto_delegate: bool = True


class ConversationSummary(BaseModel):
    """Sumário de conversa para listagem."""
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    participant_count: int
    screenplay_id: Optional[str] = None
    display_order: Optional[int] = None  # 🔥 NOVO: Ordem de exibição customizada


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
            active_agent=agent_info_dict,
            screenplay_id=request.screenplay_id,
            context=request.context,
            allowed_agents=request.allowed_agents,
            max_chain_depth=request.max_chain_depth,
            auto_delegate=request.auto_delegate,
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
    skip: int = Query(0, ge=0, description="Número de conversas a pular (paginação)"),
    screenplay_id: Optional[str] = Query(None, description="Filtrar conversas por roteiro")
):
    """
    Lista conversas recentes.

    Args:
        limit: Número máximo de conversas
        skip: Paginação (offset)
        screenplay_id: Opcional, filtrar conversas de um roteiro específico

    Returns:
        Lista de conversas com sumários
    """
    try:
        conversations = conversation_service.list_conversations(limit=limit, skip=skip, screenplay_id=screenplay_id)

        # Mapear para sumários
        summaries = []
        for conv in conversations:
            summary_dict = {
                'conversation_id': conv['conversation_id'],
                'title': conv['title'],
                'created_at': conv['created_at'],
                'updated_at': conv['updated_at'],
                'message_count': len(conv.get('messages', [])),
                'participant_count': len(conv.get('participants', []))
            }

            # Adicionar campos opcionais
            if 'screenplay_id' in conv:
                summary_dict['screenplay_id'] = conv['screenplay_id']
            if 'display_order' in conv:
                summary_dict['display_order'] = conv['display_order']

            summaries.append(ConversationSummary(**summary_dict))

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


@router.patch("/{conversation_id}/title", summary="Atualizar título da conversa")
def update_conversation_title(
    conversation_id: str = Path(..., description="ID da conversa"),
    new_title: str = Query(..., min_length=3, max_length=100, description="Novo título da conversa")
):
    """
    Atualiza o título de uma conversa.

    Args:
        conversation_id: ID da conversa
        new_title: Novo título (3-100 caracteres)

    Returns:
        Confirmação de sucesso
    """
    try:
        success = conversation_service.update_conversation_title(
            conversation_id=conversation_id,
            new_title=new_title
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Conversa não encontrada: {conversation_id}")

        return {"success": True, "message": "Título atualizado com sucesso", "new_title": new_title}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar título: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar título: {str(e)}")


class UpdateContextRequest(BaseModel):
    """Request para atualizar contexto da conversa."""
    context: Optional[str] = Field(None, description="Contexto da conversa em markdown (null para limpar)")


@router.patch("/{conversation_id}/context", summary="Atualizar contexto da conversa")
def update_conversation_context(
    conversation_id: str = Path(..., description="ID da conversa"),
    request: UpdateContextRequest = ...
):
    """
    Atualiza o contexto de uma conversa.

    Args:
        conversation_id: ID da conversa
        request: Novo contexto em markdown (pode ser null para limpar)

    Returns:
        Confirmação de sucesso
    """
    try:
        success = conversation_service.update_conversation_context(
            conversation_id=conversation_id,
            context=request.context
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Conversa não encontrada: {conversation_id}")

        return {"success": True, "message": "Contexto atualizado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar contexto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar contexto: {str(e)}")


class UpdateSettingsRequest(BaseModel):
    """Request to update conversation chain settings."""
    max_chain_depth: Optional[int] = Field(None, ge=0, le=100, description="Max autonomous chain cycles. 0 = reset to global default. Null = unchanged.")
    auto_delegate: Optional[bool] = Field(None, description="Allow agents to auto-chain without human. Null = unchanged.")


@router.patch("/{conversation_id}/settings", summary="Update conversation chain settings")
def update_conversation_settings(
    conversation_id: str = Path(..., description="ID da conversa"),
    request: UpdateSettingsRequest = Body(...),
):
    """
    Update chain settings for a conversation (max_chain_depth, auto_delegate).

    - max_chain_depth: per-conversation limit for autonomous agent chaining.
      Set to 0 to reset to global default. Null leaves unchanged.
    - auto_delegate: if true, agents can auto-chain without waiting for human.
    """
    try:
        success = conversation_service.update_conversation_settings(
            conversation_id=conversation_id,
            max_chain_depth=request.max_chain_depth,
            auto_delegate=request.auto_delegate,
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Conversa nao encontrada: {conversation_id}")

        return {"success": True, "message": "Settings updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar settings: {str(e)}")


@router.patch("/reorder", summary="Atualizar ordem das conversas")
def reorder_conversations(
    order_updates: dict
):
    """
    🔥 NOVO: Atualiza a ordem de exibição das conversas.

    Permite que o usuário reordene conversas via drag & drop,
    persistindo a ordem customizada no MongoDB.

    Args:
        order_updates: Dicionário com chave "order_updates" contendo array de
                      {conversation_id: str, display_order: int}

    Returns:
        Confirmação de sucesso com número de conversas atualizadas
    """
    try:
        updates = order_updates.get("order_updates", [])

        if not updates or not isinstance(updates, list):
            raise HTTPException(
                status_code=400,
                detail="Campo 'order_updates' é obrigatório e deve ser uma lista"
            )

        logger.info(f"🔄 [REORDER] Atualizando ordem de {len(updates)} conversas")

        updated_count = conversation_service.update_conversation_order(updates)

        return {
            "success": True,
            "message": f"Ordem atualizada para {updated_count} conversas",
            "updated_count": updated_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar ordem das conversas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar ordem: {str(e)}")


@router.post("/migrate-screenplays", summary="Migrar roteiros antigos para ter conversas")
def migrate_screenplays_to_conversations():
    """
    Endpoint de migração para normalizar roteiros antigos.

    Para cada roteiro no banco:
    1. Verifica se já tem conversa vinculada
    2. Se não tiver, cria uma conversa default
    3. Atualiza agent_instances para incluir conversation_id

    Returns:
        Estatísticas da migração
    """
    try:
        from pymongo import MongoClient
        from datetime import datetime
        import os
        import uuid

        # Conectar ao MongoDB
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        db_name = os.getenv('MONGO_DATABASE', 'conductor_state')
        client = MongoClient(mongo_uri)
        db = client[db_name]

        screenplays_collection = db['screenplays']
        conversations_collection = db['conversations']
        agent_instances_collection = db['agent_instances']

        stats = {
            "screenplays_processed": 0,
            "conversations_created": 0,
            "agent_instances_updated": 0,
            "errors": []
        }

        # Buscar todos os roteiros
        screenplays = list(screenplays_collection.find({}, {"_id": 1, "name": 1}))
        logger.info(f"🔄 [MIGRATION] Encontrados {len(screenplays)} roteiros para processar")

        for screenplay in screenplays:
            screenplay_id = str(screenplay['_id'])
            screenplay_name = screenplay.get('name', 'Sem nome')

            try:
                stats["screenplays_processed"] += 1

                # Verificar se já existe conversa para esse roteiro
                existing_conversation = conversations_collection.find_one({
                    "screenplay_id": screenplay_id
                })

                conversation_id = None

                if existing_conversation:
                    # Já tem conversa
                    conversation_id = existing_conversation['conversation_id']
                    logger.info(f"✅ [MIGRATION] Roteiro '{screenplay_name}' já tem conversa: {conversation_id}")
                else:
                    # Criar conversa default
                    conversation_id = str(uuid.uuid4())
                    timestamp = datetime.utcnow().isoformat()

                    conversation_doc = {
                        "conversation_id": conversation_id,
                        "title": f"Conversa - {screenplay_name}",
                        "created_at": timestamp,
                        "updated_at": timestamp,
                        "active_agent": None,
                        "participants": [],
                        "messages": [],
                        "screenplay_id": screenplay_id
                    }

                    conversations_collection.insert_one(conversation_doc)
                    stats["conversations_created"] += 1
                    logger.info(f"✅ [MIGRATION] Conversa criada para roteiro '{screenplay_name}': {conversation_id}")

                # Atualizar agent_instances que pertencem a esse roteiro mas não têm conversation_id
                update_result = agent_instances_collection.update_many(
                    {
                        "screenplay_id": screenplay_id,
                        "$or": [
                            {"conversation_id": {"$exists": False}},
                            {"conversation_id": None}
                        ]
                    },
                    {
                        "$set": {"conversation_id": conversation_id}
                    }
                )

                if update_result.modified_count > 0:
                    stats["agent_instances_updated"] += update_result.modified_count
                    logger.info(f"✅ [MIGRATION] Atualizados {update_result.modified_count} agent_instances do roteiro '{screenplay_name}'")

            except Exception as e:
                error_msg = f"Erro ao processar roteiro '{screenplay_name}': {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(f"❌ [MIGRATION] {error_msg}")

        logger.info(f"🎉 [MIGRATION] Migração concluída: {stats}")
        return {
            "success": True,
            "message": "Migração concluída com sucesso",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"❌ [MIGRATION] Erro fatal na migração: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na migração: {str(e)}")
