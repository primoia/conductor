# tests/core/test_conductor_service.py
import pytest
from unittest.mock import patch, MagicMock

from src.core.conductor_service import ConductorService
from src.core.domain import AgentDefinition, TaskDTO, TaskResultDTO


class TestConductorServiceOrchestration:
    """Tests for ConductorService orchestration functionality."""
    
    @patch('src.core.conductor_service.ConfigurationService')
    @patch('src.core.conductor_service.StorageService')
    @patch('src.core.conductor_service.AgentStorageService')
    @patch('src.core.conductor_service.AgentDiscoveryService')
    @patch('src.core.conductor_service.ToolManagementService')
    @patch('src.core.conductor_service.TaskExecutionService')
    def test_initialization_creates_all_services(self, mock_task_service, mock_tool_service,
                                                mock_agent_service, mock_agent_storage_service, mock_storage_service, mock_config_service):
        """Testa se a inicialização cria todos os serviços especializados."""
        # Criar instâncias mock dos serviços
        mock_config_instance = MagicMock()
        mock_storage_instance = MagicMock()
        mock_agent_storage_instance = MagicMock()
        mock_agent_instance = MagicMock()
        mock_tool_instance = MagicMock()
        mock_task_instance = MagicMock()

        mock_config_service.return_value = mock_config_instance
        mock_storage_service.return_value = mock_storage_instance
        mock_agent_storage_service.return_value = mock_agent_storage_instance
        mock_agent_service.return_value = mock_agent_instance
        mock_tool_service.return_value = mock_tool_instance
        mock_task_service.return_value = mock_task_instance
        
        service = ConductorService("test_config.yaml")
        
        # Verificar se todos os serviços foram inicializados
        mock_config_service.assert_called_once_with("test_config.yaml")
        mock_storage_service.assert_called_once_with(mock_config_instance)
        mock_agent_storage_service.assert_called_once_with(mock_config_instance)
        mock_agent_service.assert_called_once_with(mock_storage_instance)
        mock_tool_service.assert_called_once_with(mock_config_instance)
        mock_task_service.assert_called_once_with(
            mock_agent_storage_instance,
            mock_tool_instance,
            mock_config_instance
        )

    @patch('src.core.conductor_service.ConfigurationService')
    @patch('src.core.conductor_service.StorageService') 
    @patch('src.core.conductor_service.AgentDiscoveryService')
    @patch('src.core.conductor_service.ToolManagementService')
    @patch('src.core.conductor_service.TaskExecutionService')
    def test_discover_agents_delegates_to_agent_service(self, mock_task_service, mock_tool_service,
                                                      mock_agent_service, mock_storage_service, mock_config_service):
        """Testa se discover_agents delega para AgentDiscoveryService."""
        # Criar instâncias mock dos serviços
        mock_config_instance = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        mock_config_instance.get_storage_config.return_value = mock_storage_config

        mock_storage_instance = MagicMock()
        mock_agent_instance = MagicMock()
        mock_tool_instance = MagicMock()
        mock_task_instance = MagicMock()

        mock_config_service.return_value = mock_config_instance
        mock_storage_service.return_value = mock_storage_instance
        mock_agent_service.return_value = mock_agent_instance
        mock_tool_service.return_value = mock_tool_instance
        mock_task_service.return_value = mock_task_instance
        
        service = ConductorService()
        
        # Mock do retorno do serviço de agente
        mock_agents = [
            AgentDefinition(name="Test Agent 1", version="1.0", schema_version="1.0", 
                           description="Test", author="Test"),
            AgentDefinition(name="Test Agent 2", version="2.0", schema_version="1.0",
                           description="Test", author="Test")
        ]
        mock_agent_instance.discover_agents.return_value = mock_agents
        
        result = service.discover_agents()
        
        assert result == mock_agents
        mock_agent_instance.discover_agents.assert_called_once()

    @patch('src.core.conductor_service.ConfigurationService')
    @patch('src.core.conductor_service.StorageService') 
    @patch('src.core.conductor_service.AgentDiscoveryService')
    @patch('src.core.conductor_service.ToolManagementService')
    @patch('src.core.conductor_service.TaskExecutionService')
    def test_execute_task_delegates_to_execution_service(self, mock_task_service, mock_tool_service,
                                                       mock_agent_service, mock_storage_service, mock_config_service):
        """Testa se execute_task delega para TaskExecutionService."""
        # Criar instâncias mock dos serviços
        mock_config_instance = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        mock_config_instance.get_storage_config.return_value = mock_storage_config

        mock_storage_instance = MagicMock()
        mock_agent_instance = MagicMock()
        mock_tool_instance = MagicMock()
        mock_task_instance = MagicMock()

        mock_config_service.return_value = mock_config_instance
        mock_storage_service.return_value = mock_storage_instance
        mock_agent_service.return_value = mock_agent_instance
        mock_tool_service.return_value = mock_tool_instance
        mock_task_service.return_value = mock_task_instance
        
        service = ConductorService()
        
        # Mock do retorno do serviço de execução
        task = TaskDTO(agent_id="test-agent", user_input="test input")
        expected_result = TaskResultDTO(status="success", output="Task completed", metadata={})
        mock_task_instance.execute_task.return_value = expected_result
        
        result = service.execute_task(task)
        
        assert result == expected_result
        mock_task_instance.execute_task.assert_called_once_with(task)

    @patch('src.core.conductor_service.ConfigurationService')
    @patch('src.core.conductor_service.StorageService') 
    @patch('src.core.conductor_service.AgentDiscoveryService')
    @patch('src.core.conductor_service.ToolManagementService')
    @patch('src.core.conductor_service.TaskExecutionService')
    def test_load_tools_delegates_to_tool_service(self, mock_task_service, mock_tool_service,
                                                 mock_agent_service, mock_storage_service, mock_config_service):
        """Testa se load_tools delega para ToolManagementService."""
        # Criar instâncias mock dos serviços
        mock_config_instance = MagicMock()
        mock_storage_config = MagicMock()
        mock_storage_config.type = "filesystem"
        mock_storage_config.path = "/test/path"
        mock_config_instance.get_storage_config.return_value = mock_storage_config

        mock_storage_instance = MagicMock()
        mock_agent_instance = MagicMock()
        mock_tool_instance = MagicMock()
        mock_task_instance = MagicMock()

        mock_config_service.return_value = mock_config_instance
        mock_storage_service.return_value = mock_storage_instance
        mock_agent_service.return_value = mock_agent_instance
        mock_tool_service.return_value = mock_tool_instance
        mock_task_service.return_value = mock_task_instance
        
        service = ConductorService()
        
        service.load_tools()
        
        mock_tool_instance.load_tools.assert_called_once()


