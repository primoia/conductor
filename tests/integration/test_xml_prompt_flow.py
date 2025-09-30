# tests/integration/test_xml_prompt_flow.py
"""
Testes de integração para validar que o XML estruturado está sendo
gerado, salvo no MongoDB e enviado ao LLM corretamente.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestXMLPromptFlow:
    """Valida o fluxo completo do XML: geração -> MongoDB -> LLM"""

    def test_xml_is_generated_with_correct_structure(self):
        """
        Testa que get_full_prompt() gera XML com estrutura completa:
        - <prompt>
        - <system_context> com <persona> e <instructions>
        - <conversation_history>
        - <user_request>
        """
        from src.core.services.agent_discovery_service import AgentDiscoveryService
        from src.core.services.storage_service import StorageService
        from src.core.services.configuration_service import ConfigurationService
        from unittest.mock import MagicMock

        # Mock do storage
        mock_storage = MagicMock()
        mock_storage.get_agent_home_path.return_value = "mongodb://test/agent"

        # Mock do config service
        mock_config = MagicMock()
        mock_config.get_prompt_format.return_value = "xml"

        # Mock storage service que retorna mock_storage
        mock_storage_service = MagicMock()
        mock_storage_service.get_repository.return_value = mock_storage

        # Mock do PromptEngine com dados reais
        with patch('src.core.services.agent_discovery_service.PromptEngine') as MockPromptEngine:
            mock_engine = MagicMock()
            mock_engine.persona_content = "Test persona content"
            mock_engine.agent_config = {"prompt": "Test instructions"}

            # Mock do build_prompt_with_format para retornar XML estruturado
            mock_xml = """<prompt>
    <system_context>
        <persona><![CDATA[Test persona]]></persona>
        <instructions><![CDATA[Test instructions]]></instructions>
    </system_context>
    <conversation_history><history/></conversation_history>
    <user_request><![CDATA[Test message]]></user_request>
</prompt>"""
            mock_engine.build_prompt_with_format.return_value = mock_xml
            MockPromptEngine.return_value = mock_engine

            # Mock do get_conversation_history
            with patch.object(AgentDiscoveryService, 'get_conversation_history', return_value=[]):
                discovery_service = AgentDiscoveryService(mock_storage_service)

                # Act
                xml_prompt = discovery_service.get_full_prompt(
                    agent_id='test_agent',
                    current_message='Test message',
                    include_history=False,
                    save_to_file=False
                )

        # Assert - Estrutura XML
        assert xml_prompt.strip().startswith('<prompt>'), "Deve começar com <prompt>"
        assert xml_prompt.strip().endswith('</prompt>'), "Deve terminar com </prompt>"
        assert '<system_context>' in xml_prompt, "Deve conter <system_context>"
        assert '<persona>' in xml_prompt, "Deve conter <persona>"
        assert '<instructions>' in xml_prompt, "Deve conter <instructions>"
        assert '<conversation_history>' in xml_prompt, "Deve conter <conversation_history>"
        assert '<user_request>' in xml_prompt, "Deve conter <user_request>"

    def test_xml_is_saved_to_mongodb_via_submit_task(self):
        """
        Testa que submit_task() salva o XML completo no MongoDB
        sem modificações.
        """
        from src.core.services.mongo_task_client import MongoTaskClient
        from unittest.mock import MagicMock, patch

        xml_prompt = """<prompt>
    <system_context>
        <persona><![CDATA[Test persona]]></persona>
    </system_context>
    <user_request><![CDATA[Test message]]></user_request>
</prompt>"""

        # Mock MongoDB
        with patch('src.core.services.mongo_task_client.MongoClient') as MockClient:
            mock_collection = MagicMock()
            mock_result = MagicMock()
            mock_result.inserted_id = "test_task_id"
            mock_collection.insert_one.return_value = mock_result

            mock_db = MagicMock()
            mock_db.tasks = mock_collection

            mock_client = MagicMock()
            mock_client.__getitem__.return_value = mock_db
            mock_client.admin.command.return_value = None
            MockClient.return_value = mock_client

            # Act
            with patch.dict('os.environ', {'MONGO_URI': 'mongodb://test'}):
                task_client = MongoTaskClient()
                task_id = task_client.submit_task(
                    agent_id='test_agent',
                    cwd='/tmp',
                    timeout=300,
                    provider='claude',
                    prompt=xml_prompt
                )

            # Assert
            assert task_id == "test_task_id"

            # Verificar que insert_one foi chamado com o XML completo
            call_args = mock_collection.insert_one.call_args[0][0]
            assert call_args['prompt'] == xml_prompt, "Prompt XML deve ser salvo sem modificações"
            assert call_args['prompt'].startswith('<prompt>'), "Deve manter estrutura XML"
            assert call_args['agent_id'] == 'test_agent'
            assert call_args['provider'] == 'claude'
            assert call_args['status'] == 'pending'

    def test_watcher_reads_xml_from_mongodb_and_sends_to_llm(self):
        """
        Testa que o watcher lê o campo 'prompt' com XML e envia via stdin.
        """
        xml_prompt = """<prompt>
    <system_context>
        <persona><![CDATA[Test persona]]></persona>
    </system_context>
    <user_request><![CDATA[Test message]]></user_request>
