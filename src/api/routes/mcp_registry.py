# src/api/routes/mcp_registry.py
"""
MCP Registry API Routes for Conductor API.

Provides CRUD operations for managing MCP servers in the mcp_registry collection.
These endpoints are discovered by the MCP sidecar and exposed as tools.

Operations:
- List all MCPs
- Get MCP details
- Register/Create MCP
- Update MCP
- Delete MCP
- Check health
- Get statistics
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp-registry", tags=["MCP Registry"])


# ============================================================================
# Enums and Models
# ============================================================================

class MCPType(str, Enum):
    """Type of MCP server."""
    INTERNAL = "internal"
    EXTERNAL = "external"


class MCPStatus(str, Enum):
    """Health status of an MCP server."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STOPPED = "stopped"
    STARTING = "starting"


class MCPMetadata(BaseModel):
    """Optional metadata for an MCP entry."""
    category: Optional[str] = Field(None, description="Category for grouping (e.g., verticals, tools)")
    description: Optional[str] = Field(None, description="Human-readable description")
    version: Optional[str] = Field(None, description="Version of the MCP/service")
    tags: List[str] = Field(default_factory=list, description="Tags for filtering")


class MCPCreateRequest(BaseModel):
    """Request model for creating/registering an MCP server."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique identifier for this MCP")
    url: str = Field(..., description="SSE endpoint URL (e.g., http://mcp-sidecar:9000/sse)")
    type: MCPType = Field(MCPType.EXTERNAL, description="Type: internal or external")
    host_url: Optional[str] = Field(None, description="URL accessible from host machine")
    backend_url: Optional[str] = Field(None, description="URL of the backend API this MCP proxies")
    auth: Optional[str] = Field(None, description="Auth token (base64) to append to URL")
    docker_compose_path: Optional[str] = Field(None, description="Path to docker-compose for on-demand startup")
    auto_shutdown_minutes: int = Field(30, description="Minutes of inactivity before auto-shutdown")
    metadata: Optional[MCPMetadata] = Field(None, description="Optional metadata")


class MCPUpdateRequest(BaseModel):
    """Request model for updating an MCP server."""
    url: Optional[str] = Field(None, description="SSE endpoint URL")
    host_url: Optional[str] = Field(None, description="URL accessible from host machine")
    backend_url: Optional[str] = Field(None, description="Backend API URL")
    auth: Optional[str] = Field(None, description="Auth token")
    status: Optional[MCPStatus] = Field(None, description="Status")
    docker_compose_path: Optional[str] = Field(None, description="Docker compose path")
    auto_shutdown_minutes: Optional[int] = Field(None, description="Auto shutdown minutes")
    metadata: Optional[MCPMetadata] = Field(None, description="Metadata")


class MCPEntry(BaseModel):
    """Full MCP registry entry."""
    name: str
    type: MCPType
    url: str
    host_url: Optional[str] = None
    backend_url: Optional[str] = None
    auth: Optional[str] = None
    status: MCPStatus = MCPStatus.UNKNOWN
    tools_count: int = 0
    last_heartbeat: Optional[str] = None
    registered_at: Optional[str] = None
    docker_compose_path: Optional[str] = None
    auto_shutdown_minutes: int = 30
    last_used: Optional[str] = None
    metadata: Optional[MCPMetadata] = None


class MCPListResponse(BaseModel):
    """Response model for listing MCPs."""
    items: List[MCPEntry]
    total: int
    internal_count: int
    external_count: int
    healthy_count: int


class MCPStatsResponse(BaseModel):
    """Response model for registry statistics."""
    total: int
    internal: int
    external: int
    healthy: int
    unhealthy: int
    unknown: int
    stopped: int


# ============================================================================
# MongoDB Connection Helper
# ============================================================================

def _get_mcp_collection():
    """Get the mcp_registry collection from MongoDB."""
    from pymongo import MongoClient

    mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:conductor123@primoia-shared-mongo:27017')
    db_name = os.getenv('MONGO_DATABASE', 'conductor_state')

    client = MongoClient(mongo_uri)
    db = client[db_name]
    return db['mcp_registry']


def _doc_to_entry(doc: dict) -> MCPEntry:
    """Convert MongoDB document to MCPEntry."""
    return MCPEntry(
        name=doc.get("name", ""),
        type=MCPType(doc.get("type", "external")),
        url=doc.get("url", ""),
        host_url=doc.get("host_url"),
        backend_url=doc.get("backend_url"),
        auth=doc.get("auth"),
        status=MCPStatus(doc.get("status", "unknown")),
        tools_count=doc.get("tools_count", 0),
        last_heartbeat=doc.get("last_heartbeat").isoformat() if doc.get("last_heartbeat") else None,
        registered_at=doc.get("registered_at").isoformat() if doc.get("registered_at") else None,
        docker_compose_path=doc.get("docker_compose_path"),
        auto_shutdown_minutes=doc.get("auto_shutdown_minutes", 30),
        last_used=doc.get("last_used").isoformat() if doc.get("last_used") else None,
        metadata=MCPMetadata(**doc.get("metadata", {})) if doc.get("metadata") else None
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.get("/", response_model=MCPListResponse, summary="List all MCP servers")
def list_mcps(
    type: Optional[MCPType] = Query(None, description="Filter by type (internal/external)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[MCPStatus] = Query(None, description="Filter by status"),
    healthy_only: bool = Query(False, description="Only return healthy MCPs")
):
    """
    List all registered MCP servers with optional filters.

    Returns both internal MCPs (gateway-hosted) and external MCPs (sidecars).
    """
    try:
        collection = _get_mcp_collection()

        query = {}
        if type:
            query["type"] = type.value
        if category:
            query["metadata.category"] = category
        if status:
            query["status"] = status.value
        elif healthy_only:
            query["status"] = MCPStatus.HEALTHY.value

        docs = list(collection.find(query).sort("name", 1))

        items = [_doc_to_entry(doc) for doc in docs]

        # Calculate counts
        internal_count = sum(1 for item in items if item.type == MCPType.INTERNAL)
        external_count = sum(1 for item in items if item.type == MCPType.EXTERNAL)
        healthy_count = sum(1 for item in items if item.status == MCPStatus.HEALTHY)

        return MCPListResponse(
            items=items,
            total=len(items),
            internal_count=internal_count,
            external_count=external_count,
            healthy_count=healthy_count
        )

    except Exception as e:
        logger.error(f"Error listing MCPs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list MCPs: {str(e)}")


@router.get("/stats", response_model=MCPStatsResponse, summary="Get registry statistics")
def get_stats():
    """Get statistics about the MCP registry."""
    try:
        collection = _get_mcp_collection()

        pipeline = [
            {
                "$group": {
                    "_id": {"type": "$type", "status": "$status"},
                    "count": {"$sum": 1}
                }
            }
        ]

        results = list(collection.aggregate(pipeline))

        stats = {
            "total": 0,
            "internal": 0,
            "external": 0,
            "healthy": 0,
            "unhealthy": 0,
            "unknown": 0,
            "stopped": 0
        }

        for r in results:
            count = r["count"]
            stats["total"] += count

            if r["_id"]["type"] == MCPType.INTERNAL.value:
                stats["internal"] += count
            else:
                stats["external"] += count

            status = r["_id"].get("status", "unknown")
            if status in stats:
                stats[status] += count

        return MCPStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/categories", summary="List all MCP categories")
def list_categories():
    """List all unique categories in the registry."""
    try:
        collection = _get_mcp_collection()

        categories = collection.distinct("metadata.category")
        # Filter out None/empty
        categories = [c for c in categories if c]

        return {
            "categories": sorted(categories),
            "total": len(categories)
        }

    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@router.post("/resolve", summary="Resolve MCP names to URLs")
def resolve_mcps(names: List[str]):
    """
    Resolve a list of MCP names to their SSE endpoint URLs.

    Args:
        names: List of MCP names to resolve

    Returns:
        Dict with resolved URLs and list of not found names
    """
    try:
        collection = _get_mcp_collection()

        resolved = {}
        not_found = []

        for name in names:
            doc = collection.find_one({"name": name})
            if doc and doc.get("status") != MCPStatus.UNHEALTHY.value:
                # Prefer host_url for external access
                url = doc.get("host_url") or doc["url"]
                auth = doc.get("auth")

                if auth:
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}auth={auth}"

                resolved[name] = url
            else:
                not_found.append(name)

        return {
            "resolved": resolved,
            "not_found": not_found
        }

    except Exception as e:
        logger.error(f"Error resolving MCPs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to resolve MCPs: {str(e)}")


@router.post("/cleanup", summary="Cleanup stale MCP entries")
def cleanup_stale(
    max_age_hours: int = Query(24, description="Max hours since last heartbeat")
):
    """
    Remove external MCP entries that haven't sent heartbeat in a long time.

    Internal MCPs are never removed.
    """
    try:
        collection = _get_mcp_collection()

        from datetime import timedelta
        threshold = datetime.utcnow() - timedelta(hours=max_age_hours)

        result = collection.delete_many({
            "type": MCPType.EXTERNAL.value,
            "last_heartbeat": {"$lt": threshold}
        })

        removed = result.deleted_count

        if removed > 0:
            logger.info(f"✅ Cleaned up {removed} stale MCP entries")

        return {"removed": removed}

    except Exception as e:
        logger.error(f"Error cleaning up MCPs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cleanup MCPs: {str(e)}")


# ============================================================================
# Endpoints with Path Parameters (must come after fixed routes)
# ============================================================================

@router.get("/{name}", response_model=MCPEntry, summary="Get MCP details")
def get_mcp(name: str = Path(..., description="MCP name")):
    """Get details of a specific MCP server by name."""
    try:
        collection = _get_mcp_collection()

        doc = collection.find_one({"name": name})
        if not doc:
            raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")

        return _doc_to_entry(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MCP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get MCP: {str(e)}")


@router.post("/", response_model=MCPEntry, status_code=201, summary="Create/Register MCP server")
def create_mcp(request: MCPCreateRequest):
    """
    Create or register a new MCP server.

    If an MCP with the same name already exists, it will be updated (upsert).
    Internal MCPs (hosted in gateway) cannot be overwritten by external ones.
    """
    try:
        collection = _get_mcp_collection()

        # Check if internal MCP exists with same name
        existing = collection.find_one({"name": request.name})
        if existing and existing.get("type") == MCPType.INTERNAL.value and request.type == MCPType.EXTERNAL:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot register '{request.name}': name reserved for internal MCP"
            )

        now = datetime.utcnow()

        entry = {
            "name": request.name,
            "type": request.type.value,
            "url": request.url,
            "host_url": request.host_url,
            "backend_url": request.backend_url,
            "auth": request.auth,
            "status": MCPStatus.HEALTHY.value if request.type == MCPType.EXTERNAL else MCPStatus.UNKNOWN.value,
            "tools_count": 0,
            "last_heartbeat": now if request.type == MCPType.EXTERNAL else None,
            "registered_at": now,
            "docker_compose_path": request.docker_compose_path,
            "auto_shutdown_minutes": request.auto_shutdown_minutes,
            "metadata": request.metadata.model_dump() if request.metadata else {}
        }

        # Upsert - update if exists, insert if not
        collection.update_one(
            {"name": request.name},
            {"$set": entry},
            upsert=True
        )

        logger.info(f"✅ MCP registered/updated: {request.name} at {request.url}")

        # Fetch and return the created/updated entry
        doc = collection.find_one({"name": request.name})
        return _doc_to_entry(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating MCP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create MCP: {str(e)}")


@router.put("/{name}", response_model=MCPEntry, summary="Update MCP server")
def update_mcp(
    name: str = Path(..., description="MCP name"),
    request: MCPUpdateRequest = ...
):
    """
    Update an existing MCP server.

    Only the fields provided in the request will be updated.
    """
    try:
        collection = _get_mcp_collection()

        existing = collection.find_one({"name": name})
        if not existing:
            raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")

        # Build update dict with only provided fields
        update_data = {}

        if request.url is not None:
            update_data["url"] = request.url
        if request.host_url is not None:
            update_data["host_url"] = request.host_url
        if request.backend_url is not None:
            update_data["backend_url"] = request.backend_url
        if request.auth is not None:
            update_data["auth"] = request.auth
        if request.status is not None:
            update_data["status"] = request.status.value
        if request.docker_compose_path is not None:
            update_data["docker_compose_path"] = request.docker_compose_path
        if request.auto_shutdown_minutes is not None:
            update_data["auto_shutdown_minutes"] = request.auto_shutdown_minutes
        if request.metadata is not None:
            update_data["metadata"] = request.metadata.model_dump()

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        collection.update_one(
            {"name": name},
            {"$set": update_data}
        )

        logger.info(f"✅ MCP updated: {name} - fields: {list(update_data.keys())}")

        # Fetch and return updated entry
        doc = collection.find_one({"name": name})
        return _doc_to_entry(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating MCP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update MCP: {str(e)}")


@router.delete("/{name}", status_code=204, summary="Delete MCP server")
def delete_mcp(name: str = Path(..., description="MCP name")):
    """
    Delete an MCP server from the registry.

    Internal MCPs cannot be deleted.
    """
    try:
        collection = _get_mcp_collection()

        existing = collection.find_one({"name": name})
        if not existing:
            raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")

        if existing.get("type") == MCPType.INTERNAL.value:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete '{name}': internal MCPs cannot be removed"
            )

        result = collection.delete_one({"name": name})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")

        logger.info(f"✅ MCP deleted: {name}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MCP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete MCP: {str(e)}")


# ============================================================================
# Health and Heartbeat Endpoints
# ============================================================================

@router.post("/{name}/heartbeat", status_code=204, summary="Send heartbeat for MCP")
def heartbeat(
    name: str = Path(..., description="MCP name"),
    tools_count: Optional[int] = Query(None, description="Number of tools exposed")
):
    """
    Update heartbeat timestamp for an MCP server.

    Sidecars should call this periodically to indicate they're alive.
    """
    try:
        collection = _get_mcp_collection()

        update = {
            "last_heartbeat": datetime.utcnow(),
            "status": MCPStatus.HEALTHY.value
        }
        if tools_count is not None:
            update["tools_count"] = tools_count

        result = collection.update_one(
            {"name": name},
            {"$set": update}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating heartbeat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update heartbeat: {str(e)}")


@router.get("/{name}/health", summary="Check MCP health")
def check_health(name: str = Path(..., description="MCP name")):
    """
    Check the health status of an MCP server.

    Returns current status based on last heartbeat.
    """
    try:
        collection = _get_mcp_collection()

        doc = collection.find_one({"name": name})
        if not doc:
            raise HTTPException(status_code=404, detail=f"MCP '{name}' not found")

        # Check if heartbeat is stale (> 90 seconds)
        last_heartbeat = doc.get("last_heartbeat")
        is_stale = False
        seconds_since_heartbeat = None

        if last_heartbeat:
            delta = datetime.utcnow() - last_heartbeat
            seconds_since_heartbeat = int(delta.total_seconds())
            is_stale = seconds_since_heartbeat > 90

            # Update status if stale
            if is_stale and doc.get("status") == MCPStatus.HEALTHY.value:
                collection.update_one(
                    {"name": name},
                    {"$set": {"status": MCPStatus.UNHEALTHY.value}}
                )

        return {
            "name": name,
            "status": MCPStatus.UNHEALTHY.value if is_stale else doc.get("status", "unknown"),
            "tools_count": doc.get("tools_count", 0),
            "last_heartbeat": last_heartbeat.isoformat() if last_heartbeat else None,
            "seconds_since_heartbeat": seconds_since_heartbeat,
            "is_stale": is_stale
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check health: {str(e)}")
