# tests/api/test_mcp_mesh.py
"""
Tests for SAGA-016 Phase 1: MCP Mesh Service and API routes.
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from src.core.services.mcp_mesh_service import MCPMeshService, MCPNode


class TestMCPNode:
    """Tests for the MCPNode data class."""

    def test_node_creation(self):
        node = MCPNode(
            name="test-sidecar",
            url="http://localhost:13001/sse",
            port=13001,
            status="healthy",
            tools_count=5,
        )
        assert node.name == "test-sidecar"
        assert node.status == "healthy"
        assert node.tools_count == 5
        assert node.port == 13001

    def test_node_to_dict(self):
        node = MCPNode(
            name="test-sidecar",
            url="http://localhost:13001/sse",
            host_url="http://host:13001/sse",
            port=13001,
            status="healthy",
            tools_count=5,
            last_seen="2026-01-01T00:00:00+00:00",
            response_time_ms=42.5,
            category="verticals",
        )
        d = node.to_dict()
        assert d["name"] == "test-sidecar"
        assert d["host_url"] == "http://host:13001/sse"
        assert d["response_time_ms"] == 42.5
        assert d["category"] == "verticals"
        assert d["error"] is None

    def test_node_defaults(self):
        node = MCPNode(name="x", url="http://x")
        assert node.status == "unknown"
        assert node.tools_count == 0
        assert node.last_seen is None
        assert node.error is None


class TestMCPMeshService:
    """Tests for the MCPMeshService core logic."""

    def test_get_mesh_empty(self):
        svc = MCPMeshService()
        mesh = svc.get_mesh()
        assert mesh["summary"]["total"] == 0
        assert mesh["summary"]["healthy"] == 0
        assert mesh["nodes"] == []

    def test_get_mesh_with_nodes(self):
        svc = MCPMeshService()
        svc._nodes["a"] = MCPNode(name="a", url="http://a", status="healthy", tools_count=3)
        svc._nodes["b"] = MCPNode(name="b", url="http://b", status="unhealthy", tools_count=0)
        svc._nodes["c"] = MCPNode(name="c", url="http://c", status="unknown")

        mesh = svc.get_mesh()
        assert mesh["summary"]["total"] == 3
        assert mesh["summary"]["healthy"] == 1
        assert mesh["summary"]["unhealthy"] == 1
        assert mesh["summary"]["unknown"] == 1
        assert len(mesh["nodes"]) == 3
        # Nodes should be sorted by name
        assert mesh["nodes"][0]["name"] == "a"

    def test_get_mesh_context_for_prompt_empty(self):
        svc = MCPMeshService()
        ctx = svc.get_mesh_context_for_prompt()
        assert "<mcp_mesh_topology>" in ctx
        assert "<total_nodes>0</total_nodes>" in ctx
        assert "</mcp_mesh_topology>" in ctx

    def test_get_mesh_context_for_prompt_with_nodes(self):
        svc = MCPMeshService()
        svc._nodes["svc-a"] = MCPNode(
            name="svc-a", url="http://a", port=13001,
            status="healthy", tools_count=5, response_time_ms=12.3,
        )
        svc._nodes["svc-b"] = MCPNode(
            name="svc-b", url="http://b", port=13002,
            status="unhealthy", tools_count=2,
        )
        ctx = svc.get_mesh_context_for_prompt()
        assert "[+] svc-a:13001 tools=5 (12ms)" in ctx
        assert "[-] svc-b:13002 tools=2" in ctx
        assert "<healthy>1</healthy>" in ctx

    def test_extract_port(self):
        assert MCPMeshService._extract_port("http://localhost:13001/sse") == 13001
        assert MCPMeshService._extract_port("http://host:9000/health") == 9000
        assert MCPMeshService._extract_port("http://host/path") is None

    @patch("src.core.services.mcp_mesh_service.MCPMeshService._load_registry")
    def test_sweep_once_updates_nodes(self, mock_registry):
        """Test that a sweep updates the node cache."""
        mock_registry.return_value = [
            {"name": "test-svc", "url": "http://localhost:13001/sse", "tools_count": 3},
        ]
        svc = MCPMeshService()

        # Mock the ping to set the node directly
        async def mock_ping(entry):
            svc._nodes[entry["name"]] = MCPNode(
                name=entry["name"],
                url=entry["url"],
                status="healthy",
                tools_count=3,
                last_seen=datetime.now(timezone.utc).isoformat(),
                response_time_ms=10.0,
            )

        with patch.object(svc, "_ping_sidecar", side_effect=mock_ping):
            asyncio.get_event_loop().run_until_complete(svc._sweep_once())

        assert "test-svc" in svc._nodes
        assert svc._nodes["test-svc"].status == "healthy"
        assert svc._last_sweep is not None


class TestMeshAPIRoute:
    """Tests for the /system/mcp/mesh endpoint."""

    def test_mesh_endpoint_returns_data(self):
        from fastapi.testclient import TestClient
        from src.api.routes.mcp_mesh import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        # Inject a test node into the singleton
        from src.core.services.mcp_mesh_service import mesh_service
        mesh_service._nodes["test"] = MCPNode(
            name="test", url="http://test:13001", port=13001,
            status="healthy", tools_count=7,
        )

        client = TestClient(app)
        resp = client.get("/system/mcp/mesh")

        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total"] >= 1
        assert any(n["name"] == "test" for n in data["nodes"])

        # Cleanup
        mesh_service._nodes.clear()

    def test_mesh_context_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.routes.mcp_mesh import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        from src.core.services.mcp_mesh_service import mesh_service
        mesh_service._nodes["ctx-test"] = MCPNode(
            name="ctx-test", url="http://test:13002", port=13002,
            status="healthy", tools_count=3,
        )

        client = TestClient(app)
        resp = client.get("/system/mcp/mesh/context")

        assert resp.status_code == 200
        data = resp.json()
        assert "mcp_mesh_topology" in data["context"]
        assert data["node_count"] >= 1

        # Cleanup
        mesh_service._nodes.clear()
