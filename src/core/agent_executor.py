# src/core/agent_executor.py
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
        allowed_tools: Dict[str, Callable[..., Any]]
    ):
        self._agent_definition = agent_definition
        self._llm_client = llm_client
        self._prompt_engine = prompt_engine
        self._allowed_tools = allowed_tools

    def run(self, task: TaskDTO) -> TaskResultDTO:
        """
        Executa o ciclo de vida de uma tarefa: constrói o prompt, invoca o LLM e retorna o resultado.
        """
        try:
            # Assume-se que o histórico da conversa está no contexto da tarefa
            conversation_history = task.context.get("conversation_history", [])
            
            final_prompt = self._prompt_engine.build_prompt(
                conversation_history=conversation_history,
                message=task.user_input
            )

            response = self._llm_client.invoke(final_prompt)

            return TaskResultDTO(
                status="success",
                output=response,
                metadata={"agent_id": task.agent_id}
            )
        except Exception as e:
            return TaskResultDTO(
                status="error",
                output=str(e),
                metadata={"agent_id": task.agent_id}
            )