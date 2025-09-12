# src/core/agent_executor.py
import time
import uuid
from typing import Dict, Callable, Any, List
from src.core.domain import TaskDTO, TaskResultDTO, AgentDefinition
from src.core.prompt_engine import PromptEngine
# Removido o PlaceholderPromptEngine

class PlaceholderLLMClient:
    def invoke(self, prompt: str) -> str:
        return f"Resposta simulada para o prompt: {prompt[:100]}..."

class AgentExecutor:
    """
    Executa uma única tarefa para um agente, de forma stateless.
    """
    def __init__(
        self,
        agent_definition: AgentDefinition,
        llm_client: Any,
        prompt_engine: PromptEngine, # Agora recebe uma instância real
        allowed_tools: Dict[str, Callable[..., Any]],
        current_session: Dict = None
    ):
        self._agent_definition = agent_definition
        self._llm_client = llm_client
        self._prompt_engine = prompt_engine
        self._allowed_tools = allowed_tools
        self._current_session = current_session or {}

    def run(self, task: TaskDTO) -> TaskResultDTO:
        """
        Executa o ciclo de vida de uma tarefa: constrói o prompt, invoca o LLM e retorna o resultado.
        """
        try:
            # Use a função unificada do AgentDiscoveryService para construir o prompt completo
            from src.container import container
            agent_discovery_service = container.get_agent_discovery_service()
            
            # Extrair contexto meta do task
            meta = task.context.get("meta", False)
            new_agent_id = task.context.get("new_agent_id", None)
            
            # Usar a função unificada que já carrega histórico + contexto completo
            final_prompt = agent_discovery_service.get_full_prompt(
                agent_id=task.agent_id,
                current_message=task.user_input,  # Mensagem atual do usuário
                meta=meta,
                new_agent_id=new_agent_id,
                save_to_file=False  # Não salvar durante execução normal
            )

            response = self._llm_client.invoke(final_prompt)

            # Generate task_id for this execution
            task_id = str(uuid.uuid4())
            current_timestamp = time.time()

            # Create updated session data (example: add conversation entry)
            # Get current conversation count from session, default to 0
            current_count = self._current_session.get("conversation_count", 0)
            updated_session = {
                "last_task_id": task_id,
                "last_interaction": current_timestamp,
                "conversation_count": current_count + 1
            }

            # Create updated knowledge data (example: track task execution)
            updated_knowledge = {
                "last_task_execution": {
                    "task_id": task_id,
                    "timestamp": current_timestamp,
                    "user_input_summary": task.user_input[:100] + "..." if len(task.user_input) > 100 else task.user_input
                }
            }

            # Create history entry
            history_entry = {
                "task_id": task_id,
                "agent_id": task.agent_id,
                "timestamp": current_timestamp,
                "user_input": task.user_input,
                "status": "success",
                "ai_response": response,
                "output_length": len(response)
            }

            return TaskResultDTO(
                status="success",
                output=response,
                metadata={"agent_id": task.agent_id, "task_id": task_id},
                updated_session=updated_session,
                updated_knowledge=updated_knowledge,
                history_entry=history_entry
            )
        except Exception as e:
            return TaskResultDTO(
                status="error",
                output=str(e),
                metadata={"agent_id": task.agent_id}
            )