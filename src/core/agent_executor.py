# src/core/agent_executor.py
from typing import Dict, Callable, Any, List
from src.core.domain import TaskDTO, TaskResultDTO, AgentDefinition
# Supondo que um cliente LLM e um PromptEngine existam e serão injetados.
# Criaremos placeholders por enquanto.

class PlaceholderLLMClient:
    def invoke(self, prompt: str) -> str:
        return f"Resposta simulada para o prompt: {prompt[:50]}..."

class PlaceholderPromptEngine:
    def build_prompt(self, message: str) -> str:
        return f"Este é um prompt construído para: {message}"

class AgentExecutor:
    """
    Executa uma única tarefa para um agente, de forma stateless.
    Recebe todo o contexto necessário para operar, sem manter estado interno entre as execuções.
    """
    def __init__(
        self,
        agent_definition: AgentDefinition,
        llm_client: Any, # Usando Any para o placeholder
        prompt_engine: Any, # Usando Any para o placeholder
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
            # Lógica de integração com PromptEngine virá no próximo estágio
            final_prompt = self._prompt_engine.build_prompt(task.user_input)

            # Invocar o LLM
            response = self._llm_client.invoke(final_prompt)

            return TaskResultDTO(
                status="success",
                output=response,
                metadata={"agent_id": self._agent_definition.agent_id}
            )
        except Exception as e:
            return TaskResultDTO(
                status="error",
                output=str(e),
                metadata={"agent_id": self._agent_definition.agent_id}
            )