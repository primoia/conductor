# tests/api/test_dispatch.py
"""
Tests for the Agent Dispatch endpoint.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routes.dispatch import router, _ensure_conversation


class TestDispatchEndpoint:
    """Tests for POST /agents/dispatch."""

    def _make_client(self):
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @patch("src.core.services.mongo_task_client.MongoTaskClient")
    @patch("src.container.container")
    @patch("src.core.services.agent_discovery_service.AgentDiscoveryService")
    @patch("src.api.routes.dispatch._ensure_screenplay")
    def test_dispatch_creates_task(self, mock_ensure_sp, mock_disc_cls, mock_container, mock_task_cls):
        """Verify dispatch creates a task in MongoDB and returns task_id."""
        mock_agent_def = MagicMock()
        mock_agent_def.timeout = 300

        mock_disc = MagicMock()
        mock_disc.get_agent_definition.return_value = mock_agent_def
        mock_disc.get_full_prompt.return_value = "<prompt>test</prompt>"
        mock_disc_cls.return_value = mock_disc

        mock_container.get_ai_provider.return_value = "claude"
        mock_ensure_sp.return_value = "sp-123"

        mock_task_client = MagicMock()
        mock_task_client.submit_task.return_value = "task-abc"
        mock_task_cls.return_value = mock_task_client

        client = self._make_client()
        resp = client.post("/agents/dispatch", json={
            "target_agent_id": "Support_Agent",
            "input": "Investigate this alert",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["target_agent_id"] == "Support_Agent"
        assert data["screenplay_id"] == "sp-123"
        assert "conversation_id" in data
        assert data["status"] == "pending"

        # Verify submit_task was called
        mock_task_client.submit_task.assert_called_once()
        call_kwargs = mock_task_client.submit_task.call_args.kwargs
        assert call_kwargs["is_councilor_execution"] is False
        assert call_kwargs["agent_id"] == "Support_Agent"

    @patch("src.core.services.agent_discovery_service.AgentDiscoveryService")
    def test_dispatch_rejects_unknown_agent(self, mock_disc_cls):
        """Verify dispatch returns 404 for unknown agent."""
        mock_disc = MagicMock()
        mock_disc.get_agent_definition.return_value = None
        mock_disc_cls.return_value = mock_disc

        client = self._make_client()
        resp = client.post("/agents/dispatch", json={
            "target_agent_id": "NonExistent_Agent",
            "input": "test",
        })

        assert resp.status_code == 404

    @patch("src.core.services.mongo_task_client.MongoTaskClient")
    @patch("src.container.container")
    @patch("src.core.services.agent_discovery_service.AgentDiscoveryService")
    @patch("src.api.routes.dispatch._ensure_screenplay")
    def test_dispatch_preserves_conversation_id(self, mock_ensure_sp, mock_disc_cls, mock_container, mock_task_cls):
        """Verify dispatch reuses provided conversation_id."""
        mock_agent_def = MagicMock()
        mock_agent_def.timeout = 300

        mock_disc = MagicMock()
        mock_disc.get_agent_definition.return_value = mock_agent_def
        mock_disc.get_full_prompt.return_value = "<prompt>test</prompt>"
        mock_disc_cls.return_value = mock_disc

        mock_container.get_ai_provider.return_value = "claude"
        mock_ensure_sp.return_value = "sp-456"

        mock_task_client = MagicMock()
        mock_task_client.submit_task.return_value = "task-xyz"
        mock_task_cls.return_value = mock_task_client

        client = self._make_client()
        resp = client.post("/agents/dispatch", json={
            "target_agent_id": "DevOps_Agent",
            "input": "Restart billing container",
            "conversation_id": "existing-conv-123",
            "screenplay_id": "sp-456",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] == "existing-conv-123"
        assert data["screenplay_id"] == "sp-456"

        # Verify conversation_id was passed through
        call_kwargs = mock_task_client.submit_task.call_args.kwargs
        assert call_kwargs["conversation_id"] == "existing-conv-123"
        assert call_kwargs["screenplay_id"] == "sp-456"


class TestEnsureConversation:
    """Tests for _ensure_conversation helper."""

    def test_returns_existing_id(self):
        assert _ensure_conversation("conv-123") == "conv-123"

    def test_generates_new_uuid(self):
        result = _ensure_conversation(None)
        assert len(result) == 36  # UUID format
        assert "-" in result
