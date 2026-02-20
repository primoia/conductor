# src/api/routes/dispatch.py
"""
Agent Dispatch - Allows agents (or Pulse) to pass work to other agents
while sharing conversation context.

Exposed via OpenAPI → MCP sidecar as `dispatch_agent` tool.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dispatch"])


class DispatchRequest(BaseModel):
    """Request to dispatch work to another agent."""
    target_agent_id: str = Field(
        ..., description="ID of the agent to dispatch work to (e.g. 'DevOps_Agent')"
    )
    input: str = Field(
        ..., description="Message/instructions for the target agent"
    )
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID to share context. If omitted, a new one is created."
    )
    screenplay_id: Optional[str] = Field(
        None, description="Existing screenplay ID for project context. If omitted, a Pulse screenplay is created."
    )


class DispatchResponse(BaseModel):
    task_id: str
    target_agent_id: str
    conversation_id: str
    screenplay_id: str
    status: str = "pending"


def _ensure_screenplay(screenplay_id: Optional[str], event_title: str = "Pulse Escalation") -> str:
    """Return existing screenplay_id or create a new one for Pulse escalation."""
    if screenplay_id:
        return screenplay_id

    try:
        from pymongo import MongoClient
        from bson import ObjectId

        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise RuntimeError("MONGO_URI not set")

        client = MongoClient(mongo_uri)
        db = client.conductor_state

        doc = {
            "_id": ObjectId(),
            "title": f"[Pulse] {event_title}",
            "content": (
                "# Pulse Escalation Screenplay\n\n"
                "Este roteiro foi criado automaticamente pelo sistema Pulse "
                "para rastrear a investigação e resolução de um evento de infraestrutura.\n\n"
                "Os agentes participantes compartilham este contexto.\n"
            ),
            "working_directory": os.getenv("CONDUCTOR_HOST_CWD", os.path.expanduser("~")),
            "isDeleted": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        db.screenplays.insert_one(doc)
        logger.info("Created Pulse screenplay %s", doc["_id"])
        return str(doc["_id"])

    except Exception as e:
        logger.warning("Could not create screenplay: %s", e)
        raise


def _ensure_conversation(conversation_id: Optional[str]) -> str:
    """Return existing conversation_id or generate a new UUID."""
    return conversation_id or str(uuid.uuid4())


@router.post(
    "/agents/dispatch",
    response_model=DispatchResponse,
    summary="Dispatch work to another agent",
    operation_id="dispatch_agent",
)
def dispatch_agent(request: DispatchRequest):
    """
    Dispatch work to a target agent, optionally sharing conversation context.

    Used by:
    - **Agents** (via MCP tool) to chain to the next agent after completing their work
    - **Pulse Event Service** to trigger the first investigator agent

    The target agent will receive the `input` as its user message and will see
    the full conversation history if `conversation_id` is provided.
    """
    try:
        from src.core.services.agent_discovery_service import AgentDiscoveryService

        discovery = AgentDiscoveryService()
        agent_def = discovery.get_agent_definition(request.target_agent_id)
        if not agent_def:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{request.target_agent_id}' not found",
            )

        screenplay_id = _ensure_screenplay(request.screenplay_id, request.target_agent_id)
        conversation_id = _ensure_conversation(request.conversation_id)

        # Build prompt via discovery service (loads persona, playbook, history)
        xml_prompt = discovery.get_full_prompt(
            agent_id=request.target_agent_id,
            current_message=request.input,
            meta=False,
            new_agent_id=None,
            include_history=bool(request.conversation_id),  # history only if continuing conversation
            save_to_file=False,
            conversation_id=conversation_id,
            screenplay_id=screenplay_id,
        )

        # Determine provider
        from src.container import container

        provider = container.get_ai_provider(agent_definition=agent_def)

        # CWD: use screenplay's working_directory or host default
        cwd = os.getenv("CONDUCTOR_HOST_CWD", os.path.expanduser("~"))

        # Generate instance_id for context isolation
        import time, random, string
        instance_id = f"dispatch-{int(time.time())}-{''.join(random.choices(string.ascii_lowercase, k=6))}"

        # Submit task to MongoDB for the watcher to pick up
        from src.core.services.mongo_task_client import MongoTaskClient
        from bson import ObjectId

        task_client = MongoTaskClient()
        task_id = str(ObjectId())

        task_id = task_client.submit_task(
            task_id=task_id,
            agent_id=request.target_agent_id,
            cwd=cwd,
            timeout=getattr(agent_def, "timeout", 300) or 300,
            provider=provider,
            prompt=xml_prompt,
            instance_id=instance_id,
            conversation_id=conversation_id,
            screenplay_id=screenplay_id,
            is_councilor_execution=False,  # NOT councilor → history IS loaded
        )

        logger.info(
            "Dispatched task %s to %s (conversation=%s, screenplay=%s)",
            task_id, request.target_agent_id, conversation_id, screenplay_id,
        )

        return DispatchResponse(
            task_id=task_id,
            target_agent_id=request.target_agent_id,
            conversation_id=conversation_id,
            screenplay_id=screenplay_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Dispatch failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
