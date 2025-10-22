# src/api/routes/conductor_cli.py
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import subprocess
import logging
import os
import json

# Import do MongoDB client
try:
    from src.core.services.mongo_task_client import MongoTaskClient
except ImportError as e:
    MongoTaskClient = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conductor", tags=["Conductor CLI"])

# Enum para modos de execução
class ExecutionMode:
    CONTAINER_MONGODB = "container_mongodb"  # Container usando MongoDB queue
    CONTAINER_DIRECT = "container_direct"    # Container chamando Claude direto (futuro)
    LOCAL_CLI = "local_cli"                  # Local usando conductor.py

def _detect_execution_mode() -> str:
    """
    Detecta o modo de execução apropriado.

    Estrutura preparada para 3 modos:
    1. container_mongodb: Container usando MongoDB queue system
    2. container_direct: Container com credentials chamando Claude direto (FUTURO)
    3. local_cli: Local usando conductor.py CLI diretamente
    """
    # Verificar se está em container
    is_container = os.path.exists("/.dockerenv")

    if is_container:
        # TODO: Futuramente verificar se tem credentials para modo direto
        # has_claude_credentials = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        # if has_claude_credentials:
        #     return ExecutionMode.CONTAINER_DIRECT

        # Por enquanto, container sempre usa MongoDB
        return ExecutionMode.CONTAINER_MONGODB
    else:
        # Modo local
        return ExecutionMode.LOCAL_CLI

def _mongodb_available() -> bool:
    """Verifica se MongoDB está disponível."""
    if not MongoTaskClient:
        return False

    try:
        # Test connection
        task_client = MongoTaskClient()
        return True
    except Exception:
        return False

class ConductorExecuteRequest(BaseModel):
    """Modelo genérico para execução do Conductor CLI."""
    # Parâmetros principais
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None  # For compatibility with gateway
    prompt: Optional[str] = None  # For compatibility with gateway
    input_text: Optional[str] = None
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    instance_id: Optional[str] = None  # For stateful execution with isolated context

    # Modos de execução
    chat: bool = False
    interactive: bool = False
    context_mode: Optional[str] = "stateless"  # "stateless" or "stateful"

    # Configurações
    cwd: Optional[str] = None
    timeout: Optional[int] = 600  # 10 minutes timeout for long-running operations
    environment: Optional[str] = None
    project: Optional[str] = None
    ai_provider: Optional[str] = None  # AI provider override

    # Operações especiais
    list_agents: bool = False
    info_agent: Optional[str] = None
    validate: bool = False
    backup: bool = False
    restore: Optional[str] = None
    install: Optional[str] = None

    # Flags adicionais
    debug: bool = False
    show_history: bool = False
    clear_history: bool = False
    meta: bool = False
    simulate: bool = False

def _execute_conductor_command(args: List[str], cwd: Optional[str] = None, timeout: int = 600) -> Dict[str, Any]:
    """
    Executa comando conductor.py de forma genérica.
    """
    try:
        # Caminho para o conductor.py
        conductor_path = "/app/src/cli/conductor.py"
        if not os.path.exists(conductor_path):
            conductor_path = "/app/conductor.py"
        if not os.path.exists(conductor_path):
            conductor_path = "/app/src/conductor.py"

        if not os.path.exists(conductor_path):
            raise FileNotFoundError("conductor.py não encontrado")

        # Montar comando completo
        command = ["python", conductor_path] + args

        logger.info(f"Executando: {' '.join(command)} em {cwd or 'CWD atual'}")

        # Executar comando
        result = subprocess.run(
            command,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "returncode": 124,
            "stdout": "",
            "stderr": f"Comando excedeu timeout de {timeout} segundos",
            "command": command
        }
    except Exception as e:
        return {
            "status": "error",
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "command": []
        }

