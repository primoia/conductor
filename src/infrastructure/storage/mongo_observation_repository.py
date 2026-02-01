# src/infrastructure/storage/mongo_observation_repository.py
"""Repository for storing task observations in MongoDB."""

import os
from typing import Dict, Any, List
from pymongo import MongoClient
from datetime import datetime


class MongoObservationRepository:
    """Repository for storing and retrieving task observations from MongoDB."""

    def __init__(self, connection_string: str, db_name: str = "conductor_state"):
        is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER") == "true"

        if not is_docker and "host.docker.internal" in connection_string:
            connection_string = connection_string.replace("host.docker.internal", "localhost")

        self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self.observations_collection = self.db["observations"]

        self._safe_create_index(self.observations_collection, "task_id")
        self._safe_create_index(self.observations_collection, "agent_id")
        self._safe_create_index(self.observations_collection, "created_at")

    def _safe_create_index(self, collection, key, **kwargs):
        """Create index silently, ignoring if it already exists."""
        try:
            collection.create_index(key, **kwargs)
        except Exception as e:
            if hasattr(e, 'code') and e.code == 86:
                pass
            else:
                print(f"⚠️  Warning: Could not create index in MongoDB: {e}")

    def save_observation(self, observation: Dict[str, Any]) -> str:
        """Save a task observation."""
        observation["created_at"] = datetime.utcnow()
        result = self.observations_collection.insert_one(observation)
        return str(result.inserted_id)

    def get_observations_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all observations for a specific task."""
        observations = list(self.observations_collection.find(
            {"task_id": task_id}
        ).sort("created_at", -1))
        for obs in observations:
            obs["_id"] = str(obs["_id"])
        return observations

    def get_observations_by_agent(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent observations for a specific agent."""
        observations = list(self.observations_collection.find(
            {"agent_id": agent_id}
        ).sort("created_at", -1).limit(limit))
        for obs in observations:
            obs["_id"] = str(obs["_id"])
        return observations

    def get_recent_observations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the most recent observations."""
        observations = list(self.observations_collection.find().sort(
            "created_at", -1
        ).limit(limit))
        for obs in observations:
            obs["_id"] = str(obs["_id"])
        return observations

    def delete_observations_by_task(self, task_id: str) -> int:
        """Delete all observations for a specific task."""
        result = self.observations_collection.delete_many({"task_id": task_id})
        return result.deleted_count
