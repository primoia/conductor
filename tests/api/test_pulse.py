# tests/api/test_pulse.py
"""
Tests for SAGA-016 Phase 2: Pulse Event Service and API routes.
Updated for dispatch-based architecture.
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from src.core.services.pulse_event_service import PulseEvent, PulseEventService


class TestPulseEvent:
    """Tests for the PulseEvent data class."""

    def test_event_creation(self):
        ev = PulseEvent(
            source="test",
            severity=PulseEvent.SEVERITY_CRITICAL,
            title="Test Alert",
            detail="Something happened",
        )
        assert ev.source == "test"
        assert ev.severity == "critical"
        assert ev.title == "Test Alert"
        assert ev.timestamp is not None

    def test_event_to_dict(self):
        ev = PulseEvent(
            source="mesh_watcher",
            severity="warning",
            title="Sidecar down",
            detail="svc-x went offline",
            metadata={"node": "svc-x"},
        )
        d = ev.to_dict()
        assert d["source"] == "mesh_watcher"
        assert d["metadata"]["node"] == "svc-x"
        assert "timestamp" in d

    def test_event_to_prompt_text(self):
        ev = PulseEvent(
            source="rabbitmq_dlq",
            severity="warning",
            title="Dead letter from billing",
            detail="Payment message failed",
        )
        text = ev.to_prompt_text()
        assert "SYSTEM EVENT - WARNING" in text
        assert "rabbitmq_dlq" in text
        assert "Dead letter from billing" in text


class TestPulseEventService:
    """Tests for the PulseEventService core logic."""

    def test_record_event(self):
        svc = PulseEventService()
        ev = PulseEvent(
            source="test", severity="info", title="Test", detail="test detail",
        )
        svc._record_event(ev)
        assert len(svc._event_log) == 1
        assert svc._event_log[0]["title"] == "Test"

    def test_get_events_ordering(self):
        svc = PulseEventService()
        for i in range(5):
            ev = PulseEvent(
                source="test", severity="info",
                title=f"Event {i}", detail=f"Detail {i}",
            )
            svc._record_event(ev)

        events = svc.get_events(limit=3)
        # Most recent first
        assert events[0]["title"] == "Event 4"
        assert events[2]["title"] == "Event 2"
        assert len(events) == 3

    def test_event_log_max_size(self):
        svc = PulseEventService()
        svc._max_log_size = 10
        for i in range(20):
            ev = PulseEvent(
                source="test", severity="info",
                title=f"Event {i}", detail="x",
            )
            svc._record_event(ev)
        assert len(svc._event_log) <= 10

    def test_mesh_health_change_detection(self):
        """Test that health changes are detected between snapshots."""
        svc = PulseEventService()

        # Set up initial snapshot
        svc._previous_mesh_snapshot = {
            "svc-a": "healthy",
            "svc-b": "healthy",
            "svc-c": "unhealthy",
        }

        # Create new mesh data with changes
        from src.core.services.mcp_mesh_service import MCPMeshService, MCPNode

        mesh_svc = MCPMeshService()
        mesh_svc._nodes = {
            "svc-a": MCPNode(name="svc-a", url="http://a", status="unhealthy", error="timeout"),
            "svc-b": MCPNode(name="svc-b", url="http://b", status="healthy"),
            "svc-c": MCPNode(name="svc-c", url="http://c", status="healthy"),
            # svc-d is new
            "svc-d": MCPNode(name="svc-d", url="http://d", status="healthy"),
        }

        with patch("src.core.services.mcp_mesh_service.mesh_service", mesh_svc):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(svc._check_mesh_health_changes())

        # Should have detected:
        # - svc-a went from healthy to unhealthy (CRITICAL)
        # - svc-c recovered (INFO)
        # - svc-d discovered (INFO)
        events = svc.get_events()
        titles = [e["title"] for e in events]

        assert any("DOWN" in t and "svc-a" in t for t in titles)
        assert any("RECOVERED" in t and "svc-c" in t for t in titles)
        assert any("discovered" in t and "svc-d" in t for t in titles)


class TestPulseAPIRoute:
    """Tests for the Pulse API endpoints."""

    def test_pulse_status_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.routes.pulse import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        resp = client.get("/system/pulse/status")

        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert "event_count" in data

    def test_pulse_events_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.routes.pulse import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        # Inject an event
        from src.core.services.pulse_event_service import pulse_service
        pulse_service._event_log.append({
            "source": "test",
            "severity": "info",
            "title": "Test Event",
            "detail": "Testing",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "metadata": {},
        })

        client = TestClient(app)
        resp = client.get("/system/pulse/events")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

        # Cleanup
        pulse_service._event_log.clear()

    def test_pulse_events_filter(self):
        from fastapi.testclient import TestClient
        from src.api.routes.pulse import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        from src.core.services.pulse_event_service import pulse_service
        pulse_service._event_log.extend([
            {"source": "mesh_watcher", "severity": "critical", "title": "Down", "detail": "x", "timestamp": "t", "metadata": {}},
            {"source": "rabbitmq_dlq", "severity": "warning", "title": "DLQ", "detail": "y", "timestamp": "t", "metadata": {}},
        ])

        client = TestClient(app)
        resp = client.get("/system/pulse/events?severity=critical")

        assert resp.status_code == 200
        data = resp.json()
        assert all(e["severity"] == "critical" for e in data["events"])

        # Cleanup
        pulse_service._event_log.clear()

    @patch("src.api.routes.pulse.os.getenv")
    def test_screenplay_log_write(self, mock_getenv):
        """Test screenplay log write with mocked MongoDB."""
        mock_getenv.side_effect = lambda k, d=None: {
            "MONGO_URI": "mongodb://localhost:27017",
            "MONGO_DATABASE": "test_db",
        }.get(k, d)

        from fastapi.testclient import TestClient
        from src.api.routes.pulse import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        with patch("pymongo.MongoClient") as mock_mongo:
            mock_collection = MagicMock()
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_client = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_mongo.return_value = mock_client

            client = TestClient(app)
            resp = client.post("/system/pulse/screenplay-log", json={
                "agent_id": "Support_Agent",
                "entry": "Found unhealthy sidecar, recommending restart",
                "severity": "warning",
                "category": "finding",
            })

            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "written"
            assert "slog_" in data["log_id"]


class TestInjectAlertDispatch:
    """Tests for the dispatch-based _inject_alert."""

    def test_inject_alert_dispatches_for_critical(self):
        """Verify _inject_alert calls _dispatch_to_agent for critical events."""
        svc = PulseEventService()
        svc._dispatch_to_agent = AsyncMock()

        event = PulseEvent(
            source="mesh_watcher",
            severity=PulseEvent.SEVERITY_CRITICAL,
            title="MCP sidecar DOWN: test-svc",
            detail="test-svc went down",
        )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc._inject_alert(event))

        svc._dispatch_to_agent.assert_called_once_with(event)

    def test_inject_alert_dispatches_for_warning(self):
        """Verify _inject_alert calls _dispatch_to_agent for warning events."""
        svc = PulseEventService()
        svc._dispatch_to_agent = AsyncMock()

        event = PulseEvent(
            source="rabbitmq_dlq",
            severity=PulseEvent.SEVERITY_WARNING,
            title="Dead-lettered message from billing.payments",
            detail="payment timeout",
        )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc._inject_alert(event))

        svc._dispatch_to_agent.assert_called_once_with(event)

    def test_inject_alert_skips_info(self):
        """Verify _inject_alert does NOT dispatch for info events."""
        svc = PulseEventService()
        svc._dispatch_to_agent = AsyncMock()

        event = PulseEvent(
            source="mesh_watcher",
            severity=PulseEvent.SEVERITY_INFO,
            title="MCP sidecar discovered: new-svc",
            detail="new-svc is now online",
        )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(svc._inject_alert(event))

        svc._dispatch_to_agent.assert_not_called()

    def test_dispatch_to_agent_sends_correct_payload(self):
        """Verify _dispatch_to_agent POSTs to /agents/dispatch with correct payload."""
        svc = PulseEventService()
        event = PulseEvent(
            source="mesh_watcher",
            severity=PulseEvent.SEVERITY_CRITICAL,
            title="MCP sidecar DOWN: billing",
            detail="billing changed from healthy to unhealthy",
            metadata={"node": "billing"},
        )

        captured_payload = {}
        captured_url = {}

        async def mock_post(self_client, url, **kwargs):
            captured_url["url"] = url
            captured_payload.update(kwargs.get("json", {}))
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = lambda: {"task_id": "abc123", "conversation_id": "conv-1"}
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(svc._dispatch_to_agent(event))

        assert "/agents/dispatch" in captured_url["url"]
        assert captured_payload["target_agent_id"] == "Support_Agent"
        assert "SYSTEM EVENT" in captured_payload["input"]
        assert "billing" in captured_payload["input"]

    def test_dispatch_to_agent_handles_failure(self):
        """Verify _dispatch_to_agent logs warning on failure without raising."""
        svc = PulseEventService()
        event = PulseEvent(
            source="test",
            severity=PulseEvent.SEVERITY_CRITICAL,
            title="Test",
            detail="test",
        )

        async def mock_post(self_client, url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.text = "Internal Server Error"
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            # Should not raise
            loop = asyncio.get_event_loop()
            loop.run_until_complete(svc._dispatch_to_agent(event))