@router.post("/execute", summary="Execute conductor CLI command generically")
def execute_conductor(request: ConductorExecuteRequest):
    """
    Endpoint genérico para executar comandos do Conductor CLI.

    Para execução de agentes, usa MongoDB queue system.
    Para operações de gerenciamento, usa conductor.py diretamente.
    """
    try:
        # 🔍 DEBUG: Log da request recebida
        logger.info("=" * 80)
        logger.info("📥 [CONDUCTOR API] /conductor/execute recebeu request:")
        logger.info(f"   - agent_id: {request.agent_id}")
        logger.info(f"   - agent_name: {request.agent_name}")
        logger.info(f"   - prompt: {request.prompt[:50] if request.prompt else None}...")
        logger.info(f"   - input_text: {request.input_text[:50] if request.input_text else None}...")
        logger.info(f"   - instance_id: {request.instance_id}")
        logger.info(f"   - context_mode: {request.context_mode}")
        logger.info("=" * 80)

        # === EXECUÇÃO DE AGENTES VIA MONGODB ===
        if request.agent_id or request.agent_name:
            return _execute_agent_via_mongodb(request)

        # === OPERAÇÕES DE INFORMAÇÃO E GERENCIAMENTO VIA CLI ===
        else:
            logger.error("❌ [CONDUCTOR API] Nenhum agent_id ou agent_name fornecido!")
            logger.error(f"   - Request completo: {request.dict()}")
            return _execute_management_command(request)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Erro na execução do conductor: {e}", exc_info=True)

        # Return detailed error information
        error_detail = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_traceback,
            "request": {
                "agent_id": request.agent_id,
                "input_text": request.input_text[:100] if request.input_text else None,
                "cwd": request.cwd
            },
            "context": "Falha na execução do Conductor"
        }
        raise HTTPException(status_code=500, detail=error_detail)


def _execute_agent_via_mongodb(request: ConductorExecuteRequest) -> Dict[str, Any]:
    """Executa agente baseado no modo de execução detectado."""
    execution_mode = _detect_execution_mode()

    logger.info(f"Modo de execução detectado: {execution_mode}")

    if execution_mode == ExecutionMode.CONTAINER_MONGODB:
        return _execute_agent_container_mongodb(request)
    elif execution_mode == ExecutionMode.CONTAINER_DIRECT:
        return _execute_agent_container_direct(request)  # FUTURO
    elif execution_mode == ExecutionMode.LOCAL_CLI:
        return _execute_agent_local_cli(request)
    else:
        raise HTTPException(status_code=500, detail=f"Modo de execução não suportado: {execution_mode}")


