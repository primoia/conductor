# tests/api/test_sagas.py
"""
Tests for SAGA-016 Phase 4: Saga Manager and autonomous rollback.

Includes:
- Unit tests for SagaManager state management
- Integration test for simulated multi-service transaction failure
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from src.core.services.saga_manager import (
    SagaManager,
    SagaState,
    SagaStep,
    SagaStatus,
    StepStatus,
)


class TestSagaStep:
    """Tests for SagaStep data class."""

    def test_step_creation(self):
        step = SagaStep(
            step_id="s1",
            name="Create order",
            service="billing-sidecar",
            action={"tool": "create_order", "payload": {"amount": 100}},
            compensation={"tool": "cancel_order", "payload": {"reason": "rollback"}},
        )
        assert step.status == StepStatus.PENDING
        assert step.service == "billing-sidecar"
        assert step.action["tool"] == "create_order"

    def test_step_roundtrip(self):
        step = SagaStep(
            step_id="s1",
            name="Reserve inventory",
            service="inventory-sidecar",
            action={"tool": "reserve", "payload": {"sku": "ABC", "qty": 5}},
            compensation={"tool": "release", "payload": {"sku": "ABC", "qty": 5}},
        )
        step.status = StepStatus.COMPLETED
        step.result = {"reservation_id": "R123"}
        step.executed_at = "2026-01-01T00:00:00+00:00"

        d = step.to_dict()
        restored = SagaStep.from_dict(d)

        assert restored.step_id == "s1"
        assert restored.status == StepStatus.COMPLETED
        assert restored.result["reservation_id"] == "R123"


class TestSagaState:
    """Tests for SagaState data class."""

    def test_saga_creation(self):
        saga = SagaState(saga_id="saga_001", name="Order Flow", initiator="Agent_X")
        assert saga.status == SagaStatus.PENDING
        assert saga.steps == []
        assert saga.created_at is not None

    def test_saga_roundtrip(self):
        saga = SagaState(saga_id="saga_002", name="Payment Flow", initiator="Billing_Agent")
        saga.steps.append(SagaStep(
            step_id="s1", name="Charge card", service="payment-sidecar",
            action={"tool": "charge", "payload": {"amount": 50}},
            compensation={"tool": "refund", "payload": {"amount": 50}},
        ))
        saga.status = SagaStatus.RUNNING

        d = saga.to_dict()
        restored = SagaState.from_dict(d)

        assert restored.saga_id == "saga_002"
        assert restored.status == SagaStatus.RUNNING
        assert len(restored.steps) == 1
        assert restored.steps[0].name == "Charge card"


class TestSagaManager:
    """Tests for the SagaManager core logic."""

    def _make_manager(self):
        """Create a SagaManager with mocked persistence."""
        mgr = SagaManager()
        mgr._persist = MagicMock()  # Skip MongoDB writes
        mgr._load = MagicMock(return_value=None)
        return mgr

    def test_create_saga(self):
        mgr = self._make_manager()
        saga = mgr.create_saga(
            name="Test Saga",
            initiator="test_agent",
            steps=[
                {
                    "name": "Step 1",
                    "service": "svc-a",
                    "action": {"tool": "do_thing", "payload": {}},
                    "compensation": {"tool": "undo_thing", "payload": {}},
                },
                {
                    "name": "Step 2",
                    "service": "svc-b",
                    "action": {"tool": "do_other", "payload": {"x": 1}},
                    "compensation": {"tool": "undo_other", "payload": {"x": 1}},
                },
            ],
        )
        assert saga.saga_id.startswith("saga_")
        assert saga.status == SagaStatus.PENDING
        assert len(saga.steps) == 2
        assert saga.steps[0].name == "Step 1"
        assert saga.steps[1].service == "svc-b"

    def test_get_saga_from_cache(self):
        mgr = self._make_manager()
        saga = mgr.create_saga(
            name="Cached", initiator="test",
            steps=[{"name": "S1", "service": "s", "action": {"tool": "t", "payload": {}}, "compensation": {"tool": "c", "payload": {}}}],
        )
        # Should find it in cache without hitting MongoDB
        found = mgr.get_saga(saga.saga_id)
        assert found is not None
        assert found.name == "Cached"

    def test_execute_saga_success(self):
        """Test successful saga execution - all steps complete."""
        mgr = self._make_manager()
        saga = mgr.create_saga(
            name="Success Flow",
            initiator="test",
            steps=[
                {"name": "S1", "service": "svc-a", "action": {"tool": "a", "payload": {}}, "compensation": {"tool": "ca", "payload": {}}},
                {"name": "S2", "service": "svc-b", "action": {"tool": "b", "payload": {}}, "compensation": {"tool": "cb", "payload": {}}},
            ],
        )

        # Mock successful MCP tool calls
        async def mock_call(service, tool, payload):
            return {"status": "ok"}

        with patch.object(mgr, "_call_mcp_tool", side_effect=mock_call):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(mgr.execute_saga(saga.saga_id))

        assert result.status == SagaStatus.COMPLETED
        assert all(s.status == StepStatus.COMPLETED for s in result.steps)

    def test_execute_saga_failure_triggers_rollback(self):
        """
        Integration test: Simulated multi-service transaction failure.

        Scenario:
        - Step 1 (create_order) succeeds
        - Step 2 (charge_payment) succeeds
        - Step 3 (ship_item) FAILS
        - Rollback should compensate steps 2 and 1 in reverse order
        """
        mgr = self._make_manager()
        saga = mgr.create_saga(
            name="Order Pipeline",
            initiator="Order_Agent",
            steps=[
                {
                    "name": "Create Order",
                    "service": "order-sidecar",
                    "action": {"tool": "create_order", "payload": {"item": "widget", "qty": 3}},
                    "compensation": {"tool": "cancel_order", "payload": {"reason": "saga_rollback"}},
                },
                {
                    "name": "Charge Payment",
                    "service": "billing-sidecar",
                    "action": {"tool": "charge_card", "payload": {"amount": 150}},
                    "compensation": {"tool": "refund_card", "payload": {"amount": 150}},
                },
                {
                    "name": "Ship Item",
                    "service": "shipping-sidecar",
                    "action": {"tool": "create_shipment", "payload": {"dest": "NYC"}},
                    "compensation": {"tool": "cancel_shipment", "payload": {}},
                },
            ],
        )

        call_log = []

        async def mock_call(service, tool, payload):
            call_log.append({"service": service, "tool": tool, "type": "action"})
            if tool == "create_shipment":
                raise RuntimeError("Shipping service unavailable")
            return {"status": "ok"}

        async def mock_compensation_call(service, tool, payload):
            call_log.append({"service": service, "tool": tool, "type": "compensation"})
            return {"status": "compensated"}

        # First, patch for action calls (execute_saga calls _execute_step)
        # Then patch for compensation calls (rollback_saga calls _execute_compensation)
        original_execute_step = mgr._execute_step
        original_execute_compensation = mgr._execute_compensation

        async def patched_execute_step(step):
            call_log.append({"service": step.service, "tool": step.action["tool"], "type": "action"})
            if step.action["tool"] == "create_shipment":
                raise RuntimeError("Shipping service unavailable")
            return {"status": "ok"}

        async def patched_execute_compensation(step):
            call_log.append({"service": step.service, "tool": step.compensation["tool"], "type": "compensation"})
            return {"status": "compensated"}

        mgr._execute_step = patched_execute_step
        mgr._execute_compensation = patched_execute_compensation

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(mgr.execute_saga(saga.saga_id))

        # Assert saga was rolled back
        assert result.status == SagaStatus.ROLLED_BACK

        # Assert step statuses
        assert result.steps[0].status == StepStatus.COMPENSATED  # Create Order -> compensated
        assert result.steps[1].status == StepStatus.COMPENSATED  # Charge Payment -> compensated
        assert result.steps[2].status == StepStatus.FAILED  # Ship Item -> failed

        # Assert compensations ran in reverse order
        compensation_calls = [c for c in call_log if c["type"] == "compensation"]
        assert len(compensation_calls) == 2
        assert compensation_calls[0]["tool"] == "refund_card"  # Step 2 compensated first
        assert compensation_calls[1]["tool"] == "cancel_order"  # Step 1 compensated second

        # Assert error was recorded
        assert "Shipping service unavailable" in result.error

    def test_rollback_idempotent(self):
        """Test that rolling back an already-rolled-back saga is safe."""
        mgr = self._make_manager()
        saga = mgr.create_saga(
            name="Already Rolled Back",
            initiator="test",
            steps=[
                {"name": "S1", "service": "s", "action": {"tool": "a", "payload": {}}, "compensation": {"tool": "c", "payload": {}}},
            ],
        )
        saga.status = SagaStatus.ROLLED_BACK
        saga.steps[0].status = StepStatus.COMPENSATED

        # Requesting rollback on already-rolled-back saga should still work
        # (no steps to compensate)
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(mgr.rollback_saga(saga.saga_id))
        assert result.status == SagaStatus.ROLLED_BACK


class TestSagaAPIRoutes:
    """Tests for the Saga API endpoints."""

    def test_create_saga_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.routes.sagas import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        with patch("src.core.services.saga_manager.saga_manager._persist"):
            client = TestClient(app)
            resp = client.post("/system/sagas/", json={
                "name": "Test Saga",
                "initiator": "Test_Agent",
                "steps": [
                    {
                        "name": "Step 1",
                        "service": "svc-a",
                        "action": {"tool": "do_x", "payload": {}},
                        "compensation": {"tool": "undo_x", "payload": {}},
                    },
                ],
            })

            assert resp.status_code == 201
            data = resp.json()
            assert data["status"] == "pending"
            assert data["saga_id"].startswith("saga_")
            assert len(data["steps"]) == 1

    def test_get_saga_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.routes.sagas import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        # Pre-create a saga
        with patch("src.core.services.saga_manager.saga_manager._persist"):
            from src.core.services.saga_manager import saga_manager
            saga = saga_manager.create_saga(
                name="Lookup Test",
                initiator="test",
                steps=[{"name": "S1", "service": "s", "action": {"tool": "t", "payload": {}}, "compensation": {"tool": "c", "payload": {}}}],
            )

            client = TestClient(app)
            resp = client.get(f"/system/sagas/{saga.saga_id}")

            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Lookup Test"

    def test_get_saga_not_found(self):
        from fastapi.testclient import TestClient
        from src.api.routes.sagas import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        resp = client.get("/system/sagas/nonexistent_id")
        assert resp.status_code == 404

    def test_rollback_endpoint(self):
        from fastapi.testclient import TestClient
        from src.api.routes.sagas import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        # Pre-create a saga with a completed step
        with patch("src.core.services.saga_manager.saga_manager._persist"):
            from src.core.services.saga_manager import saga_manager
            saga = saga_manager.create_saga(
                name="Rollback Test",
                initiator="test",
                steps=[{"name": "S1", "service": "s", "action": {"tool": "t", "payload": {}}, "compensation": {"tool": "c", "payload": {}}}],
            )
            saga.status = SagaStatus.RUNNING
            saga.steps[0].status = StepStatus.COMPLETED

            # Mock the compensation execution
            async def mock_comp(step):
                return {"status": "ok"}

            with patch.object(saga_manager, "_execute_compensation", side_effect=mock_comp):
                client = TestClient(app)
                resp = client.post("/system/sagas/rollback", json={
                    "saga_id": saga.saga_id,
                    "reason": "Test rollback",
                })

                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "rolled_back"
                assert data["compensated_steps"] == 1
