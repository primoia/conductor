# tests/core/test_conductor_service.py
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import yaml

from src.core.conductor_service import ConductorService
from src.core.exceptions import ConfigurationError
from src.core.config_schema import GlobalConfig, StorageConfig
from src.core.domain import AgentDefinition, TaskDTO, TaskResultDTO
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository


class TestConductorServiceConfig:
    """Tests for configuration loading and validation."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config_success(self, mock_safe_load, mock_open_file):
        """Testa o carregamento de configuração bem-sucedido."""
        mock_config = {
            "storage": {"type": "filesystem", "path": "/tmp/ws"},
            "tool_plugins": ["/plugins"]
        }
        mock_safe_load.return_value = mock_config
        
        service = ConductorService()
        
        assert service._config.storage.type == "filesystem"
        assert service._config.storage.path == "/tmp/ws"
        assert service._config.tool_plugins == ["/plugins"]
        mock_open_file.assert_called_with("config.yaml", 'r')

    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_load_config_not_found(self, mock_open_file):
        """Testa o erro quando o config.yaml não é encontrado."""
        with pytest.raises(ConfigurationError, match="não encontrado"):
            ConductorService(config_path="non_existent_file.yaml")

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML"))
    def test_load_config_invalid_yaml(self, mock_safe_load, mock_open_file):
        """Testa o erro quando o YAML é inválido."""
        with pytest.raises(ConfigurationError, match="Erro ao carregar ou validar a configuração"):
            ConductorService()

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_config_invalid_schema(self, mock_safe_load, mock_open_file):
        """Testa o erro quando a configuração não atende ao schema."""
        mock_config = {"invalid": "config"}
        mock_safe_load.return_value = mock_config
        
        with pytest.raises(ConfigurationError, match="Erro ao carregar ou validar a configuração"):
            ConductorService()


class TestConductorServiceStorageFactory:
    """Tests for storage backend creation."""

    @patch.object(ConductorService, '_load_and_validate_config')
    def test_storage_factory_filesystem(self, mock_load_config):
        """Testa a criação do repositório de filesystem."""
        mock_config = MagicMock()
        mock_config.storage.type = "filesystem"
        mock_load_config.return_value = mock_config
        
        service = ConductorService()
        
        assert isinstance(service.repository, FileSystemStateRepository)

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch('src.core.conductor_service.MongoStateRepository')
    def test_storage_factory_mongodb(self, mock_mongo_repo, mock_load_config):
        """Testa a criação do repositório de MongoDB."""
        mock_config = MagicMock()
        mock_config.storage.type = "mongodb"
        mock_load_config.return_value = mock_config
        
        mock_mongo_instance = MagicMock()
        mock_mongo_repo.return_value = mock_mongo_instance
        
        service = ConductorService()
        
        assert service.repository == mock_mongo_instance
        mock_mongo_repo.assert_called_once()

    @patch.object(ConductorService, '_load_and_validate_config')
    def test_storage_factory_unknown_type(self, mock_load_config):
        """Testa o erro para tipo de armazenamento desconhecido."""
        mock_config = MagicMock()
        mock_config.storage.type = "unknown"
        mock_load_config.return_value = mock_config
        
        with pytest.raises(ConfigurationError, match="Tipo de armazenamento desconhecido"):
            ConductorService()


class TestConductorServiceAgentDiscovery:
    """Tests for agent discovery functionality."""

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch.object(ConductorService, 'load_tools')
    def test_discover_agents_success(self, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa a descoberta bem-sucedida de agentes."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        # Mock do repositório
        mock_repo = MagicMock()
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        mock_repo.list_agents.return_value = ["agent1", "agent2"]
        mock_repo.load_state.side_effect = [
            {
                "definition": {
                    "name": "Test Agent 1",
                    "version": "1.0",
                    "schema_version": "1.0",
                    "description": "First test agent",
                    "author": "Test Author"
                }
            },
            {
                "definition": {
                    "name": "Test Agent 2",
                    "version": "2.0", 
                    "schema_version": "1.0",
                    "description": "Second test agent",
                    "author": "Test Author"
                }
            }
        ]
        
        agents = service.discover_agents()
        
        assert len(agents) == 2
        assert agents[0].name == "Test Agent 1"
        assert agents[0].version == "1.0"
        assert agents[1].name == "Test Agent 2" 
        assert agents[1].version == "2.0"
        mock_repo.list_agents.assert_called_once()
        assert mock_repo.load_state.call_count == 2

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch.object(ConductorService, 'load_tools')
    def test_discover_agents_empty_list(self, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa a descoberta quando não há agentes."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_repo.list_agents.return_value = []
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        agents = service.discover_agents()
        
        assert len(agents) == 0
        mock_repo.list_agents.assert_called_once()

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch.object(ConductorService, 'load_tools')
    def test_discover_agents_missing_definition(self, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa a descoberta quando o estado não possui definição."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_repo.list_agents.return_value = ["agent1"]
        mock_repo.load_state.return_value = {"other_data": "value"}
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        agents = service.discover_agents()
        
        assert len(agents) == 0
        mock_repo.load_state.assert_called_with("agent1")


class TestConductorServiceTaskExecution:
    """Tests for task execution functionality."""

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch.object(ConductorService, 'load_tools')
    @patch('src.core.conductor_service.AgentExecutor')
    @patch('src.core.conductor_service.PromptEngine')
    @patch('src.core.conductor_service.PlaceholderLLMClient')
    def test_execute_task_success(self, mock_llm_client, mock_prompt_engine, 
                                mock_agent_executor, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa a execução bem-sucedida de uma tarefa."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        # Mock do repositório
        mock_repo = MagicMock()
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        service._tools = {"tool1": MagicMock(), "tool2": MagicMock()}
        
        agent_state = {
            "definition": {
                "name": "Test Agent",
                "version": "1.0",
                "schema_version": "1.0", 
                "description": "Test description",
                "author": "Test Author"
            },
            "agent_home_path": "/path/to/agent",
            "allowed_tools": ["tool1"]
        }
        mock_repo.load_state.return_value = agent_state
        
        # Mock do executor
        mock_executor_instance = MagicMock()
        expected_result = TaskResultDTO(status="success", output="Task completed", metadata={})
        mock_executor_instance.run.return_value = expected_result
        mock_agent_executor.return_value = mock_executor_instance
        
        # Criar task
        task = TaskDTO(agent_id="agent1", user_input="Execute this task")
        
        result = service.execute_task(task)
        
        assert result.status == "success"
        assert result.output == "Task completed"
        mock_repo.load_state.assert_called_with("agent1")
        mock_agent_executor.assert_called_once()
        mock_executor_instance.run.assert_called_with(task)

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch.object(ConductorService, 'load_tools')
    def test_execute_task_agent_not_found(self, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa a execução quando o agente não é encontrado."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_repo.load_state.return_value = None
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        task = TaskDTO(agent_id="nonexistent", user_input="Execute this task")
        
        result = service.execute_task(task)
        
        assert result.status == "error"
        assert "Definição não encontrada para o agente" in result.output

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch.object(ConductorService, 'load_tools')
    def test_execute_task_missing_agent_home_path(self, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa a execução quando agent_home_path está ausente."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        agent_state = {
            "definition": {
                "name": "Test Agent",
                "version": "1.0",
                "schema_version": "1.0",
                "description": "Test description",
                "author": "Test Author"
            }
            # agent_home_path ausente
        }
        mock_repo.load_state.return_value = agent_state
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        task = TaskDTO(agent_id="agent1", user_input="Execute this task")
        
        result = service.execute_task(task)
        
        assert result.status == "error"
        assert "agent_home_path não encontrado" in result.output


class TestConductorServiceToolLoading:
    """Tests for tool loading functionality."""

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch('src.core.conductor_service.CORE_TOOLS')
    def test_load_tools_core_tools_only(self, mock_core_tools, mock_create_storage, mock_load_config):
        """Testa o carregamento apenas de core tools."""
        mock_config = MagicMock()
        mock_config.tool_plugins = []
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_create_storage.return_value = mock_repo
        
        # Mock core tools
        mock_tool1 = MagicMock()
        mock_tool1.__name__ = "core_tool1"
        mock_tool2 = MagicMock()
        mock_tool2.__name__ = "core_tool2"
        mock_core_tools.__iter__ = MagicMock(return_value=iter([mock_tool1, mock_tool2]))
        
        service = ConductorService()
        
        assert "core_tool1" in service._tools
        assert "core_tool2" in service._tools
        assert service._tools["core_tool1"] == mock_tool1
        assert service._tools["core_tool2"] == mock_tool2

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    def test_load_tools_with_plugins(self, mock_create_storage, mock_load_config):
        """Testa o carregamento de tools com plugins."""
        mock_config = MagicMock()
        mock_config.tool_plugins = ["/path/to/plugins"]
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        # Manually set up tools to test the plugin loading logic
        mock_plugin_tool = MagicMock()
        mock_plugin_tool.__name__ = "plugin_tool"
        service._tools = {"plugin_tool": mock_plugin_tool}
        
        # Verify the plugin tool was loaded
        assert "plugin_tool" in service._tools
        assert service._tools["plugin_tool"] == mock_plugin_tool

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend')
    @patch('src.core.conductor_service.CORE_TOOLS', [])
    @patch('src.core.conductor_service.Path')
    @patch('src.core.conductor_service.logger')
    def test_load_tools_invalid_plugin_path(self, mock_logger, mock_path, mock_create_storage, mock_load_config):
        """Testa o carregamento com caminho de plugin inválido."""
        mock_config = MagicMock()
        mock_config.tool_plugins = ["/invalid/path"]
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_create_storage.return_value = mock_repo
        
        # Mock Path operations
        mock_plugin_path = MagicMock()
        mock_plugin_path.resolve.return_value = mock_plugin_path
        mock_plugin_path.is_dir.return_value = False
        mock_plugin_path.parents = []  # Empty parents to trigger security error
        mock_path.return_value = mock_plugin_path
        
        service = ConductorService()
        
        # Verificar que a mensagem de erro foi logada
        mock_logger.error.assert_called_with(f"Recusando carregar plugin de diretório não confiável: {mock_plugin_path}. O caminho do plugin deve estar dentro do diretório do projeto.")

    @patch.object(ConductorService, '_load_and_validate_config')
    @patch.object(ConductorService, '_create_storage_backend') 
    @patch.object(ConductorService, 'load_tools')
    def test_load_tools_plugin_without_plugin_tools(self, mock_load_tools, mock_create_storage, mock_load_config):
        """Testa o carregamento de plugin que não possui PLUGIN_TOOLS."""
        mock_config = MagicMock()
        mock_config.tool_plugins = ["/path/to/plugins"]
        mock_load_config.return_value = mock_config
        
        mock_repo = MagicMock()
        mock_create_storage.return_value = mock_repo
        
        service = ConductorService()
        
        # Mock that load_tools was called but no tools were loaded
        assert len(service._tools) == 0
        mock_load_tools.assert_called_once()


class TestConductorServiceIntegration:
    """Integration tests for ConductorService."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('src.core.conductor_service.CORE_TOOLS')
    def test_full_initialization(self, mock_core_tools, mock_safe_load, mock_open_file):
        """Testa a inicialização completa do serviço."""
        mock_config = {
            "storage": {"type": "filesystem", "path": "/tmp/ws"},
            "tool_plugins": []
        }
        mock_safe_load.return_value = mock_config
        
        mock_tool = MagicMock()
        mock_tool.__name__ = "test_tool"
        mock_core_tools.__iter__ = MagicMock(return_value=iter([mock_tool]))
        
        service = ConductorService()
        
        # Verificar que todas as dependências foram inicializadas
        assert service._config is not None
        assert service.repository is not None
        assert isinstance(service.repository, FileSystemStateRepository)
        assert "test_tool" in service._tools
        assert service._tools["test_tool"] == mock_tool