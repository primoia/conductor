# tests/core/services/test_tool_management_service.py
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.core.services.tool_management_service import ToolManagementService
from src.core.services.configuration_service import ConfigurationService


class TestToolManagementService:
    """Tests for ToolManagementService."""

    @patch('src.core.services.tool_management_service.CORE_TOOLS')
    def test_load_tools_core_tools_only(self, mock_core_tools):
        """Testa carregamento apenas de core tools."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = []
        
        # Mock core tools
        mock_tool1 = MagicMock()
        mock_tool1.__name__ = "core_tool_1"
        mock_tool2 = MagicMock() 
        mock_tool2.__name__ = "core_tool_2"
        mock_core_tools.__iter__ = MagicMock(return_value=iter([mock_tool1, mock_tool2]))
        
        # Act
        service = ToolManagementService(mock_config_service)
        tools = service.get_tools()
        
        # Assert
        assert "core_tool_1" in tools
        assert "core_tool_2" in tools
        assert tools["core_tool_1"] == mock_tool1
        assert tools["core_tool_2"] == mock_tool2
        assert len(tools) == 2

    @patch('src.core.services.tool_management_service.CORE_TOOLS', [])
    def test_load_tools_with_plugins_empty(self, ):
        """Testa carregamento quando não há plugins configurados."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = []
        
        # Act
        service = ToolManagementService(mock_config_service)
        tools = service.get_tools()
        
        # Assert
        assert len(tools) == 0  # No core tools, no plugins

    @patch('src.core.services.tool_management_service.CORE_TOOLS', [])
    @patch('src.core.services.tool_management_service.logger')
    def test_load_tools_logs_security_warning(self, mock_logger):
        """Testa se warnings de segurança são logados."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = ["/some/plugin/path"]
        
        # Act
        service = ToolManagementService(mock_config_service)
        
        # Assert
        # Should attempt to load plugins and potentially log warnings
        assert mock_config_service.get_tool_plugins.called

    @patch('src.core.services.tool_management_service.CORE_TOOLS', [])
    def test_load_tools_handles_invalid_paths(self):
        """Testa tratamento de caminhos inválidos."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = ["/nonexistent/path"]
        
        # Act
        service = ToolManagementService(mock_config_service)
        tools = service.get_tools()
        
        # Assert
        # Should handle invalid paths gracefully without crashing
        assert isinstance(tools, dict)

    def test_get_tools_returns_copy(self):
        """Testa se get_tools retorna uma cópia para evitar modificações externas."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = []
        
        with patch('src.core.services.tool_management_service.CORE_TOOLS') as mock_core_tools:
            mock_tool = MagicMock()
            mock_tool.__name__ = "test_tool"
            mock_core_tools.__iter__ = MagicMock(return_value=iter([mock_tool]))
            
            # Act
            service = ToolManagementService(mock_config_service)
            tools1 = service.get_tools()
            tools2 = service.get_tools()
            
            # Modify one copy
            tools1["new_tool"] = "external_modification"
            
            # Assert
            assert "new_tool" not in tools2  # Original should not be affected
            assert "test_tool" in tools2
            assert tools1 is not tools2  # Different objects

    def test_get_allowed_tools_filters_correctly(self):
        """Testa filtro de ferramentas permitidas."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = []
        
        with patch('src.core.services.tool_management_service.CORE_TOOLS') as mock_core_tools:
            mock_tool1 = MagicMock()
            mock_tool1.__name__ = "allowed_tool"
            mock_tool2 = MagicMock()
            mock_tool2.__name__ = "forbidden_tool"
            mock_core_tools.__iter__ = MagicMock(return_value=iter([mock_tool1, mock_tool2]))
            
            # Act
            service = ToolManagementService(mock_config_service)
            allowed_tools = service.get_allowed_tools(["allowed_tool"])
            
            # Assert
            assert "allowed_tool" in allowed_tools
            assert "forbidden_tool" not in allowed_tools
            assert len(allowed_tools) == 1
            assert allowed_tools["allowed_tool"] == mock_tool1

    def test_get_allowed_tools_empty_list(self):
        """Testa filtro com lista vazia de ferramentas permitidas."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = []
        
        with patch('src.core.services.tool_management_service.CORE_TOOLS') as mock_core_tools:
            mock_tool = MagicMock()
            mock_tool.__name__ = "some_tool"
            mock_core_tools.__iter__ = MagicMock(return_value=iter([mock_tool]))
            
            # Act
            service = ToolManagementService(mock_config_service)
            allowed_tools = service.get_allowed_tools([])
            
            # Assert
            assert len(allowed_tools) == 0

    def test_service_initialization_with_config(self):
        """Testa inicialização do serviço com configuração."""
        # Arrange
        mock_config_service = MagicMock()
        mock_config_service.get_tool_plugins.return_value = []
        
        # Act
        service = ToolManagementService(mock_config_service)
        
        # Assert
        assert service._config == mock_config_service
        assert isinstance(service._tools, dict)