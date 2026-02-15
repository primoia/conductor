# src/api/routes/observations.py
"""
Task Observations Router - Endpoints para gerenciar observações de tasks por agentes.
Permite que agentes se inscrevam em tasks e recebam estado consolidado para injeção no prompt.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observations", tags=["observations"])

# MongoDB connection
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/conductor_state?authSource=admin")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "conductor_state")
CONSTRUCTION_API_URL = os.getenv("CONSTRUCTION_API_URL", "http://verticals-construction-api-projects:8001")
OBSERVATION_TIMEOUT = float(os.getenv("OBSERVATION_TIMEOUT_SECONDS", "10"))


def get_db():
    """Get MongoDB database connection."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[MONGO_DATABASE]


# ============================================================================
# Models
# ============================================================================

class ObservationSubscribeRequest(BaseModel):
    """Request para inscrever agente em uma task."""
    capability: str = Field(..., description="Nome semântico da capability")
    project_id: int = Field(..., description="ID do projeto no Construction PM")
    task_id: int = Field(..., description="ID da task a observar")
    description: str = Field(default="", description="Descrição para contexto")
    include_subtasks: bool = Field(default=False, description="Se deve incluir detalhes de subtasks")


class ObservationEntry(BaseModel):
    """Uma observação individual."""
    capability: str
    project_id: int
    task_id: int
    description: str = ""
    include_subtasks: bool = False
    subscribed_at: datetime


class SubtaskState(BaseModel):
    """Estado de uma subtask."""
    id: int
    name: str
    progress: int
    status: str


class CapabilitySource(BaseModel):
    """Fonte de dados de uma capability."""
    project_id: int
    task_id: int
    task_name: str = ""


class CapabilityState(BaseModel):
    """Estado de uma capability observada."""
    name: str
    progress: int
    status: str
    description: str = ""
    source: CapabilitySource
    subtasks: Optional[List[SubtaskState]] = None
    summary: str = ""


class AgentWorldStateResponse(BaseModel):
    """Response com estado consolidado do mundo para um agente."""
    agent_id: str
    capabilities: List[CapabilityState]
    timestamp: datetime


# ============================================================================
# Helper Functions
# ============================================================================

async def fetch_task_state(project_id: int, task_id: int, include_subtasks: bool = False) -> dict:
    """Fetch task state from Construction API."""
    try:
        async with httpx.AsyncClient(timeout=OBSERVATION_TIMEOUT) as client:
            # Get task details
            response = await client.get(f"{CONSTRUCTION_API_URL}/api/v1/tasks/{task_id}")
            if response.status_code != 200:
                logger.warning(f"Failed to fetch task {task_id}: {response.status_code}")
                return None

            task_data = response.json()

            result = {
                "id": task_data.get("id"),
                "name": task_data.get("name", ""),
                "progress": task_data.get("progress_percentage", task_data.get("progress", 0)),
                "status": task_data.get("status", "unknown"),
            }

            # Get subtasks if requested
            if include_subtasks:
                subtasks_response = await client.get(f"{CONSTRUCTION_API_URL}/api/v1/tasks/{task_id}/subtasks")
                if subtasks_response.status_code == 200:
                    subtasks_data = subtasks_response.json()
                    # Handle both list and object with "items" key
                    subtasks_list = subtasks_data if isinstance(subtasks_data, list) else subtasks_data.get("items", [])
                    result["subtasks"] = [
                        {
                            "id": st.get("id"),
                            "name": st.get("name", ""),
                            "progress": st.get("progress_percentage", st.get("progress", 0)),
                            "status": st.get("status", "unknown"),
                        }
                        for st in subtasks_list
                    ]

            return result
    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        return None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/{agent_id}/subscribe")
