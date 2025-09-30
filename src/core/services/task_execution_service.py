# src/core/services/task_execution_service.py
import os
import sys
import uuid
from src.core.services.agent_storage_service import AgentStorageService
from src.core.services.tool_management_service import ToolManagementService
from src.core.services.configuration_service import ConfigurationService
from src.core.domain import AgentDefinition, TaskDTO, TaskResultDTO, HistoryEntry
from src.core.agent_executor import AgentExecutor, PlaceholderLLMClient
from src.infrastructure.llm.cli_client import create_llm_client
from src.core.prompt_engine import PromptEngine


class TaskExecutionService:
    """Responsável por executar tarefas de agentes."""

    def __init__(
        self,
        agent_storage_service: AgentStorageService,
        tool_service: ToolManagementService,
        config_service: ConfigurationService
    ):
        self._storage = agent_storage_service.get_storage()
        self._tools = tool_service
        self._config = config_service

    def execute_task(self, task: TaskDTO) -> TaskResultDTO:
        """Executa uma tarefa de agente."""
        try:
            # Armazenar task atual para acesso em _create_agent_executor
            self._current_task = task
            
            # 1. Carregar a definição do agente
            agent_definition = self._storage.load_definition(task.agent_id)
            
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
                    self._persist_task_result(task.agent_id, task, result)
            
            return result

        except Exception as e:
            return TaskResultDTO(status="error", output=str(e), metadata={})


    def _load_session_data(self, agent_id: str) -> dict:
        """Carrega dados da sessão do agente."""
        try:
            session = self._storage.load_session(agent_id)
            session_data = {
                'current_task_id': session.current_task_id,
                'state': session.state
            }

            # Achatar campos importantes do state para a raiz para compatibilidade
            if isinstance(session.state, dict):
                persistence_fields = ['last_task_id', 'last_interaction', 'conversation_count']
                for field in persistence_fields:
                    if field in session.state:
                        session_data[field] = session.state[field]

            return session_data

        except (FileNotFoundError, AttributeError):
            # Sessão não existe ou é um dict (baixo nível), retornar padrão
            return {'current_task_id': None, 'state': {}}

    def _get_agent_home_path(self, agent_id: str, session_data: dict) -> str:
        """Obtém o caminho home do agente."""
        agent_home_path = session_data.get("agent_home_path")
        if not agent_home_path:
            # Para storage de alto nível, precisamos acessar o repository de baixo nível
            # para obter o caminho físico. Isso é uma exceção necessária.
            from src.core.services.storage_service import StorageService
            storage_service = StorageService(self._config)
            repository = storage_service.get_repository()
            agent_home_path = repository.get_agent_home_path(agent_id)

            # Atualizar session com o path derivado para uso futuro
            from src.core.domain import AgentSession
            session = AgentSession(
                current_task_id=session_data.get('current_task_id'),
                state={**session_data.get('state', {}), 'agent_home_path': agent_home_path}
            )
            self._storage.save_session(agent_id, session)
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
            # Para MongoDB, usar diretório atual em vez do path conceitual
            if agent_home_path.startswith("mongodb://"):
                working_directory = os.getcwd()  # Use current directory for MongoDB agents
            else:
                working_directory = agent_home_path  # Use agent directory for filesystem agents
            timeout = 120  # Default timeout
            
            if hasattr(self, '_current_task') and self._current_task:
                project_path = self._current_task.context.get("project_path")
                if project_path and os.path.exists(project_path):
                    working_directory = project_path
                
                # Para agentes meta que criam outros agentes, usar diretório raiz do projeto
                # em vez do diretório do agente atual
                if (self._current_task.context.get("meta", False) or 
                    self._current_task.context.get("new_agent_id") or
                    agent_definition.tags and "meta" in agent_definition.tags):
                    # Usar diretório raiz do projeto para agentes meta
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(agent_home_path)))
                    if os.path.exists(project_root):
                        working_directory = project_root
                
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
        
        # Criar engine de prompt com formato configurado
        prompt_format = self._config.get_prompt_format()
        prompt_engine = PromptEngine(agent_home_path=agent_home_path, prompt_format=prompt_format)
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

    def _persist_task_result(self, agent_id: str, task: TaskDTO, result: TaskResultDTO) -> None:
        """Persiste o resultado da tarefa no repositório."""
        from src.core.domain import AgentSession, AgentKnowledge, KnowledgeItem

        # Save updated session data
        if result.updated_session:
            current_session = self._storage.load_session(agent_id)
            # Merge state dictionaries
            merged_state = {**current_session.state, **result.updated_session}
            new_session = AgentSession(
                current_task_id=current_session.current_task_id,
                state=merged_state
            )
            self._storage.save_session(agent_id, new_session)

        # Save updated knowledge data
        if result.updated_knowledge:
            current_knowledge = self._storage.load_knowledge(agent_id)
            # Merge knowledge artifacts
            merged_artifacts = {**current_knowledge.artifacts}

            # Convert updated_knowledge dict to proper KnowledgeItem objects if needed
            for path, data in result.updated_knowledge.items():
                if isinstance(data, dict):
                    merged_artifacts[path] = KnowledgeItem(
                        summary=data.get('summary', ''),
                        purpose=data.get('purpose', ''),
                        last_modified_by_task=data.get('last_modified_by_task', '')
                    )
                else:
                    merged_artifacts[path] = data

            new_knowledge = AgentKnowledge(artifacts=merged_artifacts)
            self._storage.save_knowledge(agent_id, new_knowledge)

        # Append history entry
        if result.history_entry:
            # Extract full ai_response BEFORE truncating for summary
            full_ai_response = result.history_entry.get('ai_response', '')

            # Map AgentExecutor dict fields to HistoryEntry fields
            history_entry = HistoryEntry(
                _id=str(uuid.uuid4()),  # Always generate unique ID
                agent_id=result.history_entry.get('agent_id', agent_id),
                task_id=result.history_entry.get('task_id', str(uuid.uuid4())),  # Fallback UUID if missing
                status=result.history_entry.get('status', 'completed'),
                summary=full_ai_response[:200] + '...' if len(full_ai_response) > 200 else full_ai_response,  # Truncated summary
                git_commit_hash=result.history_entry.get('git_commit_hash', '')
            )

            # 🔥 Pass FULL ai_response to append_to_history for conversation context
            self._storage.append_to_history(
                agent_id=agent_id,
                entry=history_entry,
                user_input=task.user_input,
                ai_response=full_ai_response  # Full response for building next prompts
            )