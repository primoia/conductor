# src/core/services/agent_task_queue_service.py
"""
Agent Task Queue Service - RabbitMQ-based async task execution.

Publishes agent task messages to RabbitMQ and consumes them for execution.
Consumer builds prompts fresh (not from message) to ensure up-to-date history,
then submits to MongoDB for the watcher to pick up.

Failures go to DLQ (primoia.dlx) -> Pulse captures -> alerts Support_Agent.
"""

import asyncio
import json
import logging
import os
import random
import string
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

logger = logging.getLogger(__name__)


class AgentTaskMessage:
    """Lightweight message schema for the agent task queue."""

    __slots__ = (
        "task_id",
        "agent_id",
        "conversation_id",
        "screenplay_id",
        "input",
        "priority",
        "source",
        "parent_task_id",
        "idempotency_key",
        "enqueued_at",
    )

    def __init__(
        self,
        agent_id: str,
        input: str,
        task_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        screenplay_id: Optional[str] = None,
        priority: int = 5,
        source: str = "dispatch_api",
        parent_task_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        enqueued_at: Optional[str] = None,
    ):
        self.task_id = task_id or str(ObjectId())
        self.agent_id = agent_id
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.screenplay_id = screenplay_id
        self.input = input
        self.priority = max(0, min(9, priority))
        self.source = source
        self.parent_task_id = parent_task_id
        self.idempotency_key = idempotency_key or str(uuid.uuid4())
        self.enqueued_at = enqueued_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "conversation_id": self.conversation_id,
            "screenplay_id": self.screenplay_id,
            "input": self.input,
            "priority": self.priority,
            "source": self.source,
            "parent_task_id": self.parent_task_id,
            "idempotency_key": self.idempotency_key,
            "enqueued_at": self.enqueued_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentTaskMessage":
        return cls(
            task_id=data.get("task_id"),
            agent_id=data["agent_id"],
            conversation_id=data.get("conversation_id"),
            screenplay_id=data.get("screenplay_id"),
            input=data["input"],
            priority=data.get("priority", 5),
            source=data.get("source", "dispatch_api"),
            parent_task_id=data.get("parent_task_id"),
            idempotency_key=data.get("idempotency_key"),
            enqueued_at=data.get("enqueued_at"),
        )


