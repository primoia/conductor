# tests/test_mcp_integration.py
"""
Testes de integração para o sistema MCP (Model Context Protocol).
Verifica a geração de configuração MCP e o fluxo completo.
"""
import os
import sys
import json
import tempfile
import pytest

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPConfigGeneration:
    """Testes para geração de configuração MCP."""

    def test_mcp_ports_constant_exists(self):
        """Verifica que MCP_PORTS está definido no watcher."""
        from poc.container_to_host import claude_mongo_watcher as watcher_module

        # Importar o módulo do watcher (pode falhar se não estiver no path)
        assert hasattr(watcher_module, 'MCP_PORTS')
        assert isinstance(watcher_module.MCP_PORTS, dict)

        # Verificar portas padrão
        assert 'prospector' in watcher_module.MCP_PORTS
        assert 'database' in watcher_module.MCP_PORTS
        assert 'conductor' in watcher_module.MCP_PORTS

    def test_mcp_ports_values(self):
        """Verifica valores padrão das portas MCP."""
        from poc.container_to_host import claude_mongo_watcher as watcher_module

        # Portas padrão conforme definido
        assert watcher_module.MCP_PORTS['prospector'] == 5007
        assert watcher_module.MCP_PORTS['database'] == 5008
        assert watcher_module.MCP_PORTS['conductor'] == 5009

    def test_generate_mcp_config_empty(self):
        """Verifica que lista vazia retorna None."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        # Criar instância mock sem conexão real
        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        result = watcher.generate_mcp_config([])
        assert result is None

    def test_generate_mcp_config_single_mcp(self):
        """Verifica geração de config com um MCP."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        config_path = watcher.generate_mcp_config(["prospector"], host="localhost")

        assert config_path is not None
        assert os.path.exists(config_path)

        with open(config_path, 'r') as f:
            config = json.load(f)

        assert 'mcpServers' in config
        assert 'prospector' in config['mcpServers']
        assert config['mcpServers']['prospector']['url'] == 'http://localhost:5007/sse'

        # Cleanup
        os.unlink(config_path)

    def test_generate_mcp_config_multiple_mcps(self):
        """Verifica geração de config com múltiplos MCPs."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        config_path = watcher.generate_mcp_config(["prospector", "database"], host="localhost")

        assert config_path is not None

        with open(config_path, 'r') as f:
            config = json.load(f)

        assert len(config['mcpServers']) == 2
        assert 'prospector' in config['mcpServers']
        assert 'database' in config['mcpServers']
        assert config['mcpServers']['database']['url'] == 'http://localhost:5008/sse'

        # Cleanup
        os.unlink(config_path)

    def test_generate_mcp_config_invalid_mcp_ignored(self):
        """Verifica que MCPs inválidos são ignorados."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        config_path = watcher.generate_mcp_config(["prospector", "invalid_mcp"], host="localhost")

        assert config_path is not None

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Apenas prospector deve estar presente
        assert len(config['mcpServers']) == 1
        assert 'prospector' in config['mcpServers']
        assert 'invalid_mcp' not in config['mcpServers']

        # Cleanup
        os.unlink(config_path)

    def test_generate_mcp_config_custom_host(self):
        """Verifica geração com host customizado."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        config_path = watcher.generate_mcp_config(["prospector"], host="192.168.1.100")

        assert config_path is not None

        with open(config_path, 'r') as f:
            config = json.load(f)

        assert config['mcpServers']['prospector']['url'] == 'http://192.168.1.100:5007/sse'

        # Cleanup
        os.unlink(config_path)


class TestAgentDefinitionMCPConfigs:
    """Testes para mcp_configs no AgentDefinition."""

    def test_agent_definition_has_mcp_configs_field(self):
        """Verifica que AgentDefinition tem campo mcp_configs."""
        from src.core.domain import AgentDefinition

        # Criar definição com mcp_configs
        definition = AgentDefinition(
            name="test_agent",
            version="1.0.0",
            schema_version="1.0",
            description="Test agent",
            author="Test",
            mcp_configs=["prospector", "database"]
        )

        assert hasattr(definition, 'mcp_configs')
        assert definition.mcp_configs == ["prospector", "database"]

    def test_agent_definition_empty_mcp_configs(self):
        """Verifica que mcp_configs pode ser vazio."""
        from src.core.domain import AgentDefinition

        definition = AgentDefinition(
            name="test_agent",
            version="1.0.0",
            schema_version="1.0",
            description="Test agent",
            author="Test"
        )

        assert definition.mcp_configs == []

    def test_agent_definition_mcp_config_deprecated(self):
        """Verifica que mcp_config legado ainda funciona."""
        from src.core.domain import AgentDefinition

        definition = AgentDefinition(
            name="test_agent",
            version="1.0.0",
            schema_version="1.0",
            description="Test agent",
            author="Test",
            mcp_config="/path/to/config.json"
        )

        assert definition.mcp_config == "/path/to/config.json"


class TestCLIClientMCPConfigs:
    """Testes para passagem de mcp_configs no CLI client."""

    def test_create_llm_client_accepts_mcp_configs(self):
        """Verifica que create_llm_client aceita mcp_configs."""
        from src.infrastructure.llm.cli_client import create_llm_client

        # Criar cliente com mcp_configs
        client = create_llm_client(
            ai_provider="claude",
            working_directory="/tmp",
            mcp_configs=["prospector", "database"]
        )

        assert hasattr(client, 'mcp_configs')
        assert client.mcp_configs == ["prospector", "database"]

    def test_claude_cli_client_stores_mcp_configs(self):
        """Verifica que ClaudeCLIClient armazena mcp_configs."""
        from src.infrastructure.llm.cli_client import ClaudeCLIClient

        client = ClaudeCLIClient(
            working_directory="/tmp",
            mcp_configs=["prospector"]
        )

        assert client.mcp_configs == ["prospector"]


class TestAgentFieldsValidation:
    """Testes para validação de campos MCP em AgentFields."""

    def test_mcp_configs_in_valid_fields(self):
        """Verifica que mcp_configs está nos campos válidos."""
        from src.core.constants import AgentFields

        assert 'mcp_configs' in AgentFields.VALID_FIELDS
        assert 'mcp_config' in AgentFields.VALID_FIELDS  # legado


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