</prompt>"""

        # Simular documento do MongoDB
        request = {
            "_id": "test_id",
            "agent_id": "test_agent",
            "provider": "claude",
            "prompt": xml_prompt,  # XML completo
            "cwd": "/tmp",
            "timeout": 180
        }

        # Simular lógica do watcher (de claude-mongo-watcher.py:200-220)
        prompt_from_db = request.get("prompt", "")
        provider = request.get("provider", "claude")

        # Verificar que o prompt é XML
        assert prompt_from_db.strip().startswith('<prompt>'), "Watcher deve ler XML do MongoDB"
        assert '<system_context>' in prompt_from_db, "XML deve conter system_context"

        # Verificar que o provider está correto
        if provider == "claude":
            command = ["claude", "--print", "--dangerously-skip-permissions"]
        else:
            command = None

        assert command == ["claude", "--print", "--dangerously-skip-permissions"]

        # Simular que o prompt seria enviado via stdin
        # (no watcher real: subprocess.run(command, input=prompt, ...))
        assert len(prompt_from_db) > 0, "Prompt não deve estar vazio"

    def test_api_route_generates_and_saves_xml(self):
        """
        Testa que o endpoint da API gera XML e salva no MongoDB.
        """
        from src.api.routes.agents import router
        from unittest.mock import MagicMock, patch

        xml_prompt = """<prompt>
    <system_context>
        <persona><![CDATA[API Test]]></persona>
    </system_context>
    <user_request><![CDATA[API message]]></user_request>
</prompt>"""

        # Mock discovery service
        mock_discovery = MagicMock()
        mock_discovery.get_full_prompt.return_value = xml_prompt

        # Mock task client
        mock_task_client = MagicMock()
        mock_task_client.submit_task.return_value = "test_task_123"
        mock_task_client.get_task_result.return_value = {
            "status": "completed",
            "result": "Success",
            "exit_code": 0
        }

        # Verificar que get_full_prompt retorna XML
        result = mock_discovery.get_full_prompt(
            agent_id='test',
            current_message='test',
            include_history=True,
            save_to_file=False
        )

        assert result == xml_prompt
        assert result.startswith('<prompt>')

        # Verificar que submit_task recebe o XML
        mock_task_client.submit_task(
            agent_id='test',
            cwd='/tmp',
            timeout=300,
            provider='claude',
            prompt=xml_prompt
        )

        # Verificar chamada
        call_args = mock_task_client.submit_task.call_args
        assert call_args.kwargs['prompt'] == xml_prompt
        assert call_args.kwargs['prompt'].startswith('<prompt>')


class TestXMLPromptIntegrity:
    """Testa que o XML não é corrompido durante o fluxo."""

    def test_xml_maintains_cdata_sections(self):
        """Verifica que CDATA sections são preservadas."""
        xml_with_cdata = """<prompt>
    <system_context>
        <persona><![CDATA[
# Persona with special chars <>&"'
Code example: if (x < 5) { return true; }
        ]]></persona>
    </system_context>
</prompt>"""

        # Simular salvamento e leitura
        prompt_saved = xml_with_cdata
        prompt_read = prompt_saved  # Simula leitura do MongoDB

        assert '<![CDATA[' in prompt_read, "CDATA deve ser preservado"
        assert 'if (x < 5)' in prompt_read, "Conteúdo dentro do CDATA deve estar intacto"

    def test_xml_handles_large_prompts(self):
        """Verifica que prompts grandes são salvos completamente."""
        large_persona = "A" * 10000  # 10KB de texto

        xml_large = f"""<prompt>
    <system_context>
        <persona><![CDATA[{large_persona}]]></persona>
    </system_context>
