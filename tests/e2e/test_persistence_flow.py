# tests/e2e/test_persistence_flow.py
"""
End-to-end test to validate the complete persistence flow.

This test verifies that after executing a task through ConductorService,
the persistence layer correctly writes session.json, knowledge.json, and
history.log files to the filesystem.
"""

import pytest
import os
import json
import yaml
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
from src.core.conductor_service import ConductorService
from src.core.domain import TaskDTO


@pytest.fixture
def test_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_full_persistence_flow_for_agent_task(test_workspace):
    """
    Test the complete persistence flow from task execution to file creation.
    
    This test validates:
    1. Task execution completes successfully
    2. session.json is created/updated with task data
    3. knowledge.json is created/updated with task metadata
    4. history.log is created with task history entry
    """
    
    # === ARRANGE (Preparation) ===
    
    # Define test agent ID
    agent_id = "test_persistence_agent"
    
    # Create workspace structure
    workspace_path = Path(test_workspace) / ".conductor_workspace"
    agent_dir = workspace_path / "agents" / agent_id
    agent_dir.mkdir(parents=True)
    
    # Create minimal definition.yaml
    agent_definition = {
        "name": "Test Persistence Agent",
        "version": "1.0.0",
        "schema_version": "1.0",
        "description": "Agent for testing persistence functionality",
        "author": "test",
        "tags": ["test", "persistence"],
        "capabilities": ["basic_interaction"],
        "allowed_tools": []
    }
    
    with open(agent_dir / "definition.yaml", "w") as f:
        yaml.dump(agent_definition, f)
    
    # Create minimal persona.md
    persona_content = """# Test Persistence Agent Persona

You are a test agent designed to validate persistence functionality.
Your responses should be helpful and concise.
"""
    
    with open(agent_dir / "persona.md", "w") as f:
        f.write(persona_content)
    
    # Create initial session.json with agent_home_path
    initial_session = {
        "agent_home_path": str(agent_dir),
        "allowed_tools": [],
        "initial_setup": True
    }
    
    with open(agent_dir / "session.json", "w") as f:
        json.dump(initial_session, f, indent=2)
    
    # Create config.yaml for ConductorService
    config_path = Path(test_workspace) / "config.yaml"
    config_data = {
        "storage": {
            "type": "filesystem", 
            "path": str(workspace_path)
        },
        "tool_plugins": []
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    # Instantiate ConductorService
    conductor_service = ConductorService(config_path=str(config_path))
    
    # Create TaskDTO
    task = TaskDTO(
        agent_id=agent_id,
        user_input="Hello! This is a test task to validate persistence.",
        context={"test": True}
    )
    
    # === ACT (Action) ===
    
    # Execute the task
    result = conductor_service.execute_task(task)
    
    # === ASSERT (Verification) ===
    
    # Verify task execution was successful
    assert result.status == "success", f"Task execution failed: {result.output}"
    assert result.output is not None, "Task output should not be None"
    
    # Define file paths
    session_file = agent_dir / "session.json"
    knowledge_file = agent_dir / "knowledge.json"
    history_file = agent_dir / "history.log"
    
    # === Assert Persistence: session.json ===
    assert session_file.exists(), "session.json should exist after task execution"
    
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    # Verify original data is preserved
    assert session_data["agent_home_path"] == str(agent_dir), "Original agent_home_path should be preserved"
    assert session_data["initial_setup"] is True, "Original session data should be preserved"
    
    # Verify new persistence data was added
    assert "last_task_id" in session_data, "session.json should contain last_task_id"
    assert "last_interaction" in session_data, "session.json should contain last_interaction"
    assert "conversation_count" in session_data, "session.json should contain conversation_count"
    
    # Verify data types and basic validation
    assert isinstance(session_data["last_task_id"], str), "last_task_id should be a string"
    assert isinstance(session_data["last_interaction"], (int, float)), "last_interaction should be a timestamp"
    assert isinstance(session_data["conversation_count"], int), "conversation_count should be an integer"
    
    # === Assert Persistence: knowledge.json ===
    assert knowledge_file.exists(), "knowledge.json should exist after task execution"
    
    with open(knowledge_file, "r") as f:
        knowledge_data = json.load(f)
    
    # Verify knowledge data structure
    assert "last_task_execution" in knowledge_data, "knowledge.json should contain last_task_execution"
    
    last_execution = knowledge_data["last_task_execution"]
    assert "task_id" in last_execution, "last_task_execution should contain task_id"
    assert "timestamp" in last_execution, "last_task_execution should contain timestamp"
    assert "user_input_summary" in last_execution, "last_task_execution should contain user_input_summary"
    
    # Verify the task_id matches between session and knowledge
    assert session_data["last_task_id"] == last_execution["task_id"], "Task IDs should match between session and knowledge"
    
    # === Assert Persistence: history.log ===
    assert history_file.exists(), "history.log should exist after task execution"
    
    with open(history_file, "r") as f:
        history_lines = f.readlines()
    
    assert len(history_lines) > 0, "history.log should contain at least one entry"
    
    # Parse the last (and should be only) history entry
    last_entry = json.loads(history_lines[-1].strip())
    
    # Verify history entry structure
    required_fields = ["task_id", "agent_id", "timestamp", "user_input", "status", "output_length"]
    for field in required_fields:
        assert field in last_entry, f"history entry should contain {field}"
    
    # Verify history entry content
    assert last_entry["agent_id"] == agent_id, "History entry should have correct agent_id"
    assert last_entry["status"] == "success", "History entry should show success status"
    assert last_entry["user_input"] == task.user_input, "History entry should preserve original user input"
    assert last_entry["task_id"] == session_data["last_task_id"], "Task IDs should be consistent across all artifacts"
    
    # Verify data types
    assert isinstance(last_entry["timestamp"], (int, float)), "timestamp should be numeric"
    assert isinstance(last_entry["output_length"], int), "output_length should be an integer"
    assert last_entry["output_length"] > 0, "output_length should be positive"
    
    # === Additional Validation ===
    
    # Verify all task IDs are consistent across all artifacts
    task_ids = [
        session_data["last_task_id"],
        knowledge_data["last_task_execution"]["task_id"],
        last_entry["task_id"]
    ]
    assert len(set(task_ids)) == 1, "All task IDs should be identical across session, knowledge, and history"
    
    # Verify timestamps are reasonable (within last minute)
    import time
    current_time = time.time()
    for timestamp_field, timestamp_value in [
        ("session.last_interaction", session_data["last_interaction"]),
        ("knowledge.timestamp", knowledge_data["last_task_execution"]["timestamp"]),
        ("history.timestamp", last_entry["timestamp"])
    ]:
        time_diff = abs(current_time - timestamp_value)
        assert time_diff < 60, f"{timestamp_field} should be recent (within 60 seconds)"


# Additional test for multiple task executions
def test_persistence_with_multiple_tasks(test_workspace):
    """
    Test that persistence works correctly with multiple sequential task executions.
    """
    
    # Setup similar to previous test
    agent_id = "test_multi_task_agent"
    workspace_path = Path(test_workspace) / ".conductor_workspace"
    agent_dir = workspace_path / "agents" / agent_id
    agent_dir.mkdir(parents=True)
    
    # Create agent files
    agent_definition = {
        "name": "Multi Task Agent", "version": "1.0.0", "schema_version": "1.0",
        "description": "Agent for testing multiple task persistence", "author": "test",
        "tags": [], "capabilities": [], "allowed_tools": []
    }
    
    with open(agent_dir / "definition.yaml", "w") as f:
        yaml.dump(agent_definition, f)
    
    with open(agent_dir / "persona.md", "w") as f:
        f.write("You are a multi-task test agent.")
    
    initial_session = {
        "agent_home_path": str(agent_dir),
        "allowed_tools": []
    }
    
    with open(agent_dir / "session.json", "w") as f:
        json.dump(initial_session, f, indent=2)
    
    # Create config
    config_path = Path(test_workspace) / "config.yaml"
    config_data = {
        "storage": {"type": "filesystem", "path": str(workspace_path)},
        "tool_plugins": []
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    
    conductor_service = ConductorService(config_path=str(config_path))
    
    # Execute multiple tasks
    tasks = [
        TaskDTO(agent_id=agent_id, user_input="First test task"),
        TaskDTO(agent_id=agent_id, user_input="Second test task"),
        TaskDTO(agent_id=agent_id, user_input="Third test task")
    ]
    
    results = []
    for task in tasks:
        result = conductor_service.execute_task(task)
        assert result.status == "success", f"Task failed: {result.output}"
        results.append(result)
    
    # Verify final state
    history_file = agent_dir / "history.log"
    assert history_file.exists(), "history.log should exist"
    
    with open(history_file, "r") as f:
        history_lines = f.readlines()
    
    # Should have 3 history entries
    assert len(history_lines) == 3, f"Expected 3 history entries, got {len(history_lines)}"
    
    # Verify each entry
    for i, line in enumerate(history_lines):
        entry = json.loads(line.strip())
        assert entry["user_input"] == tasks[i].user_input, f"Entry {i} should match task input"
        assert entry["status"] == "success", f"Entry {i} should show success"
    
    # Verify session was updated with last task
    session_file = agent_dir / "session.json"
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    assert session_data["conversation_count"] == 3, "Session should show 3 conversations"
    
    # Verify the last task ID in session matches the last history entry
    last_history_entry = json.loads(history_lines[-1].strip())
    assert session_data["last_task_id"] == last_history_entry["task_id"], "Session should track the last task ID"