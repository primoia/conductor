# src/api/routes/mcp_mesh.py
"""
MCP Mesh API Routes (SAGA-016 Phase 1)

Exposes the live MCP mesh topology via REST API.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.services.mcp_mesh_service import mesh_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system/mcp", tags=["MCP Mesh"])


class MCPNodeResponse(BaseModel):
    """Single node in the mesh."""
    name: str
    url: str
    host_url: Optional[str] = None
    port: Optional[int] = None
    status: str
    tools_count: int = 0
    last_seen: Optional[str] = None
    response_time_ms: Optional[float] = None
    category: Optional[str] = None
    error: Optional[str] = None


class MeshSummary(BaseModel):
    """Aggregate counts."""
    total: int = 0
    healthy: int = 0
    unhealthy: int = 0
    unknown: int = 0


class MeshResponse(BaseModel):
    """Full mesh topology response."""
    timestamp: str
    last_sweep: Optional[str] = None
    summary: MeshSummary
    nodes: List[MCPNodeResponse]


class MeshContextResponse(BaseModel):
    """Prompt-ready mesh context."""
    context: str = Field(description="XML-formatted mesh topology for agent prompts")
    node_count: int


@router.get("/mesh", response_model=MeshResponse, summary="Get live MCP mesh topology")
def get_mesh():
    """
    Returns the live mesh topology of all MCP sidecars.

    The mesh is updated every 30 seconds by a background sweep that pings
    each registered sidecar's /health endpoint. This provides real-time
    visibility into which services are available and their response times.
    """
    data = mesh_service.get_mesh()
    return MeshResponse(
        timestamp=data["timestamp"],
        last_sweep=data["last_sweep"],
        summary=MeshSummary(**data["summary"]),
        nodes=[MCPNodeResponse(**n) for n in data["nodes"]],
    )


@router.get("/mesh/context", response_model=MeshContextResponse, summary="Get mesh context for agent prompts")
def get_mesh_context():
    """
    Returns the mesh topology formatted as XML for injection into
    Council agent system prompts. This gives agents real-time awareness
    of what MCP services are available.
    """
    context = mesh_service.get_mesh_context_for_prompt()
    mesh = mesh_service.get_mesh()
    return MeshContextResponse(
        context=context,
        node_count=mesh["summary"]["total"],
    )