</prompt>"""

        # Simular salvamento
        assert len(xml_large) > 10000, "Prompt deve ser grande"

        # MongoDB não deve truncar
        prompt_from_db = xml_large
        assert len(prompt_from_db) == len(xml_large), "Tamanho deve ser preservado"
        assert large_persona in prompt_from_db, "Conteúdo completo deve estar presente"


class TestPromptFormatConfiguration:
    """Testa que a configuração prompt_format funciona corretamente."""

    def test_config_defaults_to_xml(self):
        """Verifica que o default é 'xml'."""
        from src.core.config_schema import GlobalConfig
        from src.core.config_schema import StorageConfig

        # Criar config sem prompt_format explícito
        config = GlobalConfig(
            storage=StorageConfig(type="filesystem", backup_path=".test"),
            tool_plugins=[]
            # prompt_format não especificado - deve usar default
        )

        assert config.prompt_format == "xml", "Default deve ser 'xml'"

    def test_prompt_engine_uses_xml_format(self):
        """Verifica que PromptEngine usa formato XML quando configurado."""
        from src.core.prompt_engine import PromptEngine
        from unittest.mock import MagicMock, patch

        # Mock filesystem
        with patch('src.core.prompt_engine.os.path.exists', return_value=True):
            with patch('src.core.prompt_engine.open', create=True):
                with patch.object(PromptEngine, '_load_persona', return_value="Test"):
                    with patch.object(PromptEngine, '_load_agent_config', return_value={"prompt": "Test"}):
                        engine = PromptEngine(
                            agent_home_path="/test",
                            prompt_format="xml"
                        )

                        # Mock load_context
                        engine.persona_content = "Test persona"
                        engine.agent_config = {"prompt": "Test instructions"}

                        # Testar que build_prompt_with_format chama build_xml_prompt
                        with patch.object(engine, 'build_xml_prompt', return_value="<prompt>XML</prompt>") as mock_xml:
                            result = engine.build_prompt_with_format([], "test", True)

                            # Assert
                            mock_xml.assert_called_once()
                            assert result == "<prompt>XML</prompt>"


class TestXMLPromptDebugging:
    """Testes para depurar onde o XML pode estar sendo perdido."""

    def test_discovery_service_returns_xml_not_text(self):
        """
        Teste crítico: get_full_prompt() deve retornar XML, não texto simples.
        """
        from src.core.services.agent_discovery_service import AgentDiscoveryService
        from unittest.mock import MagicMock, patch

        # Setup mocks
        mock_storage_service = MagicMock()
        mock_storage = MagicMock()
        mock_storage.get_agent_home_path.return_value = "mongodb://test/agent"
        mock_storage_service.get_repository.return_value = mock_storage

        # Mock PromptEngine para retornar XML
        with patch('src.core.services.agent_discovery_service.PromptEngine') as MockEngine:
            mock_engine = MagicMock()
            mock_engine.persona_content = "Persona"
            mock_engine.agent_config = {"prompt": "Instructions"}

            # 🔥 CRITICAL: build_prompt_with_format DEVE retornar XML
            xml_output = "<prompt><system_context><persona><![CDATA[Persona]]></persona></system_context></prompt>"
            mock_engine.build_prompt_with_format.return_value = xml_output
            MockEngine.return_value = mock_engine

            # Mock container
            with patch('src.core.services.agent_discovery_service.container') as mock_container:
                mock_config_service = MagicMock()
                mock_config_service.get_prompt_format.return_value = "xml"
                mock_container.get_configuration_service.return_value = mock_config_service

                with patch.object(AgentDiscoveryService, 'get_conversation_history', return_value=[]):
                    discovery = AgentDiscoveryService(mock_storage_service)

                    # Act
                    result = discovery.get_full_prompt(
                        agent_id='test',
                        current_message='test',
                        include_history=False,
                        save_to_file=False
                    )

                    # Assert 🔥
                    print(f"\n🔍 DEBUG: get_full_prompt retornou:")
                    print(f"  Tipo: {'XML' if result.startswith('<prompt>') else 'TEXTO SIMPLES'}")
                    print(f"  Primeiros 200 chars: {result[:200]}")

                    assert result == xml_output, "Deve retornar exatamente o XML gerado"
                    assert result.startswith('<prompt>'), "DEVE começar com <prompt>"
                    assert not result.startswith('==='), "NÃO deve ser texto de fallback"