async def subscribe_to_task(agent_id: str, request: ObservationSubscribeRequest):
    """
    Inscreve um agente para observar uma task.
    """
    db = get_db()
    collection = db["agent_task_observations"]

    observation = {
        "capability": request.capability,
        "project_id": request.project_id,
        "task_id": request.task_id,
        "description": request.description,
        "include_subtasks": request.include_subtasks,
        "subscribed_at": datetime.utcnow(),
    }

    # Upsert: add observation to agent's list
    result = collection.update_one(
        {"agent_id": agent_id},
        {
            "$push": {"observations": observation},
            "$set": {"updated_at": datetime.utcnow()},
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )

    logger.info(f"Agent {agent_id} subscribed to task {request.task_id} (capability: {request.capability})")

    return {
        "status": "subscribed",
        "agent_id": agent_id,
        "observation": observation,
    }


@router.delete("/{agent_id}/unsubscribe/{task_id}")
async def unsubscribe_from_task(agent_id: str, task_id: int):
    """
    Remove inscrição de um agente em uma task.
    """
    db = get_db()
    collection = db["agent_task_observations"]

    result = collection.update_one(
        {"agent_id": agent_id},
        {
            "$pull": {"observations": {"task_id": task_id}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"No subscription found for agent {agent_id} and task {task_id}")

    logger.info(f"Agent {agent_id} unsubscribed from task {task_id}")

    return {
        "status": "unsubscribed",
        "agent_id": agent_id,
        "task_id": task_id,
    }


@router.get("/{agent_id}")
async def list_observations(agent_id: str):
    """
    Lista todas as observações de um agente.
    """
    db = get_db()
    collection = db["agent_task_observations"]

    doc = collection.find_one({"agent_id": agent_id})

    if not doc:
        return {
            "agent_id": agent_id,
            "observations": [],
            "count": 0,
        }

    observations = doc.get("observations", [])

    return {
        "agent_id": agent_id,
        "observations": observations,
        "count": len(observations),
    }


@router.get("/{agent_id}/state")
async def get_agent_world_state(agent_id: str):
    """
    Retorna o estado consolidado do mundo para um agente.
    Busca os dados atuais de cada task observada e retorna em formato pronto para injeção no prompt.
    """
    db = get_db()
    collection = db["agent_task_observations"]

    doc = collection.find_one({"agent_id": agent_id})

    if not doc:
        raise HTTPException(status_code=404, detail=f"No observations found for agent {agent_id}")

    observations = doc.get("observations", [])

    if not observations:
        return {
            "agent_id": agent_id,
            "capabilities": [],
            "timestamp": datetime.utcnow(),
        }

    # Fetch current state for each observed task
    capabilities = []
    for obs in observations:
        task_state = await fetch_task_state(
            obs["project_id"],
            obs["task_id"],
            obs.get("include_subtasks", False),
        )

        if task_state:
            # Build summary
            subtasks = task_state.get("subtasks", [])
            if subtasks:
                completed = sum(1 for st in subtasks if st["status"] == "completed")
                total = len(subtasks)
                summary = f"{task_state['name']} {task_state['status']}: {completed}/{total} subtasks completed ({task_state['progress']}%)"
            else:
                summary = f"{task_state['name']} {task_state['status']} ({task_state['progress']}%)"

            capability = {
                "name": obs["capability"],
                "progress": task_state["progress"],
                "status": task_state["status"],
                "description": obs.get("description", ""),
                "source": {
                    "project_id": obs["project_id"],
                    "task_id": obs["task_id"],
                    "task_name": task_state["name"],
                },
                "subtasks": [
                    {
                        "id": st["id"],
                        "name": st["name"],
                        "progress": st["progress"],
                        "status": st["status"],
                    }
                    for st in subtasks
                ] if subtasks else None,
                "summary": summary,
            }
            capabilities.append(capability)
        else:
            logger.warning(f"Could not fetch state for task {obs['task_id']}")

    return {
        "agent_id": agent_id,
        "capabilities": capabilities,
        "timestamp": datetime.utcnow(),
    }
