# src/api/routes/agents.py
from fastapi import APIRouter, HTTPException, Path
from typing import List, Dict, Any
from pydantic import BaseModel
from typing import Optional

# Importar da arquitetura existente
from src.container import container  # Usar instância global do container DI
from src.api.models import AgentListResponse, AgentSummary, AgentDetailResponse, ValidationResult
from src.core.services.mongo_task_client import MongoTaskClient

router = APIRouter(prefix="/agents", tags=["Agents"])

# Modelo existente do server.py
class AgentExecuteRequest(BaseModel):
    user_input: str
    cwd: str
    timeout: Optional[int] = 300
    provider: Optional[str] = "claude"
    instance_id: Optional[str] = None  # SAGA-003: Instance ID for isolated context
    context_mode: Optional[str] = "stateless"  # SAGA-003: "stateful" or "stateless"

@router.get("/", response_model=AgentListResponse, summary="Listar todos os agentes")
def list_agents():
    """
    Lista todos os agentes disponíveis no sistema.

    Esta rota é uma versão refatorada do endpoint GET /agents original,
    utilizando os mesmos serviços mas com estrutura modular.
    """
    try:
        conductor_service = container.get_conductor_service()
        agents = conductor_service.discover_agents()

        # Usar mesma estrutura de resposta do endpoint atual
        agent_summaries = [
            AgentSummary(id=agent.agent_id, name=getattr(agent, 'name', 'N/A'))
            for agent in agents
        ]

        return AgentListResponse(total=len(agent_summaries), agents=agent_summaries)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar a lista de agentes: {e}"
        )

@router.get("/{agent_id}/info", response_model=AgentDetailResponse, summary="Obter detalhes de um agente")
def get_agent_info(agent_id: str = Path(..., description="ID do agente a ser consultado")):
    """
    Retorna informações detalhadas de um agente específico.

    Utiliza o AgentDiscoveryService para carregar a definição completa do agente.
    """
    try:
        discovery_service = container.get_agent_discovery_service()

        # Verificar se agente existe primeiro
        if not discovery_service.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")

        # Carregar definição completa
        definition = discovery_service.get_agent_definition(agent_id)
        if not definition:
            raise HTTPException(status_code=404, detail=f"Definição do agente '{agent_id}' não encontrada")

        return AgentDetailResponse(
            name=definition.name,
            version=definition.version,
            schema_version=definition.schema_version,
            description=definition.description,
            author=definition.author,
            tags=definition.tags,
            capabilities=definition.capabilities,
            allowed_tools=definition.allowed_tools,
            agent_id=definition.agent_id or agent_id
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao carregar informações do agente: {e}"
        )

@router.get("/{agent_id}/validate", response_model=ValidationResult, summary="Validar configuração de um agente")
def validate_agent(agent_id: str = Path(..., description="ID do agente a ser validado")):
    """
    Executa validação completa de um agente específico.

    Verifica definição, estrutura de arquivos e integridade de dados.
    """
    try:
        discovery_service = container.get_agent_discovery_service()

        # Usar método de validação que acabamos de implementar
        is_valid, errors, warnings = discovery_service.validate_agent(agent_id)

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            agent_id=agent_id
        )

    except Exception as e:
        # Se houver erro na validação, retornar como erro de validação
        return ValidationResult(
            is_valid=False,
            errors=[f"Erro durante validação: {str(e)}"],
            warnings=[],
            agent_id=agent_id
        )

@router.post("/{agent_id}/execute", response_model=Dict[str, Any], summary="Executar um agente")
def execute_agent(agent_id: str, request: AgentExecuteRequest):
    """
    Executa um agente específico via MongoDB queue system.

    SAGA-003: Suporta context_mode "stateful" para manter histórico por instance_id.
    """
    if MongoTaskClient is None:
        raise HTTPException(status_code=503, detail="MongoDB client não está disponível")

    try:
        task_client = MongoTaskClient()
        discovery_service = container.get_agent_discovery_service()

        # SAGA-003: Gerenciar histórico por instance_id se stateful
        conversation_history = []
        if request.context_mode == "stateful" and request.instance_id:
            from src.core.services.conversation_service import ConversationService
            conv_service = ConversationService()
            conversation_history = conv_service.get_conversation_history(
                instance_id=request.instance_id,
                agent_name=agent_id
            )

        # Build XML prompt com histórico personalizado se stateful
        if request.context_mode == "stateful" and conversation_history:
            # Usar histórico do instance_id em vez do histórico global
            xml_prompt = discovery_service.get_full_prompt(
                agent_id=agent_id,
                current_message=request.user_input,
                meta=False,
                new_agent_id=None,
                include_history=False,  # Não usar histórico global
                save_to_file=False
            )
            # TODO: Injetar conversation_history customizado no prompt
            # Por enquanto, incluímos manualmente
        else:
            # Modo stateless: usa histórico global ou nenhum
            xml_prompt = discovery_service.get_full_prompt(
                agent_id=agent_id,
                current_message=request.user_input,
                meta=False,
                new_agent_id=None,
                include_history=(request.context_mode != "stateless"),
                save_to_file=False
            )

        # Submete a tarefa
        task_id = task_client.submit_task(
            agent_id=agent_id,
            cwd=request.cwd,
            timeout=request.timeout,
            provider=request.provider,
            prompt=xml_prompt
        )

        # Aguarda o resultado
        result_document = task_client.get_task_result(task_id=task_id, timeout=request.timeout)

        # SAGA-003: Salvar histórico se stateful
        if request.context_mode == "stateful" and request.instance_id:
            from src.core.services.conversation_service import ConversationService
            conv_service = ConversationService()
            assistant_response = result_document.get("output", "")
            conv_service.append_to_conversation(
                instance_id=request.instance_id,
                agent_name=agent_id,
                user_message=request.user_input,
                assistant_response=assistant_response
            )

        return result_document

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))