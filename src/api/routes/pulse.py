# src/api/routes/pulse.py
"""
Pulse API Routes (SAGA-016 Phase 2)

Exposes proactive event triggers - the system events detected by
the DLQ listener and mesh health watcher.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.services.pulse_event_service import pulse_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system/pulse", tags=["Pulse Events"])

# Module-level MongoDB client (connection pool, lazy init)
_mongo_client = None


def _get_screenplay_collection():
    """Get MongoDB screenplay_logs collection using a shared client."""
    global _mongo_client
    if _mongo_client is None:
        from pymongo import MongoClient
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    db_name = os.getenv("MONGO_DATABASE", "conductor_state")
    return _mongo_client[db_name]["screenplay_logs"]


class PulseEventResponse(BaseModel):
    """A single pulse event."""
    source: str
    severity: str
    title: str
    detail: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class PulseStatusResponse(BaseModel):
    """Pulse service status."""
    running: bool
    rabbitmq_available: bool
    event_count: int
    recent_events: List[PulseEventResponse]


class ScreenplayLogRequest(BaseModel):
    """Request to write to the Living Screenplay log."""
    agent_id: str = Field(..., description="ID of the agent writing the log")
    entry: str = Field(..., min_length=1, description="Log entry content")
    severity: str = Field("info", description="Severity: info, warning, critical")
    category: str = Field("observation", description="Category: observation, finding, recommendation, escalation")


class ScreenplayLogResponse(BaseModel):
    """Response from screenplay log write."""
    status: str
    log_id: str
    timestamp: str


@router.get("/status", response_model=PulseStatusResponse, summary="Get Pulse service status")
def get_pulse_status():
    """
    Returns the current status of the Pulse event detection service,
    including whether RabbitMQ DLQ is connected and recent events.
    """
    events = pulse_service.get_events(limit=10)
    return PulseStatusResponse(
        running=pulse_service._running,
        rabbitmq_available=pulse_service._rabbitmq_available,
        event_count=len(pulse_service._event_log),
        recent_events=[PulseEventResponse(**e) for e in events],
    )


@router.get("/events", summary="List pulse events")
def list_events(
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """
    List recent system events detected by the Pulse service.
    Events are returned most-recent-first.
    """
    events = pulse_service.get_events(limit=limit)

    if severity:
        events = [e for e in events if e.get("severity") == severity]
    if source:
        events = [e for e in events if e.get("source") == source]

    return {
        "total": len(events),
        "events": events,
    }


@router.post("/screenplay-log", response_model=ScreenplayLogResponse, summary="Write screenplay log entry")
def write_screenplay_log(request: ScreenplayLogRequest):
    """
    MCP tool endpoint: write_screenplay_log

    Allows Support Councilor (or any agent) to log findings to the
    Living Screenplay. Entries are persisted to MongoDB for audit trail.
    """
    try:
        collection = _get_screenplay_collection()

        now = datetime.now(timezone.utc)
        log_id = f"slog_{int(now.timestamp() * 1000)}"

        doc = {
            "log_id": log_id,
            "agent_id": request.agent_id,
            "entry": request.entry,
            "severity": request.severity,
            "category": request.category,
            "timestamp": now,
            "created_at": now,
        }

        collection.insert_one(doc)

        logger.info(
            "Screenplay log written by %s: [%s] %s",
            request.agent_id, request.severity, request.entry[:100],
        )

        return ScreenplayLogResponse(
            status="written",
            log_id=log_id,
            timestamp=now.isoformat(),
        )

    except Exception as e:
        logger.error("Failed to write screenplay log: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to write log: {str(e)}")


@router.get("/screenplay-log", summary="Read screenplay logs")
def read_screenplay_logs(
    limit: int = Query(50, ge=1, le=500, description="Max logs to return"),
    agent_id: Optional[str] = Query(None, description="Filter by agent"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """Read screenplay log entries, most recent first."""
    try:
        collection = _get_screenplay_collection()

        query: Dict[str, Any] = {}
        if agent_id:
            query["agent_id"] = agent_id
        if severity:
            query["severity"] = severity
        if category:
            query["category"] = category

        docs = list(
            collection.find(query, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )

        # Convert datetime fields to ISO strings
        for doc in docs:
            for key in ("timestamp", "created_at"):
                if key in doc and hasattr(doc[key], "isoformat"):
                    doc[key] = doc[key].isoformat()

        return {"total": len(docs), "logs": docs}

    except Exception as e:
        logger.error("Failed to read screenplay logs: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")
