# src/core/services/pulse_event_service.py
"""
Pulse Event Service - Proactive Event Triggers (SAGA-016 Phase 2)

Dual event source:
1. RabbitMQ Dead Letter Queue listener - captures failed messages from DLX
2. MCP Mesh health change detector - detects sidecars going down/up

When critical events are detected, they are formatted as system events
and injected into Support Councilor agent sessions via the Conductor API.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PulseEvent:
    """A system event detected by the Pulse."""

    __slots__ = ("source", "severity", "title", "detail", "timestamp", "metadata")

    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_CRITICAL = "critical"

    def __init__(
        self,
        source: str,
        severity: str,
        title: str,
        detail: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.source = source
        self.severity = severity
        self.title = title
        self.detail = detail
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def to_prompt_text(self) -> str:
        """Format event as text suitable for injection into an agent prompt."""
        return (
            f"[SYSTEM EVENT - {self.severity.upper()}]\n"
            f"Source: {self.source}\n"
            f"Time: {self.timestamp}\n"
            f"Title: {self.title}\n"
            f"Detail: {self.detail}\n"
            f"Metadata: {json.dumps(self.metadata)}"
        )


class PulseEventService:
    """
    Proactive event detection and alert injection.

    Runs two background loops:
    - RabbitMQ DLQ consumer (if RabbitMQ is reachable)
    - MCP Mesh health watcher (compares snapshots to detect changes)
    """

    DLQ_EXCHANGE = "primoia.dlx"
    DLQ_QUEUE = "primoia.dead-letters"
    HEALTH_CHECK_INTERVAL = 30  # seconds

    def __init__(self):
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._event_log: List[Dict[str, Any]] = []
        self._max_log_size = 200
        self._previous_mesh_snapshot: Dict[str, str] = {}  # name -> status
        self._rabbitmq_available = False

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent events (most recent first)."""
        return list(reversed(self._event_log[-limit:]))

    async def start(self):
        """Start all event listeners."""
        if self._running:
            return
        self._running = True

        # Start RabbitMQ DLQ listener
        self._tasks.append(asyncio.create_task(self._dlq_listener_loop()))
        # Start mesh health watcher
        self._tasks.append(asyncio.create_task(self._mesh_health_watcher_loop()))

        logger.info("Pulse Event Service started")

    async def stop(self):
        """Stop all event listeners."""
        self._running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._tasks.clear()
        logger.info("Pulse Event Service stopped")

    # ------------------------------------------------------------------
    # RabbitMQ DLQ listener
    # ------------------------------------------------------------------

    async def _dlq_listener_loop(self):
        """Connect to RabbitMQ and consume dead-lettered messages."""
        while self._running:
            try:
                connection = await self._connect_rabbitmq()
                if connection is None:
                    # RabbitMQ not available - wait and retry
                    await asyncio.sleep(30)
                    continue

                self._rabbitmq_available = True
                logger.info("Connected to RabbitMQ DLQ")

                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)

                # Declare dead letter exchange and queue (aio-pika v9 API)
                import aio_pika

                exchange = await channel.declare_exchange(
                    self.DLQ_EXCHANGE,
                    type=aio_pika.ExchangeType.FANOUT,
                    durable=True,
                )
                queue = await channel.declare_queue(
                    self.DLQ_QUEUE,
                    durable=True,
                )
                await queue.bind(exchange)

                # Consume messages
                async for message in queue:
                    if not self._running:
                        break
                    try:
                        body = message.body.decode("utf-8", errors="replace")
                        headers = dict(message.headers) if message.headers else {}
                        routing_key = message.routing_key or "unknown"

                        event = PulseEvent(
                            source="rabbitmq_dlq",
                            severity=PulseEvent.SEVERITY_WARNING,
                            title=f"Dead-lettered message from {routing_key}",
                            detail=body[:500],
                            metadata={
                                "routing_key": routing_key,
                                "exchange": headers.get("x-first-death-exchange", "unknown"),
                                "reason": headers.get("x-first-death-reason", "unknown"),
                                "queue": headers.get("x-first-death-queue", "unknown"),
                            },
                        )
                        self._record_event(event)
                        await self._inject_alert(event)
                        await message.ack()
                    except Exception as e:
                        logger.error("Error processing DLQ message: %s", e)
                        try:
                            await message.nack(requeue=False)
                        except Exception:
                            pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._rabbitmq_available = False
                logger.warning("RabbitMQ DLQ connection lost: %s. Retrying in 30s.", e)
                await asyncio.sleep(30)

    async def _connect_rabbitmq(self):
        """Attempt to connect to RabbitMQ. Returns connection or None."""
        try:
            import aio_pika
        except ImportError:
            logger.info("aio_pika not installed - RabbitMQ DLQ listener disabled")
            return None

        amqp_url = os.getenv(
            "AMQP_URL",
            "amqp://admin:PrimoiaSecure2025!RabbitMQ@primoia-shared-rabbitmq:5672/",
        )

        try:
            connection = await aio_pika.connect_robust(
                amqp_url,
                timeout=5,
            )
            return connection
        except Exception as e:
            logger.info("Cannot connect to RabbitMQ: %s", e)
            return None

    # ------------------------------------------------------------------
    # MCP Mesh health watcher
    # ------------------------------------------------------------------

    async def _mesh_health_watcher_loop(self):
        """Detect MCP sidecar health changes by comparing mesh snapshots."""
        while self._running:
            try:
                await asyncio.sleep(self.HEALTH_CHECK_INTERVAL)
                if not self._running:
                    break
                await self._check_mesh_health_changes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Mesh health watcher error: %s", e)
                await asyncio.sleep(10)

    async def _check_mesh_health_changes(self):
        """Compare current mesh to previous snapshot and emit events."""
        try:
            from src.core.services.mcp_mesh_service import mesh_service
        except ImportError:
            return

        mesh = mesh_service.get_mesh()
        current_snapshot: Dict[str, str] = {}

        for node in mesh.get("nodes", []):
            name = node["name"]
            status = node["status"]
            current_snapshot[name] = status

            prev_status = self._previous_mesh_snapshot.get(name)

            if prev_status is None:
                # New node discovered
                if status == "healthy":
                    event = PulseEvent(
                        source="mesh_watcher",
                        severity=PulseEvent.SEVERITY_INFO,
                        title=f"MCP sidecar discovered: {name}",
                        detail=f"{name} is now online (port {node.get('port', '?')}, {node.get('tools_count', 0)} tools)",
                        metadata={"node": name, "status": status, "port": node.get("port")},
                    )
                    self._record_event(event)

            elif prev_status == "healthy" and status != "healthy":
                # Service went down
                event = PulseEvent(
                    source="mesh_watcher",
                    severity=PulseEvent.SEVERITY_CRITICAL,
                    title=f"MCP sidecar DOWN: {name}",
                    detail=f"{name} changed from healthy to {status}. Error: {node.get('error', 'N/A')}",
                    metadata={"node": name, "prev_status": prev_status, "new_status": status},
                )
                self._record_event(event)
                await self._inject_alert(event)

            elif prev_status != "healthy" and status == "healthy":
                # Service recovered
                event = PulseEvent(
                    source="mesh_watcher",
                    severity=PulseEvent.SEVERITY_INFO,
                    title=f"MCP sidecar RECOVERED: {name}",
                    detail=f"{name} is healthy again (was {prev_status})",
                    metadata={"node": name, "prev_status": prev_status, "new_status": status},
                )
                self._record_event(event)

        # Detect removed nodes
        for name in set(self._previous_mesh_snapshot) - set(current_snapshot):
            event = PulseEvent(
                source="mesh_watcher",
                severity=PulseEvent.SEVERITY_WARNING,
                title=f"MCP sidecar REMOVED: {name}",
                detail=f"{name} is no longer in the registry",
                metadata={"node": name},
            )
            self._record_event(event)

        self._previous_mesh_snapshot = current_snapshot

    # ------------------------------------------------------------------
    # Alert injection via dispatch
    # ------------------------------------------------------------------

    async def _inject_alert(self, event: PulseEvent):
        """
        Dispatch the event to the appropriate agent via the /agents/dispatch
        endpoint. The agent receives the event as input with full conversation
        context, enabling it to investigate and chain to other agents.

        Info events are not dispatched (handled autonomously or ignored).
        """
        if event.severity == PulseEvent.SEVERITY_INFO:
            return

        try:
            await self._dispatch_to_agent(event)
        except Exception as e:
            logger.warning("Could not dispatch alert: %s", e)

    async def _dispatch_to_agent(self, event: PulseEvent):
        """Dispatch event to Support_Agent via the Agent Task Queue (RabbitMQ).

        Falls back to HTTP /agents/dispatch if the queue is unavailable.
        """
        support_agent_id = os.getenv(
            "SUPPORT_COUNCILOR_AGENT_ID", "Support_Agent"
        )

        prompt = (
            f"PROACTIVE SYSTEM ALERT:\n\n"
            f"{event.to_prompt_text()}\n\n"
            f"Investigate this event:\n"
            f"1. Check MCP mesh health with get_mesh\n"
            f"2. Review recent events with list_pulse_events\n"
            f"3. Assess impact and determine root cause\n"
            f"4. Create a task in the Construction PM backlog via create_task with your findings\n"
            f"5. If the issue requires infrastructure action, dispatch to DevOps_Agent using dispatch_agent\n"
            f"6. Log your analysis using write_screenplay_log\n"
        )

        # Try RabbitMQ queue first (priority=8 for Pulse escalations)
        try:
            from src.core.services.agent_task_queue_service import (
                AgentTaskMessage,
                agent_task_queue_service,
            )

            msg = AgentTaskMessage(
                agent_id=support_agent_id,
                input=prompt,
                priority=8,
                source="pulse",
            )
            published = await agent_task_queue_service.publish(msg)
            if published:
                logger.info(
                    "Enqueued Pulse alert for %s (task=%s, priority=8)",
                    support_agent_id,
                    msg.task_id,
                )
                return
            else:
                logger.warning("Queue publish failed, falling back to HTTP dispatch")
        except Exception as e:
            logger.warning("Queue unavailable (%s), falling back to HTTP dispatch", e)

        # Fallback: HTTP dispatch
        conductor_api_url = os.getenv(
            "CONDUCTOR_API_URL", "http://primoia-conductor-api:8000"
        )

        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{conductor_api_url}/agents/dispatch",
                json={
                    "target_agent_id": support_agent_id,
                    "input": prompt,
                },
            )
            if resp.status_code < 300:
                data = resp.json()
                logger.info(
                    "Dispatched %s to %s via HTTP fallback (task=%s, conversation=%s)",
                    event.title,
                    support_agent_id,
                    data.get("task_id"),
                    data.get("conversation_id"),
                )
            else:
                logger.warning(
                    "Failed to dispatch alert (HTTP %d): %s",
                    resp.status_code,
                    resp.text[:200],
                )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _record_event(self, event: PulseEvent):
        """Append event to the in-memory log."""
        self._event_log.append(event.to_dict())
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
        logger.info("[PULSE] %s: %s", event.severity.upper(), event.title)


# Singleton
pulse_service = PulseEventService()
