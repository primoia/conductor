# src/core/services/saga_manager.py
"""
Saga Manager - Autonomous Saga Healing (SAGA-016 Phase 4)

Implements the Saga pattern for distributed transactions across
MCP services. Each saga tracks a sequence of steps with their
compensating actions, enabling automatic rollback on failure.

Flow:
1. Agent starts a saga via API (defines steps + compensating payloads)
2. SagaManager executes steps sequentially via MCP tool calls
3. On failure, SagaManager triggers compensating transactions
   for all completed steps in reverse order
4. State is persisted to MongoDB for auditability
"""

import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class SagaStatus(str, Enum):
    """Lifecycle status of a saga."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Lifecycle status of a saga step."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"
    COMPENSATION_FAILED = "compensation_failed"


class SagaStep:
    """A single step in a saga with its compensating action."""

    def __init__(
        self,
        step_id: str,
        name: str,
        service: str,
        action: Dict[str, Any],
        compensation: Dict[str, Any],
    ):
        self.step_id = step_id
        self.name = name
        self.service = service  # MCP sidecar name
        self.action = action  # {"tool": "tool_name", "payload": {...}}
        self.compensation = compensation  # {"tool": "tool_name", "payload": {...}}
        self.status = StepStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.executed_at: Optional[str] = None
        self.compensated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "service": self.service,
            "action": self.action,
            "compensation": self.compensation,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "executed_at": self.executed_at,
            "compensated_at": self.compensated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SagaStep":
        step = cls(
            step_id=data["step_id"],
            name=data["name"],
            service=data["service"],
            action=data["action"],
            compensation=data["compensation"],
        )
        step.status = StepStatus(data.get("status", "pending"))
        step.result = data.get("result")
        step.error = data.get("error")
        step.executed_at = data.get("executed_at")
        step.compensated_at = data.get("compensated_at")
        return step


class SagaState:
    """Full state of a saga instance."""

    def __init__(self, saga_id: str, name: str, initiator: str):
        self.saga_id = saga_id
        self.name = name
        self.initiator = initiator  # agent or user that started the saga
        self.status = SagaStatus.PENDING
        self.steps: List[SagaStep] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "saga_id": self.saga_id,
            "name": self.name,
            "initiator": self.initiator,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SagaState":
        saga = cls(
            saga_id=data["saga_id"],
            name=data["name"],
            initiator=data["initiator"],
        )
        saga.status = SagaStatus(data.get("status", "pending"))
        saga.steps = [SagaStep.from_dict(s) for s in data.get("steps", [])]
        saga.created_at = data.get("created_at", saga.created_at)
        saga.updated_at = data.get("updated_at", saga.updated_at)
        saga.completed_at = data.get("completed_at")
        saga.error = data.get("error")
        return saga


class SagaManager:
    """
    Manages saga lifecycle: creation, execution, and rollback.

    Sagas are persisted to MongoDB collection ``sagas``.
    """

    def __init__(self):
        self._sagas: Dict[str, SagaState] = {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _get_collection(self):
        from pymongo import MongoClient

        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGO_DATABASE", "conductor_state")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        return client[db_name]["sagas"]

    def _persist(self, saga: SagaState):
        """Save saga state to MongoDB."""
        saga.updated_at = datetime.now(timezone.utc).isoformat()
        try:
            collection = self._get_collection()
            collection.update_one(
                {"saga_id": saga.saga_id},
                {"$set": saga.to_dict()},
                upsert=True,
            )
        except Exception as e:
            logger.error("Failed to persist saga %s: %s", saga.saga_id, e)

    def _load(self, saga_id: str) -> Optional[SagaState]:
        """Load saga from MongoDB."""
        try:
            collection = self._get_collection()
            doc = collection.find_one({"saga_id": saga_id})
            if doc:
                return SagaState.from_dict(doc)
        except Exception as e:
            logger.error("Failed to load saga %s: %s", saga_id, e)
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_saga(
        self,
        name: str,
        initiator: str,
        steps: List[Dict[str, Any]],
    ) -> SagaState:
        """
        Create a new saga with the given steps.

        Each step dict must contain:
        - name: human-readable step name
        - service: MCP sidecar name to call
        - action: {"tool": "...", "payload": {...}}
        - compensation: {"tool": "...", "payload": {...}}
        """
        saga_id = f"saga_{uuid4().hex[:12]}"
        saga = SagaState(saga_id=saga_id, name=name, initiator=initiator)

        for i, step_data in enumerate(steps):
            step = SagaStep(
                step_id=f"{saga_id}_step_{i}",
                name=step_data["name"],
                service=step_data["service"],
                action=step_data["action"],
                compensation=step_data["compensation"],
            )
            saga.steps.append(step)

        self._sagas[saga_id] = saga
        self._persist(saga)
        logger.info("Saga created: %s (%s) with %d steps", saga_id, name, len(steps))
        return saga

    def get_saga(self, saga_id: str) -> Optional[SagaState]:
        """Get saga state from cache or MongoDB."""
        if saga_id in self._sagas:
            return self._sagas[saga_id]
        saga = self._load(saga_id)
        if saga:
            self._sagas[saga_id] = saga
        return saga

    def list_sagas(
        self,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List sagas from MongoDB, optionally filtered by status."""
        try:
            collection = self._get_collection()
            query = {}
            if status:
                query["status"] = status
            docs = list(
                collection.find(query, {"_id": 0})
                .sort("created_at", -1)
                .limit(limit)
            )
            return docs
        except Exception as e:
            logger.error("Failed to list sagas: %s", e)
            return []

    async def execute_saga(self, saga_id: str) -> SagaState:
        """
        Execute all steps in a saga sequentially.

        On any step failure, automatically triggers rollback of
        all previously completed steps.
        """
        saga = self.get_saga(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        if saga.status != SagaStatus.PENDING:
            raise ValueError(f"Saga {saga_id} is in {saga.status} state, cannot execute")

        saga.status = SagaStatus.RUNNING
        self._persist(saga)

        for step in saga.steps:
            try:
                result = await self._execute_step(step)
                step.status = StepStatus.COMPLETED
                step.result = result
                step.executed_at = datetime.now(timezone.utc).isoformat()
                self._persist(saga)

            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)[:500]
                saga.error = f"Step '{step.name}' failed: {str(e)[:200]}"
                self._persist(saga)

                logger.error(
                    "Saga %s step '%s' failed: %s. Triggering rollback.",
                    saga_id, step.name, e,
                )
                await self.rollback_saga(saga_id)
                return self.get_saga(saga_id)

        saga.status = SagaStatus.COMPLETED
        saga.completed_at = datetime.now(timezone.utc).isoformat()
        self._persist(saga)
        logger.info("Saga %s completed successfully", saga_id)
        return saga

    async def rollback_saga(self, saga_id: str) -> SagaState:
        """
        Rollback a saga by executing compensating transactions
        for all completed steps in reverse order.
        """
        saga = self.get_saga(saga_id)
        if not saga:
            raise ValueError(f"Saga {saga_id} not found")

        saga.status = SagaStatus.COMPENSATING
        self._persist(saga)

        # Get completed steps in reverse order
        completed_steps = [
            s for s in reversed(saga.steps)
            if s.status == StepStatus.COMPLETED
        ]

        for step in completed_steps:
            try:
                await self._execute_compensation(step)
                step.status = StepStatus.COMPENSATED
                step.compensated_at = datetime.now(timezone.utc).isoformat()
                self._persist(saga)
                logger.info(
                    "Saga %s: compensated step '%s'", saga_id, step.name,
                )
            except Exception as e:
                step.status = StepStatus.COMPENSATION_FAILED
                step.error = f"Compensation failed: {str(e)[:300]}"
                self._persist(saga)
                logger.error(
                    "Saga %s: compensation failed for step '%s': %s",
                    saga_id, step.name, e,
                )

        saga.status = SagaStatus.ROLLED_BACK
        saga.completed_at = datetime.now(timezone.utc).isoformat()
        self._persist(saga)
        logger.info("Saga %s rolled back", saga_id)
        return saga

    # ------------------------------------------------------------------
    # Step execution
    # ------------------------------------------------------------------

    async def _execute_step(self, step: SagaStep) -> Dict[str, Any]:
        """Execute a saga step by calling the MCP sidecar tool."""
        return await self._call_mcp_tool(
            service=step.service,
            tool=step.action["tool"],
            payload=step.action.get("payload", {}),
        )

    async def _execute_compensation(self, step: SagaStep) -> Dict[str, Any]:
        """Execute the compensating action for a step."""
        return await self._call_mcp_tool(
            service=step.service,
            tool=step.compensation["tool"],
            payload=step.compensation.get("payload", {}),
        )

    async def _call_mcp_tool(
        self,
        service: str,
        tool: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Call an MCP sidecar tool via HTTP.

        Resolves the service name to a URL from the MCP registry,
        then POSTs to /tools/{tool_name}.
        """
        import httpx

        url = await self._resolve_service_url(service)
        if not url:
            raise ConnectionError(f"Service '{service}' not found in MCP registry")

        # MCP sidecar tool call: POST /tools/{tool_name}
        tool_url = f"{url.rstrip('/')}/tools/{tool}"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(tool_url, json=payload)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"MCP tool call failed: {tool} on {service} "
                    f"(HTTP {resp.status_code}): {resp.text[:200]}"
                )
            return resp.json()

    async def _resolve_service_url(self, service: str) -> Optional[str]:
        """Resolve MCP service name to its sidecar URL."""
        try:
            from pymongo import MongoClient

            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            db_name = os.getenv("MONGO_DATABASE", "conductor_state")
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            collection = client[db_name]["mcp_registry"]
            doc = collection.find_one({"name": service})
            client.close()

            if doc:
                # Prefer host_url for external access
                return doc.get("host_url") or doc.get("url", "")
        except Exception as e:
            logger.error("Failed to resolve service URL for %s: %s", service, e)
        return None


# Singleton
saga_manager = SagaManager()
