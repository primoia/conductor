# src/core/services/mcp_mesh_service.py
"""
MCP Mesh Service - Dynamic MCP Discovery Node (SAGA-016 Phase 1)

Background service that maintains a live view of all MCP sidecars
in the Primoia ecosystem. Pings /health on all registered 13xxx
MCP sidecars every 30 seconds and caches results in memory.

Used by:
- GET /api/system/mcp/mesh endpoint
- Council agent prompt injection (live mesh context)
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import httpx

logger = logging.getLogger(__name__)


class MCPNode:
    """Represents a single MCP sidecar in the mesh."""

    __slots__ = (
        "name", "url", "host_url", "port", "status", "tools_count",
        "last_seen", "response_time_ms", "category", "error",
    )

    def __init__(
        self,
        name: str,
        url: str,
        host_url: Optional[str] = None,
        port: Optional[int] = None,
        status: str = "unknown",
        tools_count: int = 0,
        last_seen: Optional[str] = None,
        response_time_ms: Optional[float] = None,
        category: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.name = name
        self.url = url
        self.host_url = host_url
        self.port = port
        self.status = status
        self.tools_count = tools_count
        self.last_seen = last_seen
        self.response_time_ms = response_time_ms
        self.category = category
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "host_url": self.host_url,
            "port": self.port,
            "status": self.status,
            "tools_count": self.tools_count,
            "last_seen": self.last_seen,
            "response_time_ms": self.response_time_ms,
            "category": self.category,
            "error": self.error,
        }


class MCPMeshService:
    """
    Maintains an in-memory mesh topology of all MCP sidecars.

    Runs a background loop that pings each registered sidecar's /health
    endpoint every ``ping_interval`` seconds.
    """

    PING_INTERVAL_SECONDS = 30
    PING_TIMEOUT_SECONDS = 5

    def __init__(self):
        self._nodes: Dict[str, MCPNode] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_sweep: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_mesh(self) -> Dict[str, Any]:
        """Return the current mesh topology snapshot."""
        nodes = list(self._nodes.values())
        healthy = [n for n in nodes if n.status == "healthy"]
        unhealthy = [n for n in nodes if n.status == "unhealthy"]
        unknown = [n for n in nodes if n.status == "unknown"]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "last_sweep": self._last_sweep,
            "summary": {
                "total": len(nodes),
                "healthy": len(healthy),
                "unhealthy": len(unhealthy),
                "unknown": len(unknown),
            },
            "nodes": [n.to_dict() for n in sorted(nodes, key=lambda x: x.name)],
        }

    def get_mesh_context_for_prompt(self) -> str:
        """
        Return a compact text block suitable for injection into an agent
        system prompt.  Gives Council agents awareness of the live mesh.
        """
        mesh = self.get_mesh()
        summary = mesh["summary"]

        lines = [
            "<mcp_mesh_topology>",
            f"  <sweep_time>{mesh['last_sweep'] or 'never'}</sweep_time>",
            f"  <total_nodes>{summary['total']}</total_nodes>",
            f"  <healthy>{summary['healthy']}</healthy>",
            f"  <unhealthy>{summary['unhealthy']}</unhealthy>",
            "  <services>",
        ]

        for node in mesh["nodes"]:
            status_icon = "+" if node["status"] == "healthy" else "-"
            rt = f" ({node['response_time_ms']:.0f}ms)" if node["response_time_ms"] else ""
            tools = f" tools={node['tools_count']}" if node["tools_count"] else ""
            lines.append(
                f"    [{status_icon}] {node['name']}:{node['port'] or '?'}{tools}{rt}"
            )

        lines.append("  </services>")
        lines.append("</mcp_mesh_topology>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Background sweep
    # ------------------------------------------------------------------

    async def start(self):
        """Start the background sweep loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._sweep_loop())
        logger.info("MCP Mesh Service started (interval=%ds)", self.PING_INTERVAL_SECONDS)

    async def stop(self):
        """Stop the background sweep loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MCP Mesh Service stopped")

    async def _sweep_loop(self):
        """Periodically sweep all registered sidecars."""
        # Initial sweep immediately
        await self._sweep_once()

        while self._running:
            try:
                await asyncio.sleep(self.PING_INTERVAL_SECONDS)
                if self._running:
                    await self._sweep_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Mesh sweep error: %s", e, exc_info=True)
                await asyncio.sleep(5)

    async def _sweep_once(self):
        """Run one full sweep: load registry, ping all sidecars."""
        try:
            registry_entries = self._load_registry()
        except Exception as e:
            logger.error("Failed to load MCP registry: %s", e)
            return

        tasks = []
        for entry in registry_entries:
            tasks.append(self._ping_sidecar(entry))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._last_sweep = datetime.now(timezone.utc).isoformat()
        healthy = sum(1 for n in self._nodes.values() if n.status == "healthy")
        logger.info(
            "Mesh sweep complete: %d nodes (%d healthy)",
            len(self._nodes), healthy,
        )

    def _load_registry(self) -> List[Dict[str, Any]]:
        """Load MCP entries from MongoDB registry (synchronous)."""
        import os
        from pymongo import MongoClient

        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DATABASE", "conductor_state")

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]
        collection = db["mcp_registry"]

        docs = list(collection.find({}))
        client.close()
        return docs

    async def _ping_sidecar(self, entry: Dict[str, Any]):
        """Ping a single sidecar's /health endpoint."""
        name = entry.get("name", "unknown")
        # Prefer host_url for accessibility, fall back to internal url
        url = entry.get("host_url") or entry.get("url", "")

        # Derive the health URL from the sidecar base URL
        # Sidecars expose /health on the same base
        if "/sse" in url:
            health_url = url.rsplit("/sse", 1)[0] + "/health"
        elif url.rstrip("/").endswith(("/tools", "/docs")):
            health_url = url.rsplit("/", 1)[0] + "/health"
        else:
            health_url = url.rstrip("/") + "/health"

        # Extract port from URL
        port = self._extract_port(url)

        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=self.PING_TIMEOUT_SECONDS) as client:
                resp = await client.get(health_url)
            elapsed_ms = (time.monotonic() - start) * 1000

            if resp.status_code == 200:
                body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                tools_count = body.get("tools_count", entry.get("tools_count", 0))
                self._nodes[name] = MCPNode(
                    name=name,
                    url=entry.get("url", ""),
                    host_url=entry.get("host_url"),
                    port=port,
                    status="healthy",
                    tools_count=tools_count,
                    last_seen=datetime.now(timezone.utc).isoformat(),
                    response_time_ms=round(elapsed_ms, 1),
                    category=entry.get("metadata", {}).get("category") if entry.get("metadata") else None,
                )
            else:
                self._nodes[name] = MCPNode(
                    name=name,
                    url=entry.get("url", ""),
                    host_url=entry.get("host_url"),
                    port=port,
                    status="unhealthy",
                    tools_count=entry.get("tools_count", 0),
                    last_seen=self._nodes.get(name, MCPNode(name, "")).last_seen,
                    category=entry.get("metadata", {}).get("category") if entry.get("metadata") else None,
                    error=f"HTTP {resp.status_code}",
                )
        except Exception as e:
            self._nodes[name] = MCPNode(
                name=name,
                url=entry.get("url", ""),
                host_url=entry.get("host_url"),
                port=port,
                status="unhealthy",
                tools_count=entry.get("tools_count", 0),
                last_seen=self._nodes.get(name, MCPNode(name, "")).last_seen,
                category=entry.get("metadata", {}).get("category") if entry.get("metadata") else None,
                error=str(e)[:200],
            )

    @staticmethod
    def _extract_port(url: str) -> Optional[int]:
        """Extract port number from a URL string."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.port
        except Exception:
            return None


# Singleton instance
mesh_service = MCPMeshService()
