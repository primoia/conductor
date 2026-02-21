# src/api/routes/enqueue.py
"""
Agent Enqueue - Async agent task submission via RabbitMQ.

POST /agents/enqueue publishes a lightweight message to the agent task queue
and returns immediately. The consumer builds the prompt and submits to MongoDB.

Agents can call this endpoint to chain work recursively:
    Agent A finishes -> enqueue(Agent B) -> consumer runs B -> B enqueue(Agent C) -> ...

If RabbitMQ is offline, returns HTTP 503 (fallback: use /agents/dispatch).
"""

import asyncio
import logging
import os
import uuid
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Enqueue"])


class EnqueueRequest(BaseModel):
    """Request to enqueue work for an agent."""

    target_agent_id: str = Field(
        ..., description="ID of the agent to enqueue work for (e.g. 'Support_Agent')"
    )
    input: str = Field(
        ..., description="Message/instructions for the target agent"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Existing conversation ID. If omitted, a new one is created.",
    )
    screenplay_id: Optional[str] = Field(
        None,
        description="Existing screenplay ID. If omitted, one is created on consumption.",
    )
    priority: int = Field(
        5,
        ge=0,
        le=9,
        description="Queue priority (0=lowest, 9=highest). Pulse escalations use 8.",
    )
    source: str = Field(
        "dispatch_api",
        description="Origin of the task: dispatch_api | agent_chain | pulse",
    )
    parent_task_id: Optional[str] = Field(
        None,
        description="Parent task ID for chained agent execution.",
    )
    instance_id: Optional[str] = Field(
        None,
        description="Existing agent instance ID from agent_instances collection. "
        "If provided, the task runs under this instance instead of creating a new one.",
    )


class EnqueueResponse(BaseModel):
    task_id: str
    target_agent_id: str
    instance_id: Optional[str] = None
    conversation_id: str
    idempotency_key: str
    chain_depth: int
    max_chain_depth: int
    auto_delegate: bool
    status: str = "queued"


MAX_CHAIN_DEPTH = int(os.getenv("MAX_CHAIN_DEPTH", "10"))


def _get_conversation_settings(conversation_id: str) -> dict:
    """Get per-conversation chain settings (max_chain_depth, auto_delegate).

    Returns dict with 'max_chain_depth' (int) and 'auto_delegate' (bool).
    Falls back to global defaults if conversation not found or fields missing.
    """
    try:
        db = _get_mongo_db()
        if db is None:
            return {"max_chain_depth": MAX_CHAIN_DEPTH, "auto_delegate": True}
        conv = db.conversations.find_one(
            {"conversation_id": conversation_id},
            {"max_chain_depth": 1, "auto_delegate": 1},
        )
        if not conv:
            return {"max_chain_depth": MAX_CHAIN_DEPTH, "auto_delegate": True}
        return {
            "max_chain_depth": conv.get("max_chain_depth") or MAX_CHAIN_DEPTH,
            "auto_delegate": conv.get("auto_delegate", True),
        }
    except Exception as e:
        logger.warning("Conversation settings lookup failed: %s", e)
        return {"max_chain_depth": MAX_CHAIN_DEPTH, "auto_delegate": False}


_mongo_client = None


def _get_mongo_db():
    """Get a shared MongoDB database handle (module-level singleton)."""
    global _mongo_client
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        return None
    if _mongo_client is None:
        from pymongo import MongoClient
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    return _mongo_client.conductor_state


def _get_chain_depth(conversation_id: str) -> int:
    """Count agent-chain tasks since the last human-initiated task.

    Human intervention (source != 'agent_chain') resets the counter.
    Only consecutive agent_chain tasks at the tail count toward depth.
    """
    try:
        db = _get_mongo_db()
        if db is None:
            return 0
        # Walk backwards from newest task; stop at first non-chain task
        cursor = db.tasks.find(
            {"conversation_id": conversation_id},
            {"source": 1},
        ).sort("created_at", -1)
        depth = 0
        for task in cursor:
            if task.get("source") == "agent_chain":
                depth += 1
            else:
                break
        return depth
    except Exception as e:
        logger.warning("Chain depth check failed: %s", e)
        return 0


def _inherit_from_parent(parent_task_id: str) -> dict:
    """Look up parent task and return its conversation_id and screenplay_id.

    This is the deterministic enforcement: when an agent chains work,
    the server forces the child to stay in the same conversation/screenplay.
    """
    try:
        db = _get_mongo_db()
        if db is None:
            return {}
        task = db.tasks.find_one(
            {"_id": ObjectId(parent_task_id)},
            {"conversation_id": 1, "screenplay_id": 1},
        )
        if not task:
            return {}
        return {
            "conversation_id": task.get("conversation_id"),
            "screenplay_id": task.get("screenplay_id"),
        }
    except Exception as e:
        logger.warning("Parent task lookup failed: %s", e)
        return {}


def _get_squad(conversation_id: str) -> list | None:
    """Get the squad from agent_instances for this conversation.

    Returns a list of agent_ids that are instantiated in this conversation,
    or None if no instances exist (no restriction).
    This is dynamic and automatic — the squad is whoever was added to the
    conversation in the frontend (via the Add Agent button or screenplay setup).
    """
    try:
        db = _get_mongo_db()
        if db is None:
            return None
        agent_ids = db.agent_instances.distinct(
            "agent_id", {"conversation_id": conversation_id}
        )
        return agent_ids if agent_ids else None
    except Exception as e:
        logger.warning("Squad lookup failed: %s", e)
        return None


