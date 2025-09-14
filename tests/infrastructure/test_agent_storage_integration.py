# tests/infrastructure/test_agent_storage_integration.py
import pytest
import tempfile
import os
from pathlib import Path

from src.core.domain import AgentDefinition, AgentPersona
from src.infrastructure.filesystem_storage import FileSystemStorage
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository


class TestAgentStorageIntegration:
    """
    Testa a integração entre as camadas Storage e Repository.
    """

    def test_filesystem_storage_uses_repository_correctly(self):
        """Testa se FileSystemStorage usa FileSystemStateRepository corretamente."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileSystemStorage(base_path)

            # Criar AgentDefinition de teste
            definition = AgentDefinition(
                name="TestAgent",
                version="1.0.0",
                schema_version="1.0",
                description="Agent for testing",
                author="Test Author",
                tags=["test"],
                capabilities=["testing"],
                allowed_tools=["test_tool"]
            )

            # Act
            # Salvar através do Storage (alto nível)
            storage.save_definition("test_agent", definition)

            # Verificar se foi salvo corretamente no Repository (baixo nível)
            repository = FileSystemStateRepository(str(base_path))
            saved_data = repository.load_definition("test_agent")

            # Assert
            assert saved_data["name"] == "TestAgent"
            assert saved_data["version"] == "1.0.0"
            assert saved_data["tags"] == ["test"]

            # Carregar através do Storage e verificar se retorna objeto de domínio
            loaded_definition = storage.load_definition("test_agent")
            assert isinstance(loaded_definition, AgentDefinition)
            assert loaded_definition.name == "TestAgent"
            assert loaded_definition.version == "1.0.0"

    def test_filesystem_persona_integration(self):
        """Testa integração para persona."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileSystemStorage(base_path)

            persona = AgentPersona(content="Test persona content")

            # Act
            storage.save_persona("test_agent", persona)

            # Verificar no repository
            repository = FileSystemStateRepository(str(base_path))
            saved_content = repository.load_persona("test_agent")

            # Assert
            assert saved_content == "Test persona content"

            # Carregar através do Storage
            loaded_persona = storage.load_persona("test_agent")
            assert isinstance(loaded_persona, AgentPersona)
            assert loaded_persona.content == "Test persona content"

    def test_list_agents_works_across_layers(self):
        """Testa se list_agents funciona corretamente entre as camadas."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileSystemStorage(base_path)
            repository = FileSystemStateRepository(str(base_path))

            # Criar alguns agentes através do repository
            repository.save_definition("agent1", {"name": "Agent1", "version": "1.0"})
            repository.save_definition("agent2", {"name": "Agent2", "version": "1.0"})

            # Act
            agents_from_storage = storage.list_agents()
            agents_from_repository = repository.list_agents()

            # Assert
            assert sorted(agents_from_storage) == sorted(agents_from_repository)
            assert "agent1" in agents_from_storage
            assert "agent2" in agents_from_storage

    def test_storage_handles_missing_data_gracefully(self):
        """Testa se Storage lida graciosamente com dados ausentes."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            storage = FileSystemStorage(base_path)

            # Act & Assert
            with pytest.raises(FileNotFoundError):
                storage.load_definition("nonexistent_agent")

            with pytest.raises(FileNotFoundError):
                storage.load_persona("nonexistent_agent")