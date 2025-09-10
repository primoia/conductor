"""
Tests for core functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.core.agent_logic import AgentLogic
from src.core.domain import AgentNotEmbodied, ConfigurationError
from src.ports.state_repository import IStateRepository as StateRepository
from src.ports.llm_client import LLMClient


class MockStateRepository(StateRepository):
    """Mock state repository for testing."""

    def __init__(self):
        self.states = {}

    def load_state(self, agent_home_path: str, state_file_name: str):
        key = f"{agent_home_path}/{state_file_name}"
        return self.states.get(key, {"conversation_history": []})

    def save_state(self, agent_home_path: str, state_file_name: str, state_data):
        key = f"{agent_home_path}/{state_file_name}"
        self.states[key] = state_data
        return True

    def list_agents(self):
        return []


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self):
        self.persona = None
        self.conversation_history = []
        self.responses = ["Mock response"]
        self.call_count = 0

    def invoke(self, prompt: str) -> str:
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        # Don't store here - AgentLogic will handle it via add_to_conversation_history
        return response

    def set_persona(self, persona: str) -> None:
        self.persona = persona

    def add_to_conversation_history(self, user_input: str, ai_response: str) -> None:
        """Add user input and AI response to conversation history."""
        self.conversation_history.append({
            "user_input": user_input,
            "ai_response": ai_response,
            "timestamp": 1234567890
        })


class TestAgentLogic:
    """Test cases for AgentLogic."""

    def setup_method(self):
        """Setup for each test."""
        self.mock_state_repo = MockStateRepository()
        self.mock_llm_client = MockLLMClient()
        self.agent_logic = AgentLogic(self.mock_state_repo, self.mock_llm_client)

    def test_initialization(self):
        """Test AgentLogic initialization."""
        assert not self.agent_logic.is_embodied()
        assert self.agent_logic.get_current_agent() is None
        assert self.agent_logic.get_available_tools() == []

    def test_chat_without_embodiment(self):
        """Test chat raises exception when agent not embodied."""
        with pytest.raises(AgentNotEmbodied):
            self.agent_logic.chat("Hello")

    @patch("builtins.open")
    @patch("yaml.safe_load")
    @patch("pathlib.Path.exists")
    def test_embody_agent_success(self, mock_exists, mock_yaml_load, mock_open):
        """Test successful agent embodiment."""
        # Setup mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            "name": "TestAgent",
            "description": "Test agent",
            "persona_prompt_path": "persona.md",
        }
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "Test persona content"
        )

        # Create mock paths
        agent_home = Path("/test/agent/home")
        project_root = Path("/test/project")

        # Test embodiment
        success = self.agent_logic.embody_agent(
            environment="test",
            project="testproject",
            agent_id="testagent",
            agent_home_path=agent_home,
            project_root_path=project_root,
        )

        assert success
        assert self.agent_logic.is_embodied()
        assert self.agent_logic.get_current_agent() == "testagent"
        assert self.agent_logic.environment == "test"
        assert self.agent_logic.project == "testproject"

    @patch("pathlib.Path.exists")
    def test_embody_agent_missing_config(self, mock_exists):
        """Test embodiment fails with missing config."""
        # Setup mocks
        mock_exists.return_value = False

        agent_home = Path("/test/agent/home")
        project_root = Path("/test/project")

        success = self.agent_logic.embody_agent(
            environment="test",
            project="testproject",
            agent_id="testagent",
            agent_home_path=agent_home,
            project_root_path=project_root,
        )

        assert not success
        assert not self.agent_logic.is_embodied()

    def test_save_state_without_embodiment(self):
        """Test save state without embodiment."""
        result = self.agent_logic.save_agent_state()
        assert not result

    def test_chat_after_embodiment(self):
        """Test chat functionality after embodiment."""
        import tempfile
        import yaml

        # Create a temporary agent directory with real files for PromptEngine
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            # Create agent.yaml
            agent_config = {"name": "TestAgent", "description": "Test agent"}
            with open(agent_path / "agent.yaml", "w") as f:
                yaml.dump(agent_config, f)

            # Create persona.md
            with open(agent_path / "persona.md", "w") as f:
                f.write("You are a helpful test assistant.")

            # Setup embodied state with real path
            self.agent_logic.embodied = True
            self.agent_logic.current_agent = "testagent"
            self.agent_logic.agent_home_path = agent_path
            self.agent_logic.agent_config = {"state_file_path": "state.json"}

            response = self.agent_logic.chat("Hello")

            assert response == "Mock response"
            assert len(self.mock_llm_client.conversation_history) == 1
            # Verify that the user input and AI response were stored correctly
            conversation_entry = self.mock_llm_client.conversation_history[0]
            assert conversation_entry["user_input"] == "Hello"
            assert conversation_entry["ai_response"] == "Mock response"


class TestStateRepository:
    """Test cases for state repositories."""

    def test_mock_state_repository(self):
        """Test mock state repository."""
        repo = MockStateRepository()

        # Test initial empty state
        state = repo.load_state("/test/path", "state.json")
        assert state == {"conversation_history": []}

        # Test save and load
        test_data = {"conversation_history": [{"prompt": "test", "response": "test"}]}
        success = repo.save_state("/test/path", "state.json", test_data)
        assert success

        loaded_state = repo.load_state("/test/path", "state.json")
        assert loaded_state == test_data


if __name__ == "__main__":
    pytest.main([__file__])
