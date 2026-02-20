# src/api/routes/sagas.py
"""
Saga API Routes (SAGA-016 Phase 4)

Exposes saga state, creation, execution, and rollback endpoints.
The rollback endpoint doubles as an MCP tool definition for agents.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.services.saga_manager import saga_manager, SagaStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system/sagas", tags=["Saga Healing"])


# ------------------------------------------------------------------
# Request / Response Models
# ------------------------------------------------------------------

class SagaStepRequest(BaseModel):
    """Definition of a single saga step."""
    name: str = Field(..., description="Human-readable step name")
    service: str = Field(..., description="MCP sidecar service name")
    action: Dict[str, Any] = Field(..., description="Action: {tool, payload}")
    compensation: Dict[str, Any] = Field(..., description="Compensation: {tool, payload}")


class SagaCreateRequest(BaseModel):
    """Request to create a new saga."""
    name: str = Field(..., min_length=1, max_length=200, description="Saga name")
    initiator: str = Field(..., description="Agent or user starting the saga")
    steps: List[SagaStepRequest] = Field(..., min_length=1, description="Ordered list of steps")


class SagaStateResponse(BaseModel):
    """Full saga state."""
    saga_id: str
    name: str
    initiator: str
    status: str
    steps: List[Dict[str, Any]]
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class SagaListResponse(BaseModel):
    """List of sagas."""
    total: int
    sagas: List[Dict[str, Any]]


class RollbackRequest(BaseModel):
    """Request to trigger saga rollback."""
    saga_id: str = Field(..., description="ID of the saga to rollback")
    reason: Optional[str] = Field(None, description="Reason for rollback")


class RollbackResponse(BaseModel):
    """Result of rollback execution."""
    saga_id: str
    status: str
    compensated_steps: int
    failed_compensations: int
    error: Optional[str] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get("/", response_model=SagaListResponse, summary="List sagas")
def list_sagas(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
):
    """List all sagas, optionally filtered by status."""
    sagas = saga_manager.list_sagas(status=status, limit=limit)
    return SagaListResponse(total=len(sagas), sagas=sagas)


@router.post("/", response_model=SagaStateResponse, status_code=201, summary="Create saga")
def create_saga(request: SagaCreateRequest):
    """
    Create a new saga with defined steps and compensation actions.

    Each step must specify:
    - service: name of the MCP sidecar
    - action: {tool: "tool_name", payload: {...}}
    - compensation: {tool: "tool_name", payload: {...}}
    """
    try:
        steps = [s.model_dump() for s in request.steps]
        saga = saga_manager.create_saga(
            name=request.name,
            initiator=request.initiator,
            steps=steps,
        )
        return SagaStateResponse(**saga.to_dict())
    except Exception as e:
        logger.error("Failed to create saga: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{saga_id}", response_model=SagaStateResponse, summary="Get saga state")
def get_saga(saga_id: str):
    """
    Get the current state of a saga including all steps.

    This is the primary endpoint for agents to inspect saga state
    before deciding whether to trigger a rollback.
    """
    saga = saga_manager.get_saga(saga_id)
    if not saga:
        raise HTTPException(status_code=404, detail=f"Saga {saga_id} not found")
    return SagaStateResponse(**saga.to_dict())


@router.post("/{saga_id}/execute", response_model=SagaStateResponse, summary="Execute saga")
async def execute_saga(saga_id: str):
    """
    Execute all steps of a saga sequentially.

    If any step fails, automatically triggers rollback of completed steps.
    """
    try:
        saga = await saga_manager.execute_saga(saga_id)
        return SagaStateResponse(**saga.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to execute saga %s: %s", saga_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback", response_model=RollbackResponse, summary="Execute saga rollback (MCP tool)")
async def execute_saga_rollback(request: RollbackRequest):
    """
    MCP tool: execute_saga_rollback

    Triggers compensating transactions for all completed steps in a saga,
    executing them in reverse order. This is the primary tool for agents
    to autonomously heal failed distributed transactions.

    The agent should:
    1. Inspect saga state via GET /{saga_id}
    2. Determine if rollback is needed
    3. Call this endpoint with the saga_id
    """
    saga = saga_manager.get_saga(request.saga_id)
    if not saga:
        raise HTTPException(status_code=404, detail=f"Saga {request.saga_id} not found")

    if saga.status == SagaStatus.ROLLED_BACK:
        return RollbackResponse(
            saga_id=request.saga_id,
            status="already_rolled_back",
            compensated_steps=sum(1 for s in saga.steps if s.status.value == "compensated"),
            failed_compensations=0,
        )

    if request.reason:
        logger.info("Rollback requested for saga %s: %s", request.saga_id, request.reason)

    try:
        saga = await saga_manager.rollback_saga(request.saga_id)
        compensated = sum(1 for s in saga.steps if s.status.value == "compensated")
        failed = sum(1 for s in saga.steps if s.status.value == "compensation_failed")

        return RollbackResponse(
            saga_id=request.saga_id,
            status=saga.status.value,
            compensated_steps=compensated,
            failed_compensations=failed,
            error=saga.error,
        )
    except Exception as e:
        logger.error("Rollback failed for saga %s: %s", request.saga_id, e)
        raise HTTPException(status_code=500, detail=str(e))
