# src/core/services/task_execution_service.py
import os
import sys
from src.core.services.storage_service import StorageService
from src.core.services.tool_management_service import ToolManagementService
from src.core.services.configuration_service import ConfigurationService
from src.core.domain import AgentDefinition, TaskDTO, TaskResultDTO
from src.core.agent_executor import AgentExecutor, PlaceholderLLMClient
from src.infrastructure.llm.cli_client import create_llm_client
from src.core.prompt_engine import PromptEngine


class TaskExecutionService:
    """Responsável por executar tarefas de agentes."""

    def __init__(
        self, 
        storage_service: StorageService,
        tool_service: ToolManagementService,
        config_service: ConfigurationService
    ):
        self._storage = storage_service.get_repository()
        self._tools = tool_service
        self._config = config_service

    def execute_task(self, task: TaskDTO) -> TaskResultDTO:
        """Executa uma tarefa de agente."""
        try:
            # Armazenar task atual para acesso em _create_agent_executor
            self._current_task = task
            
            # 1. Carregar a definição do agente
            agent_definition = self._load_agent_definition(task.agent_id)
            
            # 2. Carregar dados da sessão
            session_data = self._load_session_data(task.agent_id)
            agent_home_path = self._get_agent_home_path(task.agent_id, session_data)
            
            # 3. Criar executor de agente
            executor = self._create_agent_executor(
                agent_definition, 
                agent_home_path, 
                session_data
            )
            
            # 4. Executar tarefa
            result = executor.run(task)
            
            # 5. Persistir resultado se bem-sucedido e solicitado
            if result.status == "success":
                # Check if we should save to history (default: True for backward compatibility)
                save_to_history = task.context.get("save_to_history", True)
                if save_to_history:
                    self._persist_task_result(task.agent_id, result)
            
            return result

        except Exception as e:
            return TaskResultDTO(status="error", output=str(e), metadata={})

    def _load_agent_definition(self, agent_id: str) -> AgentDefinition:
        """Carrega e cria a definição do agente."""
        definition = self._storage.load_definition(agent_id)
        if not definition:
            raise FileNotFoundError(f"Definição não encontrada para o agente: {agent_id}")

        # Filter only valid fields for AgentDefinition
        valid_fields = {
            'name', 'version', 'schema_version', 'description', 'author', 
            'tags', 'capabilities', 'allowed_tools'
        }
        
        filtered_data = {k: v for k, v in definition.items() if k in valid_fields}
        
        # Ensure required fields have defaults
        filtered_data.setdefault('name', agent_id)
        filtered_data.setdefault('version', '1.0.0')
        filtered_data.setdefault('schema_version', '1.0')
        filtered_data.setdefault('description', f'Agent {agent_id}')
        filtered_data.setdefault('author', 'Unknown')
        filtered_data.setdefault('tags', [])
        filtered_data.setdefault('capabilities', [])
        filtered_data.setdefault('allowed_tools', [])
        
        return AgentDefinition(**filtered_data)

    def _load_session_data(self, agent_id: str) -> dict:
        """Carrega dados da sessão do agente."""
        return self._storage.load_session(agent_id)

    def _get_agent_home_path(self, agent_id: str, session_data: dict) -> str:
        """Obtém o caminho home do agente."""
        agent_home_path = session_data.get("agent_home_path")
        if not agent_home_path:
            # Fall back to deriving the path from the repository if missing from session
            agent_home_path = self._storage.get_agent_home_path(agent_id)
            # Update session with the derived path for future use
            self._storage.save_session(agent_id, session_data)
        return agent_home_path

    def _create_agent_executor(
        self, 
        agent_definition: AgentDefinition, 
        agent_home_path: str, 
        session_data: dict
    ) -> AgentExecutor:
        """Cria o executor de agente com suas dependências."""
        # Detectar se estamos em ambiente de teste
        is_test_environment = (
            'pytest' in sys.modules or 
            'unittest' in sys.modules or
            os.getenv('PYTEST_RUNNING') == 'true'
        )
        
        # Criar cliente LLM
        if is_test_environment:
            llm_client = PlaceholderLLMClient()
        else:
            ai_provider = getattr(agent_definition, 'ai_provider', 'claude')
            # Determinar working directory e timeout
            # Se project_path foi fornecido no contexto, usar ele
            # Senão, usar agent_home_path (comportamento atual)
            working_directory = agent_home_path
            timeout = 120  # Default timeout
            
            if hasattr(self, '_current_task') and self._current_task:
                project_path = self._current_task.context.get("project_path")
                if project_path and os.path.exists(project_path):
                    working_directory = project_path
                
                # Usar timeout do contexto se fornecido
                context_timeout = self._current_task.context.get("timeout")
                if context_timeout and isinstance(context_timeout, int):
                    timeout = context_timeout
            
            llm_client = create_llm_client(
                ai_provider=ai_provider,
                working_directory=working_directory,
                timeout=timeout,
                is_admin_agent=True
            )
        
        # Criar engine de prompt
        prompt_engine = PromptEngine(agent_home_path=agent_home_path)
        prompt_engine.load_context()
        
        # Filtrar ferramentas permitidas
        allowed_tools = self._tools.get_allowed_tools(
            session_data.get("allowed_tools", [])
        )

        return AgentExecutor(
            agent_definition=agent_definition,
            llm_client=llm_client,
            prompt_engine=prompt_engine,
            allowed_tools=allowed_tools,
            current_session=session_data
        )

    def _persist_task_result(self, agent_id: str, result: TaskResultDTO) -> None:
        """Persiste o resultado da tarefa no repositório."""
        # Save updated session data
        if result.updated_session:
            current_session = self._storage.load_session(agent_id)
            current_session.update(result.updated_session)
            self._storage.save_session(agent_id, current_session)
        
        # Save updated knowledge data
        if result.updated_knowledge:
            current_knowledge = self._storage.load_knowledge(agent_id)
            current_knowledge.update(result.updated_knowledge)
            self._storage.save_knowledge(agent_id, current_knowledge)
        
        # Append history entry
        if result.history_entry:
            self._storage.append_to_history(agent_id, result.history_entry)