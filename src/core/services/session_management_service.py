# src/core/services/session_management_service.py
from src.infrastructure.utils import cleanup_orphan_sessions
from src.core.services.configuration_service import ConfigurationService


class SessionManagementService:
    """Service responsible for session cleanup and management."""

    def __init__(self, config_service: ConfigurationService):
        self._config_service = config_service

    def cleanup_orphan_sessions(self) -> bool:
        """Clean up orphan sessions based on storage configuration."""
        try:
            storage_config = self._config_service.load_storage_config()
            
            if storage_config.get('type') == 'filesystem':
                workspace_path = storage_config.get('workspace_path')
                if workspace_path:
                    cleanup_orphan_sessions(workspace_path)
                    return True
            return True
        except Exception:
            return False