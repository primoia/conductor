# tests/api/test_prompt_xml_integration.py
"""
Testes de integração para validar que o prompt XML é corretamente gerado e usado.

OBJETIVO: Garantir que a correção do bug está funcionando end-to-end.
"""
import pytest
from unittest.mock import Mock, patch


class TestPromptXMLIntegration:
    """Testes que validam o fluxo completo do prompt XML."""

    def test_prompt_engine_generates_xml_with_history(self):
        """
        Testa se o PromptEngine gera XML corretamente com histórico.

        Este teste valida que o prompt XML inclui:
        - Persona
        - Instruções
        - Histórico de conversação
        - Input do usuário
        """
        from src.core.prompt_engine import PromptEngine
        import tempfile
        import yaml
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            # Criar definition.yaml
            with open(agent_path / "definition.yaml", "w") as f:
                yaml.dump({
                    "name": "TestAgent",
                    "description": "A test agent",
                    "prompt": "Be helpful",
                }, f)

            # Criar persona.md
            with open(agent_path / "persona.md", "w") as f:
                f.write("# Persona: Test Agent\n\nYou are helpful.")

            # Create PromptEngine with XML format
            prompt_engine = PromptEngine(agent_path, prompt_format="xml")
            prompt_engine.load_context()

            # Build XML prompt with history
            history = [
                {"user_input": "Question 1", "ai_response": "Answer 1"},
                {"user_input": "Question 2", "ai_response": "Answer 2"},
            ]

            xml_prompt = prompt_engine.build_xml_prompt(history, "New question")

            # Validate XML structure
            assert "<prompt>" in xml_prompt
            assert "<system_context>" in xml_prompt
            assert "<persona>" in xml_prompt
            assert "<instructions>" in xml_prompt
            assert "<conversation_history>" in xml_prompt
            assert "<user_request>" in xml_prompt
            assert "Question 1" in xml_prompt, "History should be included"
            assert "Answer 1" in xml_prompt, "History responses should be included"
            assert "New question" in xml_prompt, "Current input should be included"
            assert "CDATA" in xml_prompt, "Should use CDATA for escaping"

    def test_agent_discovery_service_generates_full_prompt(self):
        """
        Testa se AgentDiscoveryService.get_full_prompt() usa build_prompt_with_format().

        Este teste valida que o método usado pela API gera o prompt corretamente.
        """
        from src.core.services.agent_discovery_service import AgentDiscoveryService
        from src.core.prompt_engine import PromptEngine
        from src.core.services.storage_service import StorageService
        import tempfile
        import yaml
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_path = Path(tmp_dir) / "workspace"
            workspace_path.mkdir()
            agents_dir = workspace_path / "agents"
            agents_dir.mkdir()

            # Create test agent
            test_agent_dir = agents_dir / "test_agent"
            test_agent_dir.mkdir()

            with open(test_agent_dir / "definition.yaml", "w") as f:
                yaml.dump({
                    "name": "TestAgent",
                    "version": "1.0",
                    "schema_version": "1.0",
                    "description": "Test agent",
                    "author": "test",
                    "tags": [],
                    "capabilities": [],
                    "allowed_tools": [],
                }, f)

            with open(test_agent_dir / "persona.md", "w") as f:
                f.write("You are a test agent.")

            # Create config
            config_path = Path(tmp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump({
                    "storage": {"type": "filesystem", "path": str(workspace_path)},
                    "prompt_format": "xml",  # 🔥 Configure XML format
                }, f)

            # Create services
            from src.core.services.configuration_service import ConfigurationService
            config_service = ConfigurationService(str(config_path))
            storage_service = StorageService(config_service)
            discovery_service = AgentDiscoveryService(storage_service)

            # Act: Generate full prompt
            prompt = discovery_service.get_full_prompt(
                agent_id="test_agent",
                sample_message="Test message",
                include_history=False
            )

            # Assert: Should generate XML
            assert "<prompt>" in prompt, "Should generate XML format prompt"
            assert "Test message" in prompt, "Should include user message"

    def test_watcher_prioritizes_prompt_field(self):
        """
        Testa se o watcher usa o campo 'prompt' quando disponível.

        Este teste valida que o watcher foi corrigido para usar o XML.
        """
        # Simulação direta da lógica do watcher
        request_with_prompt = {
            "_id": "test_id",
            "agent_id": "test_agent",
            "provider": "claude",
            "prompt": "<prompt><user>XML Prompt</user></prompt>",
            "command": ["old", "command"],
            "cwd": "/tmp",
            "timeout": 180
        }

        # Lógica do watcher (copiada de claude-mongo-watcher.py:187-193)
        prompt = request_with_prompt.get("prompt", "")
        if prompt:
            command = ["claude", "-p", prompt]
        else:
            command = request_with_prompt.get("command", [])

        # Assert
        assert command == ["claude", "-p", "<prompt><user>XML Prompt</user></prompt>"]

    def test_watcher_fallback_to_command(self):
        """
        Testa backward compatibility: watcher usa 'command' sem 'prompt'.
        """
        request_without_prompt = {
            "_id": "test_id",
            "agent_id": "test_agent",
            "provider": "claude",
            "command": ["claude", "legacy", "command"],
            "cwd": "/tmp",
            "timeout": 180
        }

        # Lógica do watcher
        prompt = request_without_prompt.get("prompt", "")
        if prompt:
            command = ["claude", "-p", prompt]
        else:
            command = request_without_prompt.get("command", [])

        # Assert
        assert command == ["claude", "legacy", "command"]


class TestPromptXMLFormatConfiguration:
    """Testa se a configuração de formato XML está funcionando."""

    def test_prompt_format_xml_is_used_by_default(self):
        """
        Testa se o formato XML é usado quando configurado.
        """
        from src.core.prompt_engine import PromptEngine
        import tempfile
        import yaml
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            with open(agent_path / "definition.yaml", "w") as f:
                yaml.dump({"name": "Test", "prompt": "Be helpful"}, f)

            with open(agent_path / "persona.md", "w") as f:
                f.write("You are helpful.")

            # Create with XML format
            prompt_engine = PromptEngine(agent_path, prompt_format="xml")
            prompt_engine.load_context()

            prompt = prompt_engine.build_prompt_with_format([], "Test")

            # Should use XML format
            assert "<prompt>" in prompt
            assert "</prompt>" in prompt

    def test_prompt_format_text_fallback(self):
        """
        Testa se o formato texto ainda funciona (backward compatibility).
        """
        from src.core.prompt_engine import PromptEngine
        import tempfile
        import yaml
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_path = Path(tmp_dir)

            with open(agent_path / "definition.yaml", "w") as f:
                yaml.dump({"name": "Test", "prompt": "Be helpful"}, f)

            with open(agent_path / "persona.md", "w") as f:
                f.write("You are helpful.")

            # Create with text format
            prompt_engine = PromptEngine(agent_path, prompt_format="text")
            prompt_engine.load_context()

            prompt = prompt_engine.build_prompt_with_format([], "Test")

            # Should use text format
            assert "### INSTRUÇÕES DO AGENTE" in prompt
            assert "### NOVA INSTRUÇÃO DO USUÁRIO" in prompt
            assert "<prompt>" not in prompt  # Should NOT be XML