def _execute_agent_container_mongodb(request: ConductorExecuteRequest) -> Dict[str, Any]:
    """Executa agente via MongoDB queue system em container."""
    if MongoTaskClient is None:
        raise HTTPException(status_code=503, detail="MongoDB client não está disponível")

    # 🔍 DEBUG: Log completo da request recebida
    logger.info("=" * 80)
    logger.info("📥 REQUEST RECEBIDA:")
    logger.info(f"  agent_id: {request.agent_id}")
    logger.info(f"  agent_name: {request.agent_name}")
    logger.info(f"  instance_id: {request.instance_id}")
    logger.info(f"  input_text: {request.input_text[:50] if request.input_text else None}...")
    logger.info(f"  prompt: {request.prompt[:50] if request.prompt else None}...")
    logger.info(f"  context_mode: {request.context_mode}")
    logger.info("=" * 80)

    # Accept both input_text and prompt (for gateway compatibility)
    user_input = request.input_text or request.prompt
    if not user_input:
        raise HTTPException(status_code=400, detail="input_text or prompt is required for agent execution")

    # Accept both agent_id and agent_name (for gateway compatibility)
    agent_id = request.agent_id or request.agent_name
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id or agent_name is required")

    try:
        from src.container import container
        from src.core.prompt_engine import PromptEngine
        from src.core.services.conversation_service import ConversationService

        task_client = MongoTaskClient()
        conversation_service = ConversationService()

        # Obter services do container (mesma forma que o CLI faz)
        agent_discovery = container.get_agent_discovery_service()
        storage_service = container.get_storage_service()
        repository = storage_service.get_repository()

        # Verificar se agente existe
        agent_definition = agent_discovery.get_agent_definition(agent_id)
        if not agent_definition:
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")

        # Obter histórico de conversas
        # Se instance_id for fornecido, usar ConversationService (isolado por instância)
        # Caso contrário, usar AgentDiscoveryService (histórico global do agente)
        if request.instance_id:
            logger.info(f"Loading conversation history for instance_id: {request.instance_id}")
            conversation_history = conversation_service.get_conversation_history(
                instance_id=request.instance_id,
                agent_name=agent_id
            )
        else:
            logger.info(f"Loading global conversation history for agent: {agent_id}")
            conversation_history = agent_discovery.get_conversation_history(agent_id)

        # Construir prompt completo usando PromptEngine (mesma forma que o CLI faz)
        agent_home = repository.get_agent_home_path(agent_id)

        prompt_engine = PromptEngine(agent_home_path=agent_home, prompt_format="xml", instance_id=request.instance_id)
        prompt_engine.load_context()

        full_prompt = prompt_engine.build_prompt_with_format(
            conversation_history=conversation_history,
            message=user_input,
            include_history=True
        )

        logger.info(f"Submetendo tarefa via MongoDB: agent={agent_id}, instance={request.instance_id or 'global'}...")

        # 🔍 LOG DETALHADO PARA RASTREAR PROVIDER
        logger.info("🔍 [CONDUCTOR_CLI] Determinando provider:")
        logger.info(f"   - request.ai_provider: {request.ai_provider}")
        logger.info(f"   - agent_definition: {agent_definition}")
        logger.info(f"   - agent_ai_provider: {getattr(agent_definition, 'ai_provider', 'N/A')}")
        
        # Determinar provider com fallback hierárquico
        provider = container.get_ai_provider(
            agent_definition=agent_definition,
            cli_provider=request.ai_provider
        )
        
        logger.info(f"✅ [CONDUCTOR_CLI] Provider final: {provider}")
        logger.info(f"   - cli_provider: {request.ai_provider}")
        logger.info(f"   - agent_ai_provider: {getattr(agent_definition, 'ai_provider', 'N/A')}")
        logger.info(f"   - provider_final: {provider}")

        # Submeter tarefa via MongoDB
        task_id = task_client.submit_task(
            agent_id=agent_id,
            prompt=full_prompt,
            cwd=request.cwd or "/app",
            timeout=request.timeout or 600,
            provider=provider,
            instance_id=request.instance_id  # SAGA-004: Pass instance_id to task
        )

        # Aguardar resultado
        result_document = task_client.get_task_result(
            task_id=task_id,
            timeout=request.timeout or 600
        )

        # Extrair resposta do assistente
        assistant_response = result_document.get("result") or result_document.get("stdout") or ""

        # 🔥 NORMALIZAÇÃO: Salvar no history GLOBAL do agente (mesmo fluxo que REPL)
        if assistant_response:
            logger.info(f"Saving to global agent history for agent: {agent_id}")
            try:
                from src.core.domain import HistoryEntry
                import uuid
                import time

                # Criar HistoryEntry (mesma estrutura que TaskExecutionService usa)
                history_entry = HistoryEntry(
                    _id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    task_id=result_document.get("task_id", str(uuid.uuid4())),
                    status="completed" if result_document.get("status") == "success" else "error",
                    summary=assistant_response[:200] + '...' if len(assistant_response) > 200 else assistant_response,
                    git_commit_hash=""
                )

                # Obter agent storage service do container
                agent_storage_service = container.get_agent_storage_service()
                storage = agent_storage_service.get_storage()

                # Salvar no history global (MESMA função que TaskExecutionService usa)
                logger.info(f"💾 [CONDUCTOR] Salvando no history global:")
                logger.info(f"   - agent_id: {agent_id}")
                logger.info(f"   - instance_id: {request.instance_id}")
                logger.info(f"   - user_input: {user_input[:100]}...")
                logger.info(f"   - ai_response: {assistant_response[:100]}...")
                
                storage.append_to_history(
                    agent_id=agent_id,
                    entry=history_entry,
                    user_input=user_input,
                    ai_response=assistant_response,
                    instance_id=request.instance_id  # Pode ser None, storage decide o que fazer
                )

                logger.info(f"✅ [CONDUCTOR] Successfully saved to global history for agent: {agent_id}")
                if request.instance_id:
                    logger.info(f"   - instance_id salvo: {request.instance_id}")

            except Exception as e:
                logger.error(f"❌ Error saving to global history: {e}", exc_info=True)
                # Não falhar a request por erro de persistência

        # Salvar em coleção isolada SE instance_id for fornecido (comportamento adicional)
        if request.instance_id and assistant_response:
            logger.info(f"Also saving to isolated conversation for instance_id: {request.instance_id}")
            conversation_service.append_to_conversation(
                instance_id=request.instance_id,
                agent_name=agent_id,
                user_message=user_input,
                assistant_response=assistant_response
            )

        return result_document

    except HTTPException:
        # Re-raise HTTP exceptions as-is (like 404 for agent not found)
        raise
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Erro na execução via MongoDB: {e}", exc_info=True)

        # Return detailed error information
        error_detail = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_traceback,
            "agent_id": request.agent_id,
            "context": "Falha ao executar agente via MongoDB queue system"
        }
        raise HTTPException(status_code=500, detail=error_detail)