@router.post(
    "/agents/enqueue",
    response_model=EnqueueResponse,
    summary="Enqueue async work for an agent via RabbitMQ",
    operation_id="enqueue_agent",
)
async def enqueue_agent(request: EnqueueRequest):
    """
    Enqueue work for a target agent asynchronously via RabbitMQ.

    The message is published to the agent task queue and the endpoint returns
    immediately with {task_id, status: "queued"}. The consumer will build
    the prompt and submit the task to MongoDB for the watcher to execute.

    Use this instead of /agents/dispatch when you want fire-and-forget
    semantics with retry and DLQ support.

    If RabbitMQ is unavailable, returns HTTP 503 — fall back to /agents/dispatch.
    """
    try:
        # Fail fast: validate agent exists
        from src.container import container

        discovery = container.get_agent_discovery_service()
        agent_def = discovery.get_agent_definition(request.target_agent_id)
        if not agent_def:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{request.target_agent_id}' not found",
            )

        # Chain depth guard: prevent infinite loops
        from src.core.services.agent_task_queue_service import (
            AgentTaskMessage,
            agent_task_queue_service,
        )

        task_id = str(ObjectId())
        idempotency_key = str(uuid.uuid4())

        # Deterministic context inheritance: if parent_task_id is provided,
        # force conversation_id and screenplay_id from the parent task.
        # The agent cannot escape the squad this way.
        # NOTE: All _get_* helpers use sync pymongo. We run them in a thread
        # pool to avoid blocking the async event loop (pymongo heartbeat
        # uses streaming protocol which can block for up to 10s).
        screenplay_id = request.screenplay_id
        if request.parent_task_id:
            parent_ctx = await asyncio.to_thread(_inherit_from_parent, request.parent_task_id)
            if parent_ctx.get("conversation_id"):
                conversation_id = parent_ctx["conversation_id"]
                if request.conversation_id and request.conversation_id != conversation_id:
                    logger.info(
                        "Overriding conversation_id %s -> %s (inherited from parent %s)",
                        request.conversation_id,
                        conversation_id,
                        request.parent_task_id,
                    )
            else:
                conversation_id = request.conversation_id or str(uuid.uuid4())
            if parent_ctx.get("screenplay_id"):
                screenplay_id = parent_ctx["screenplay_id"]
        else:
            conversation_id = request.conversation_id or str(uuid.uuid4())

        # Squad guard: only agents instantiated in this conversation can participate.
        # The squad is built automatically from agent_instances (frontend Add Agent).
        squad = await asyncio.to_thread(_get_squad, conversation_id)
        if squad and request.target_agent_id not in squad:
            logger.warning(
                "Agent %s not in conversation %s squad: %s",
                request.target_agent_id,
                conversation_id,
                squad,
            )
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Agent '{request.target_agent_id}' is not in this conversation's squad. "
                    f"Instantiated agents: {squad}"
                ),
            )

        # Per-conversation settings (max_chain_depth, auto_delegate)
        conv_settings = await asyncio.to_thread(_get_conversation_settings, conversation_id)
        limit = conv_settings["max_chain_depth"]

        # auto_delegate guard: if disabled, only the first enqueue (from
        # the human via frontend) is allowed. Agent-to-agent chaining
        # (source=agent_chain) is blocked — the human must interact.
        if not conv_settings["auto_delegate"] and request.source == "agent_chain":
            logger.info(
                "auto_delegate=false for conversation %s. "
                "Agent chain from %s blocked — human must interact.",
                conversation_id,
                request.target_agent_id,
            )
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Auto-delegation is disabled for conversation {conversation_id}. "
                    f"Enable auto_delegate via PATCH /conversations/{conversation_id}/settings "
                    f"to allow agents to chain autonomously."
                ),
            )

        chain_depth = await asyncio.to_thread(_get_chain_depth, conversation_id)
        if chain_depth >= limit:
            logger.warning(
                "Chain depth limit reached (%d/%d) for conversation %s. "
                "Agent %s blocked.",
                chain_depth,
                limit,
                conversation_id,
                request.target_agent_id,
            )
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Chain depth limit reached ({chain_depth}/{limit}). "
                    f"Too many chained tasks in conversation {conversation_id}. "
                    f"Adjust via PATCH /conversations/{conversation_id}/settings."
                ),
            )

        msg = AgentTaskMessage(
            task_id=task_id,
            agent_id=request.target_agent_id,
            instance_id=request.instance_id,
            conversation_id=conversation_id,
            screenplay_id=screenplay_id,
            input=request.input,
            priority=request.priority,
            source=request.source,
            parent_task_id=request.parent_task_id,
            idempotency_key=idempotency_key,
        )

        # Publish to RabbitMQ
        published = await agent_task_queue_service.publish(msg)
        if not published:
            raise HTTPException(
                status_code=503,
                detail=(
                    "RabbitMQ is unavailable. "
                    "Use /agents/dispatch for synchronous execution."
                ),
            )

        logger.info(
            "Enqueued task %s for agent %s (key=%s, priority=%d)",
            task_id,
            request.target_agent_id,
            idempotency_key,
            request.priority,
        )

        return EnqueueResponse(
            task_id=task_id,
            target_agent_id=request.target_agent_id,
            instance_id=request.instance_id,
            conversation_id=conversation_id,
            idempotency_key=idempotency_key,
            chain_depth=chain_depth + 1,
            max_chain_depth=limit,
            auto_delegate=conv_settings["auto_delegate"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Enqueue failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
