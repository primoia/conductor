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
    input_text: Optional[str] = None
    input_file: Optional[str] = None
    output_file: Optional[str] = None

    # Modos de execução
    chat: bool = False
    interactive: bool = False

    # Configurações
    cwd: Optional[str] = None
    timeout: Optional[int] = 300
    environment: Optional[str] = None
    project: Optional[str] = None

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

def _execute_conductor_command(args: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Dict[str, Any]:
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
        # === EXECUÇÃO DE AGENTES VIA MONGODB ===
        if request.agent_id:
            return _execute_agent_via_mongodb(request)

        # === OPERAÇÕES DE INFORMAÇÃO E GERENCIAMENTO VIA CLI ===
        else:
            return _execute_management_command(request)

    except Exception as e:
        logger.error(f"Erro na execução do conductor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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

    if not request.input_text:
        raise HTTPException(status_code=400, detail="input_text é obrigatório para execução de agente")

    try:
        task_client = MongoTaskClient()

        # Montar comando preservando input original do usuário
        command = ["claude", "-p", request.input_text]  # Input original preservado!

        # Adicionar flags baseadas nos parâmetros
        if request.chat:
            command.append("--chat")
        if request.debug:
            command.append("--debug")

        logger.info(f"Submetendo tarefa via MongoDB: agent={request.agent_id}, command={command[:2]}...")

        # Submeter tarefa via MongoDB
        task_id = task_client.submit_task(
            agent_id=request.agent_id,
            command=command,
            cwd=request.cwd or "/app",
            timeout=request.timeout or 300,
            provider="claude"  # Pode ser expandido para gemini
        )

        # Aguardar resultado
        result_document = task_client.get_task_result(
            task_id=task_id,
            timeout=request.timeout or 300
        )

        return result_document

    except Exception as e:
        logger.error(f"Erro na execução via MongoDB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    if request.timeout and request.timeout != 300:
        args.extend(["--timeout", str(request.timeout)])

    logger.info(f"Executando via CLI local: conductor.py {' '.join(args[:6])}...")

    # Executar via CLI
    result = _execute_conductor_command(args, request.cwd, request.timeout or 300)
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
    result = _execute_conductor_command(args, request.cwd, request.timeout or 300)
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
        timeout = request_data.get("timeout", 300)

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