def _execute_agent_container_direct(request: ConductorExecuteRequest) -> Dict[str, Any]:
    """
    FUTURO: Executa agente diretamente no container com credentials.

    Quando implementado, terá acesso direto ao Claude API sem precisar
    de processos externos ou MongoDB queue.
    """
    raise HTTPException(
        status_code=501,
        detail="Modo container_direct não implementado ainda. Configure CONDUCTOR_MODE=mongodb para usar queue system."
    )


def _execute_agent_local_cli(request: ConductorExecuteRequest) -> Dict[str, Any]:
    """Executa agente localmente via conductor.py CLI."""
    if not request.input_text:
        raise HTTPException(status_code=400, detail="input_text é obrigatório para execução de agente")

    # Montar argumentos para conductor.py
    args = ["--agent", request.agent_id, "--input", request.input_text]

    # Adicionar flags baseadas nos parâmetros
    if request.chat:
        args.append("--chat")
    if request.interactive:
        args.append("--interactive")
    if request.debug:
        args.append("--debug")
    if request.timeout and request.timeout != 600:
        args.extend(["--timeout", str(request.timeout)])

    logger.info(f"Executando via CLI local: conductor.py {' '.join(args[:6])}...")

    # Executar via CLI
    result = _execute_conductor_command(args, request.cwd, request.timeout or 600)
    return result


def _execute_management_command(request: ConductorExecuteRequest) -> Dict[str, Any]:
    """Executa comandos de gerenciamento via conductor.py CLI."""
    args = []

    # === OPERAÇÕES DE INFORMAÇÃO ===
    if request.list_agents:
        args.append("--list")
    elif request.info_agent:
        args.extend(["--info", request.info_agent])
    elif request.validate:
        args.append("--validate")
    # === GERENCIAMENTO ===
    elif request.backup:
        args.append("--backup")
    elif request.restore:
        args.extend(["--restore", request.restore])
    elif request.install:
        args.extend(["--install", request.install])
    else:
        raise HTTPException(status_code=400, detail="Operação não reconhecida")

    # Executar comando via CLI
    result = _execute_conductor_command(args, request.cwd, request.timeout or 600)
    return result

@router.get("/agents", summary="List all available agents")
def list_agents():
    """Listar todos os agentes disponíveis."""
    request = ConductorExecuteRequest(list_agents=True)
    return execute_conductor(request)

@router.get("/agents/{agent_id}/info", summary="Get agent information")
def get_agent_info(agent_id: str):
    """Obter informações de um agente específico."""
    request = ConductorExecuteRequest(info_agent=agent_id)
    return execute_conductor(request)

@router.get("/validate", summary="Validate system configuration")
def validate_system():
    """Validar configuração do sistema."""
    request = ConductorExecuteRequest(validate=True)
    return execute_conductor(request)

# Manter compatibilidade com endpoint antigo
@router.post("/agents/{agent_id}/execute", summary="Execute specific agent (compatibility)")
def execute_agent_legacy(agent_id: str, request_data: Dict[str, Any]):
    """Endpoint de compatibilidade que mapeia para o novo sistema genérico."""
    try:
        # Extrair dados do request antigo
        user_input = request_data.get("user_input", "")
        cwd = request_data.get("cwd")
        timeout = request_data.get("timeout", 600)

        # Criar request genérico
        conductor_request = ConductorExecuteRequest(
            agent_id=agent_id,
            input_text=user_input,  # Preservar input original
            cwd=cwd,
            timeout=timeout
        )

        return execute_conductor(conductor_request)

    except Exception as e:
        logger.error(f"Erro no endpoint de compatibilidade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))