class AgentTaskQueueService:
    """
    RabbitMQ-based agent task queue with publisher and consumer.

    Topology:
        Exchange: conductor.agent-tasks (DIRECT, durable)
            -> Queue: conductor.agent-task-queue
                - durable, x-max-priority=10
                - x-dead-letter-exchange=primoia.dlx
                - routing_key=agent.task
                - Consumer: prefetch_count=1
    """

    EXCHANGE_NAME = "conductor.agent-tasks"
    QUEUE_NAME = "conductor.agent-task-queue"
    ROUTING_KEY = "agent.task"
    DLX_EXCHANGE = "primoia.dlx"

    def __init__(self):
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
        self._connection = None
        self._channel = None
        self._exchange = None
        self._rabbitmq_available = False
        self._mongo_client = None

        # Stats
        self._stats = {
            "published": 0,
            "consumed": 0,
            "failed": 0,
            "deduplicated": 0,
        }

    def _get_mongo_db(self):
        """Get a reusable MongoDB database handle."""
        if self._mongo_client is None:
            from pymongo import MongoClient
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                return None
            self._mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        return self._mongo_client.conductor_state

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self):
        """Start the consumer loop."""
        if self._running:
            return
        self._running = True
        self._consumer_task = asyncio.create_task(self._consumer_loop())
        logger.info("Agent Task Queue Service started")

    async def stop(self):
        """Stop the consumer loop and close connections."""
        self._running = False
        if self._consumer_task and not self._consumer_task.done():
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        self._consumer_task = None

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        self._connection = None
        self._channel = None
        self._exchange = None

        logger.info("Agent Task Queue Service stopped")

    # ------------------------------------------------------------------
    # Publisher
    # ------------------------------------------------------------------

    async def publish(self, msg: AgentTaskMessage) -> bool:
        """
        Publish an agent task message to RabbitMQ.

        Returns True if published successfully, False otherwise.
        """
        try:
            import aio_pika

            if not self._exchange:
                await self._ensure_topology()

            if not self._exchange:
                logger.error("Cannot publish: RabbitMQ topology not available")
                return False

            body = json.dumps(msg.to_dict()).encode("utf-8")

            await self._exchange.publish(
                aio_pika.Message(
                    body=body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    priority=msg.priority,
                    message_id=msg.idempotency_key,
                    timestamp=datetime.now(timezone.utc),
                ),
                routing_key=self.ROUTING_KEY,
            )

            self._stats["published"] += 1
            logger.info(
                "Published task %s for agent %s (priority=%d, key=%s)",
                msg.task_id,
                msg.agent_id,
                msg.priority,
                msg.idempotency_key,
            )
            return True

        except Exception as e:
            logger.error("Failed to publish task: %s", e)
            return False

    # ------------------------------------------------------------------
    # Consumer
    # ------------------------------------------------------------------

    async def _consumer_loop(self):
        """Main consumer loop - connects, declares topology, consumes."""
        while self._running:
            try:
                await self._ensure_topology()
                if not self._channel:
                    await asyncio.sleep(10)
                    continue

                import aio_pika

                queue = await self._channel.declare_queue(
                    self.QUEUE_NAME,
                    durable=True,
                    arguments={
                        "x-max-priority": 10,
                        "x-dead-letter-exchange": self.DLX_EXCHANGE,
                    },
                )

                await self._channel.set_qos(prefetch_count=1)

                logger.info("Consumer listening on %s", self.QUEUE_NAME)

                async for message in queue:
                    if not self._running:
                        break
                    await self._process_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._rabbitmq_available = False
                self._exchange = None
                self._channel = None
                self._connection = None
                logger.warning(
                    "Consumer connection lost: %s. Retrying in 10s.", e
                )
                await asyncio.sleep(10)

    async def _process_message(self, message):
        """Process a single message from the queue."""
        try:
            body = message.body.decode("utf-8")
            data = json.loads(body)
            msg = AgentTaskMessage.from_dict(data)

            logger.info(
                "Consuming task %s for agent %s (key=%s)",
                msg.task_id,
                msg.agent_id,
                msg.idempotency_key,
            )

            # Layer 1: Dedup check via MongoDB
            if self._is_duplicate(msg.idempotency_key):
                logger.info(
                    "Duplicate task skipped (key=%s)", msg.idempotency_key
                )
                self._stats["deduplicated"] += 1
                await message.ack()
                return

            # Validate agent exists
            agent_def = self._get_agent_definition(msg.agent_id)
            if not agent_def:
                logger.error("Agent '%s' not found, sending to DLQ", msg.agent_id)
                self._stats["failed"] += 1
                await message.nack(requeue=False)
                return

            # Ensure screenplay
            screenplay_id = self._ensure_screenplay(
                msg.screenplay_id, msg.agent_id
            )

            # Inject delegation context so agent always passes parent_task_id
            delegation_footer = (
                f"\n\n---\n"
                f"[DELEGATION CONTEXT — mandatory when calling enqueue_agent]\n"
                f"parent_task_id: \"{msg.task_id}\"\n"
                f"conversation_id: \"{msg.conversation_id}\"\n"
                f"screenplay_id: \"{screenplay_id}\"\n"
                f"When delegating work to another agent via enqueue_agent, "
                f"you MUST include parent_task_id=\"{msg.task_id}\". "
                f"The server will automatically enforce the correct "
                f"conversation_id and screenplay_id.\n"
                f"---"
            )
            input_with_context = msg.input + delegation_footer

            # Build prompt fresh (with up-to-date history)
            xml_prompt = self._build_prompt(
                agent_id=msg.agent_id,
                input_text=input_with_context,
                conversation_id=msg.conversation_id,
                screenplay_id=screenplay_id,
            )

            if not xml_prompt:
                logger.error("Failed to build prompt for agent %s", msg.agent_id)
                self._stats["failed"] += 1
                await message.nack(requeue=False)
                return

            # Determine provider
            provider = self._get_provider(agent_def)

            # Generate instance_id
            instance_id = (
                f"queue-{int(time.time())}-"
                f"{''.join(random.choices(string.ascii_lowercase, k=6))}"
            )

            # Submit task to MongoDB (watcher picks it up)
            from src.core.services.mongo_task_client import MongoTaskClient

            task_client = MongoTaskClient()
            cwd = os.getenv("CONDUCTOR_HOST_CWD", os.path.expanduser("~"))

            task_client.submit_task(
                task_id=msg.task_id,
                agent_id=msg.agent_id,
                cwd=cwd,
                timeout=getattr(agent_def, "timeout", 300) or 300,
                provider=provider,
                prompt=xml_prompt,
                instance_id=instance_id,
                conversation_id=msg.conversation_id,
                screenplay_id=screenplay_id,
                is_councilor_execution=False,
                idempotency_key=msg.idempotency_key,
            )

            self._stats["consumed"] += 1
            await message.ack()

            logger.info(
                "Task %s submitted to MongoDB for agent %s",
                msg.task_id,
                msg.agent_id,
            )

        except Exception as e:
            logger.error("Error processing task message: %s", e, exc_info=True)
            self._stats["failed"] += 1
            try:
                await message.nack(requeue=False)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Topology setup
    # ------------------------------------------------------------------

    async def _ensure_topology(self):
        """Ensure RabbitMQ connection, channel, exchange, and queue exist."""
        if self._exchange and self._connection and not self._connection.is_closed:
            return

        try:
            import aio_pika
        except ImportError:
            logger.info("aio_pika not installed - Agent Task Queue disabled")
            return

        amqp_url = os.getenv(
            "AMQP_URL",
            "amqp://admin:PrimoiaSecure2025!RabbitMQ@primoia-shared-rabbitmq:5672/",
        )

        try:
            self._connection = await aio_pika.connect_robust(amqp_url, timeout=5)
            self._channel = await self._connection.channel()

            # Declare the task exchange
            self._exchange = await self._channel.declare_exchange(
                self.EXCHANGE_NAME,
                type=aio_pika.ExchangeType.DIRECT,
                durable=True,
            )

            # Declare the DLX (idempotent - already exists)
            await self._channel.declare_exchange(
                self.DLX_EXCHANGE,
                type=aio_pika.ExchangeType.FANOUT,
                durable=True,
            )

            # Declare the task queue with priority and DLX
            queue = await self._channel.declare_queue(
                self.QUEUE_NAME,
                durable=True,
                arguments={
                    "x-max-priority": 10,
                    "x-dead-letter-exchange": self.DLX_EXCHANGE,
                },
            )

            # Bind queue to exchange
            await queue.bind(self._exchange, routing_key=self.ROUTING_KEY)

            self._rabbitmq_available = True
            logger.info("RabbitMQ topology established for Agent Task Queue")

        except Exception as e:
            self._rabbitmq_available = False
            self._exchange = None
            self._channel = None
            self._connection = None
            logger.info("Cannot connect to RabbitMQ for task queue: %s", e)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_duplicate(self, idempotency_key: str) -> bool:
        """Check MongoDB for an existing task with this idempotency_key."""
        try:
            db = self._get_mongo_db()
            if db is None:
                return False
            existing = db.tasks.find_one(
                {"idempotency_key": idempotency_key},
                {"_id": 1},
            )
            return existing is not None
        except Exception as e:
            logger.warning("Dedup check failed: %s", e)
            return False

    def _get_agent_definition(self, agent_id: str):
        """Load agent definition via the discovery service."""
        try:
            from src.container import container

            discovery = container.get_agent_discovery_service()
            return discovery.get_agent_definition(agent_id)
        except Exception as e:
            logger.error("Failed to load agent definition for %s: %s", agent_id, e)
            return None

    def _ensure_screenplay(
        self, screenplay_id: Optional[str], agent_id: str
    ) -> str:
        """Return existing screenplay_id or create a new one."""
        if screenplay_id:
            return screenplay_id

        try:
            db = self._get_mongo_db()
            if db is None:
                raise RuntimeError("MONGO_URI not set")

            doc = {
                "_id": ObjectId(),
                "title": f"[TaskQueue] {agent_id}",
                "content": (
                    "# Task Queue Screenplay\n\n"
                    "Auto-created by the Agent Task Queue for tracking "
                    "queued agent execution context.\n"
                ),
                "working_directory": os.getenv(
                    "CONDUCTOR_HOST_CWD", os.path.expanduser("~")
                ),
                "isDeleted": False,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            db.screenplays.insert_one(doc)
            logger.info("Created TaskQueue screenplay %s", doc["_id"])
            return str(doc["_id"])

        except Exception as e:
            logger.warning("Could not create screenplay: %s", e)
            raise

    def _build_prompt(
        self,
        agent_id: str,
        input_text: str,
        conversation_id: str,
        screenplay_id: str,
    ) -> Optional[str]:
        """Build the full XML prompt for an agent using the discovery service."""
        try:
            from src.container import container

            discovery = container.get_agent_discovery_service()
            xml_prompt = discovery.get_full_prompt(
                agent_id=agent_id,
                current_message=input_text,
                meta=False,
                new_agent_id=None,
                include_history=True,
                save_to_file=False,
                conversation_id=conversation_id,
                screenplay_id=screenplay_id,
            )
            return xml_prompt
        except Exception as e:
            logger.error("Prompt build failed for %s: %s", agent_id, e)
            return None

    def _get_provider(self, agent_def) -> str:
        """Determine the AI provider for an agent."""
        try:
            from src.container import container

            return container.get_ai_provider(agent_definition=agent_def)
        except Exception:
            return "claude"

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return queue statistics."""
        return {
            "rabbitmq_available": self._rabbitmq_available,
            "running": self._running,
            **self._stats,
        }


# Singleton
agent_task_queue_service = AgentTaskQueueService()
