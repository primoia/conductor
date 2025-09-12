# tests/core/services/test_session_management_service.py
import pytest
from unittest.mock import MagicMock, patch

from src.core.services.session_management_service import SessionManagementService
from src.core.services.configuration_service import ConfigurationService


class TestSessionManagementService:
    """Tests for SessionManagementService."""

    def test_cleanup_orphan_sessions_filesystem_success(self):
        """Test successful cleanup for filesystem backend."""
        # Setup mock
        mock_config_service = MagicMock()
        mock_config_service.load_storage_config.return_value = {
            'type': 'filesystem',
            'workspace_path': '/test/workspace'
        }
        
        service = SessionManagementService(mock_config_service)
        
        # Mock the cleanup function
        with patch('src.core.services.session_management_service.cleanup_orphan_sessions') as mock_cleanup:
            # Test
            result = service.cleanup_orphan_sessions()
        
        # Verify
        assert result is True
        mock_cleanup.assert_called_once_with('/test/workspace')

    def test_cleanup_orphan_sessions_non_filesystem_backend(self):
        """Test cleanup returns True for non-filesystem backends."""
        # Setup mock
        mock_config_service = MagicMock()
        mock_config_service.load_storage_config.return_value = {
            'type': 'mongodb'
        }
        
        service = SessionManagementService(mock_config_service)
        
        # Test
        result = service.cleanup_orphan_sessions()
        
        # Verify
        assert result is True

    def test_cleanup_orphan_sessions_handles_exceptions(self):
        """Test cleanup handles exceptions gracefully."""
        # Setup mock that raises exception
        mock_config_service = MagicMock()
        mock_config_service.load_storage_config.side_effect = Exception("Config error")
        
        service = SessionManagementService(mock_config_service)
        
        # Test
        result = service.cleanup_orphan_sessions()
        
        # Verify
        assert result is False

    def test_cleanup_orphan_sessions_no_workspace_path(self):
        """Test cleanup when workspace_path is not provided."""
        # Setup mock
        mock_config_service = MagicMock()
        mock_config_service.load_storage_config.return_value = {
            'type': 'filesystem'
            # No workspace_path
        }
        
        service = SessionManagementService(mock_config_service)
        
        # Test
        result = service.cleanup_orphan_sessions()
        
        # Verify
        assert result is True  # Should return True even without path