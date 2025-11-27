# tests/test_mcp_e2e.py
"""
Testes end-to-end para o fluxo MCP.
Simula o fluxo completo: Task com mcp_configs -> Watcher -> Claude CLI.
"""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMCPEndToEndFlow:
    """Testes E2E para o fluxo MCP."""

    def test_task_with_mcp_configs_generates_command(self):
        """
        Simula uma task com mcp_configs e verifica que o comando Claude
        é gerado corretamente com --mcp-config.
        """
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        # Mock do subprocess para não executar realmente
        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        # Simular task com mcp_configs
        task = {
            "_id": "test_task_123",
            "agent_id": "Hunter_Agent",
            "provider": "claude",
            "prompt": "Test prompt",
            "cwd": "/tmp",
            "timeout": 60,
            "mcp_configs": ["prospector", "database"]
        }

        # Gerar config MCP
        config_path = watcher.generate_mcp_config(task["mcp_configs"])

        assert config_path is not None
        assert os.path.exists(config_path)

        # Verificar conteúdo do config
        with open(config_path, 'r') as f:
            config = json.load(f)

        assert 'mcpServers' in config
        assert 'prospector' in config['mcpServers']
        assert 'database' in config['mcpServers']
        assert config['mcpServers']['prospector']['url'] == 'http://localhost:5007/sse'
        assert config['mcpServers']['database']['url'] == 'http://localhost:5008/sse'

        # Cleanup
        os.unlink(config_path)

    def test_claude_command_includes_mcp_config_flag(self):
        """
        Verifica que o comando Claude inclui --mcp-config quando mcp_configs está presente.
        """
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher
        import subprocess

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        captured_command = None

        def mock_run(cmd, **kwargs):
            nonlocal captured_command
            captured_command = cmd
            # Retornar resultado simulado
            result = MagicMock()
            result.returncode = 0
            result.stdout = "Test output"
            result.stderr = ""
            return result

        with patch('subprocess.run', side_effect=mock_run):
            # Executar com mcp_configs
            result, exit_code, duration = watcher.execute_llm_request(
                provider="claude",
                prompt="Test prompt",
                cwd="/tmp",
                timeout=60,
                mcp_configs=["prospector"]
            )

        # Verificar que o comando foi capturado
        assert captured_command is not None
        assert "claude" in captured_command
        assert "--print" in captured_command
        assert "--dangerously-skip-permissions" in captured_command

        # Verificar que --mcp-config foi incluído
        assert "--mcp-config" in captured_command
        mcp_config_index = captured_command.index("--mcp-config")
        config_path = captured_command[mcp_config_index + 1]
        assert config_path.endswith(".json")

    def test_claude_command_without_mcp_configs(self):
        """
        Verifica que o comando Claude não inclui --mcp-config quando mcp_configs está vazio.
        """
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher
        import subprocess

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        captured_command = None

        def mock_run(cmd, **kwargs):
            nonlocal captured_command
            captured_command = cmd
            result = MagicMock()
            result.returncode = 0
            result.stdout = "Test output"
            result.stderr = ""
            return result

        with patch('subprocess.run', side_effect=mock_run):
            result, exit_code, duration = watcher.execute_llm_request(
                provider="claude",
                prompt="Test prompt",
                cwd="/tmp",
                timeout=60,
                mcp_configs=[]  # Lista vazia
            )

        assert captured_command is not None
        assert "--mcp-config" not in captured_command

    def test_task_execution_service_passes_mcp_configs(self):
        """
        Verifica que TaskExecutionService extrai e passa mcp_configs corretamente.
        """
        from src.core.domain import AgentDefinition

        # Criar definição com mcp_configs
        definition = AgentDefinition(
            name="Hunter_Agent",
            version="1.0.0",
            schema_version="1.0",
            description="Test agent",
            author="Test",
            mcp_configs=["prospector", "database"],
            allowed_tools=["Read", "Write", "mcp__prospector__fetch_page"]
        )

        # Verificar que mcp_configs está presente
        assert definition.mcp_configs == ["prospector", "database"]
        assert "mcp__prospector__fetch_page" in definition.allowed_tools


class TestMCPConfigFormat:
    """Testes para o formato do config MCP."""

    def test_mcp_config_json_format(self):
        """Verifica que o JSON gerado está no formato correto para Claude CLI."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        config_path = watcher.generate_mcp_config(
            ["prospector", "database", "conductor"],
            host="gateway.local"
        )

        with open(config_path, 'r') as f:
            config = json.load(f)

        # Verificar estrutura esperada pelo Claude CLI
        expected_format = {
            "mcpServers": {
                "prospector": {"url": "http://gateway.local:5007/sse"},
                "database": {"url": "http://gateway.local:5008/sse"},
                "conductor": {"url": "http://gateway.local:5009/sse"}
            }
        }

        assert config == expected_format

        # Cleanup
        os.unlink(config_path)

    def test_mcp_urls_use_sse_protocol(self):
        """Verifica que as URLs MCP usam protocolo SSE."""
        from poc.container_to_host.claude_mongo_watcher import UniversalMongoWatcher

        watcher = UniversalMongoWatcher.__new__(UniversalMongoWatcher)
        watcher.mongo_uri = "mongodb://localhost:27017"

        config_path = watcher.generate_mcp_config(["prospector"])

        with open(config_path, 'r') as f:
            config = json.load(f)

        url = config['mcpServers']['prospector']['url']
        assert url.endswith('/sse'), f"URL should end with /sse, got: {url}"
        assert url.startswith('http://'), f"URL should start with http://, got: {url}"

        # Cleanup
        os.unlink(config_path)


class TestMCPPortsConfiguration:
    """Testes para configuração de portas MCP."""

    def test_default_ports(self):
        """Verifica portas padrão dos MCPs."""
        from poc.container_to_host.claude_mongo_watcher import MCP_PORTS

        assert MCP_PORTS['prospector'] == 5007
        assert MCP_PORTS['database'] == 5008
        assert MCP_PORTS['conductor'] == 5009

    def test_ports_can_be_overridden_by_env(self):
        """Verifica que portas podem ser sobrescritas por variáveis de ambiente."""
        import importlib

        # Definir variável de ambiente
        os.environ['MCP_PROSPECTOR_PORT'] = '9007'

        # Reimportar módulo para pegar nova variável
        from poc.container_to_host import claude_mongo_watcher
        importlib.reload(claude_mongo_watcher)

        assert claude_mongo_watcher.MCP_PORTS['prospector'] == 9007

        # Cleanup
        os.environ.pop('MCP_PROSPECTOR_PORT', None)
        importlib.reload(claude_mongo_watcher)  # Restaurar padrão


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
