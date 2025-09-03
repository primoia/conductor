import pytest
import tempfile
import yaml
from pathlib import Path
from src.core.prompt_engine import PromptEngine
from src.core.exceptions import AgentNotFoundError, ConfigurationError


class TestPromptEngine:
    """Testes unitários para a classe PromptEngine."""

    @pytest.fixture
    def temp_agent_dir(self):
        """Create a temporary agent directory with test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            # Create agent.yaml
            agent_config = {
                "name": "TestAgent",
                "description": "A test agent",
                "prompt": "Be helpful and concise",
                "available_tools": ["tool1", "tool2"],
            }
            with open(agent_path / "agent.yaml", "w") as f:
                yaml.dump(agent_config, f)

            # Create persona.md
            persona_content = """# Persona: Test Assistant

You are a helpful test assistant.
Your name is {{agent_name}} and you work with {{agent_description}}.
"""
            with open(agent_path / "persona.md", "w") as f:
                f.write(persona_content)

            yield agent_path

    def test_prompt_engine_load_context_happy_path(self, temp_agent_dir):
        """Test successful loading of agent context."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)

        # Act
        prompt_engine.load_context()

        # Assert
        assert prompt_engine.agent_config is not None
        assert prompt_engine.persona_content is not None
        assert prompt_engine.agent_config["name"] == "TestAgent"
        assert (
            "Test Assistant" in prompt_engine.persona_content
        )  # placeholder resolved to friendly name
        assert "A test agent" in prompt_engine.persona_content

    def test_prompt_engine_fails_on_missing_config(self):
        """Test failure when agent.yaml is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)
            prompt_engine = PromptEngine(agent_path)

            with pytest.raises(AgentNotFoundError, match="agent.yaml not found"):
                prompt_engine.load_context()

    def test_prompt_engine_fails_on_missing_persona(self, temp_agent_dir):
        """Test failure when persona.md is missing."""
        # Remove persona.md
        (temp_agent_dir / "persona.md").unlink()

        prompt_engine = PromptEngine(temp_agent_dir)

        with pytest.raises(AgentNotFoundError, match="Persona file not found"):
            prompt_engine.load_context()

    def test_prompt_engine_resolves_placeholders_correctly(self, temp_agent_dir):
        """Test placeholder resolution in persona content."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)

        # Act
        prompt_engine.load_context()

        # Assert
        assert "{{agent_name}}" not in prompt_engine.persona_content
        assert "{{agent_description}}" not in prompt_engine.persona_content
        assert (
            "Test Assistant" in prompt_engine.persona_content
        )  # Uses friendly name from title
        assert "A test agent" in prompt_engine.persona_content

    def test_build_prompt_with_empty_history(self, temp_agent_dir):
        """Validate prompt construction with empty history."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()

        conversation_history = []
        user_input = "Hello, how are you?"

        # Act
        result = prompt_engine.build_prompt(conversation_history, user_input)

        # Assert
        assert "You are a helpful test assistant" in result
        assert "Be helpful and concise" in result
        assert user_input in result
        assert "Nenhum histórico de conversa para esta tarefa ainda." in result
        assert "### INSTRUÇÕES DO AGENTE" in result
        assert "### HISTÓRICO DA TAREFA ATUAL" in result
        assert "### NOVA INSTRUÇÃO DO USUÁRIO" in result

    def test_build_prompt_with_history(self, temp_agent_dir):
        """Validate prompt construction with conversation history."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()

        conversation_history = [
            {"prompt": "First question", "response": "First answer"},
            {"prompt": "Second question", "response": "Second answer"},
        ]
        user_input = "New question"

        # Act
        result = prompt_engine.build_prompt(conversation_history, user_input)

        # Assert
        assert "First question" in result
        assert "First answer" in result
        assert "Second question" in result
        assert "Second answer" in result
        assert user_input in result
        assert "Usuário: First question" in result
        assert "IA: First answer" in result
        assert "---" in result  # Separator between turns

    def test_build_prompt_without_loaded_context(self, temp_agent_dir):
        """Test that build_prompt fails if context not loaded."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)
        # Note: NOT calling load_context()

        # Act & Assert
        with pytest.raises(ValueError, match="Contexto não foi carregado"):
            prompt_engine.build_prompt([], "test input")

    def test_format_history(self, temp_agent_dir):
        """Test the _format_history method isolated."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()

        # Test with empty history
        empty_history = []
        result_empty = prompt_engine._format_history(empty_history)
        assert result_empty == "Nenhum histórico de conversa para esta tarefa ainda."

        # Test with single turn
        single_turn = [{"prompt": "Test", "response": "Response test"}]
        result_single = prompt_engine._format_history(single_turn)
        assert "Usuário: Test" in result_single
        assert "IA: Response test" in result_single

        # Test with multiple turns
        multiple_turns = [
            {"prompt": "Q1", "response": "A1"},
            {"prompt": "Q2", "response": "A2"},
        ]
        result_multiple = prompt_engine._format_history(multiple_turns)
        assert "Usuário: Q1" in result_multiple
        assert "IA: A1" in result_multiple
        assert "Usuário: Q2" in result_multiple
        assert "IA: A2" in result_multiple
        assert result_multiple.count("---") == 1  # One separator between two turns

    def test_format_history_with_missing_fields(self, temp_agent_dir):
        """Test _format_history with missing fields in history."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()

        # Test with missing prompt field
        history_missing_prompt = [{"response": "Response without question"}]
        result = prompt_engine._format_history(history_missing_prompt)
        assert "Usuário: " in result  # Should handle missing prompt gracefully
        assert "IA: Response without question" in result

        # Test with missing response field
        history_missing_response = [{"prompt": "Question without answer"}]
        result = prompt_engine._format_history(history_missing_response)
        assert "Usuário: Question without answer" in result
        assert "IA: " in result  # Should handle missing response gracefully

    def test_get_available_tools(self, temp_agent_dir):
        """Test get_available_tools method."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()

        # Act
        tools = prompt_engine.get_available_tools()

        # Assert
        assert tools == ["tool1", "tool2"]

    def test_get_available_tools_empty(self):
        """Test get_available_tools with no config loaded."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            # Create minimal agent.yaml without available_tools
            agent_config = {"name": "MinimalAgent"}
            with open(agent_path / "agent.yaml", "w") as f:
                yaml.dump(agent_config, f)

            # Create minimal persona.md
            with open(agent_path / "persona.md", "w") as f:
                f.write("You are a minimal agent.")

            prompt_engine = PromptEngine(agent_path)
            prompt_engine.load_context()

            tools = prompt_engine.get_available_tools()
            assert tools == []

    def test_validate_config_missing_required_fields(self):
        """Test config validation with missing required fields."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            # Create invalid agent.yaml (missing 'name' field)
            agent_config = {"description": "Agent without name"}
            with open(agent_path / "agent.yaml", "w") as f:
                yaml.dump(agent_config, f)

            prompt_engine = PromptEngine(agent_path)

            with pytest.raises(
                ConfigurationError,
                match="Required field 'name' or 'id' missing in agent configuration",
            ):
                prompt_engine.load_context()

    def test_extract_persona_title(self, temp_agent_dir):
        """Test persona title extraction."""
        # Arrange
        prompt_engine = PromptEngine(temp_agent_dir)

        # Test with title
        persona_with_title = "# Persona: Creative Writer Agent\nYou write stories."
        title = prompt_engine._extract_persona_title(persona_with_title)
        assert title == "Creative Writer"

        # Test without title
        persona_without_title = "You are an agent."
        title = prompt_engine._extract_persona_title(persona_without_title)
        assert title is None

    def test_persona_placeholder_edge_cases(self):
        """Test persona placeholder resolution edge cases."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            # Create agent config with empty values
            agent_config = {"name": "", "description": ""}
            with open(agent_path / "agent.yaml", "w") as f:
                yaml.dump(agent_config, f)

            # Create persona with placeholders
            persona_content = (
                "Agent: {{agent_name}}, Description: {{agent_description}}"
            )
            with open(agent_path / "persona.md", "w") as f:
                f.write(persona_content)

            prompt_engine = PromptEngine(agent_path)
            prompt_engine.load_context()

            # Should handle empty values gracefully
            assert prompt_engine.persona_content is not None
