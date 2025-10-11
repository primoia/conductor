# tests/api/test_history_persistence.py
"""
Teste para validar que ambos os fluxos (REPL e API) salvam no history global.
"""
import pytest
import uuid
from unittest.mock import Mock, MagicMock


class TestHistoryPersistence:
    """Testa que ambos os fluxos salvam no history global do agente."""

    def test_repl_flow_saves_to_global_history(self):
        """
        Valida que execução via REPL (conductor.py) salva no history global.

        Este teste verifica que TaskExecutionService._persist_task_result
        chama storage.append_to_history corretamente.
        """
        from src.core.services.task_execution_service import TaskExecutionService
        from src.core.domain import TaskDTO, TaskResultDTO, HistoryEntry

        # Arrange: Criar mocks
        mock_storage = MagicMock()
        mock_tool_service = MagicMock()
        mock_config_service = MagicMock()

        # Create service
        task_service = TaskExecutionService(
            agent_storage_service=MagicMock(get_storage=lambda: mock_storage),
            tool_service=mock_tool_service,
            config_service=mock_config_service
        )

        # Create task and result
        task = TaskDTO(
            agent_id="test_agent",
            user_input="REPL test input",
            context={"instance_id": "repl-session-123"}
        )

        result = TaskResultDTO(
            status="success",
            output="REPL test output",
            metadata={},
            history_entry={
                "agent_id": "test_agent",
                "task_id": str(uuid.uuid4()),
                "status": "completed",
                "ai_response": "Full AI response from REPL flow",
                "git_commit_hash": ""
            }
        )

        # Act: Call _persist_task_result directly
        task_service._persist_task_result("test_agent", task, result)

        # Assert: Verify append_to_history was called
        mock_storage.append_to_history.assert_called_once()
        call_args = mock_storage.append_to_history.call_args

        assert call_args.kwargs['agent_id'] == "test_agent"
        assert call_args.kwargs['user_input'] == "REPL test input"
        assert call_args.kwargs['ai_response'] == "Full AI response from REPL flow"
        assert call_args.kwargs['instance_id'] == "repl-session-123"
