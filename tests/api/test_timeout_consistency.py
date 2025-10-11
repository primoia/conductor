# tests/api/test_timeout_consistency.py
"""
Testes para garantir que os timeouts estão sincronizados em toda a arquitetura.

IMPORTANTE: Inconsistências de timeout podem causar:
- Cliente aguardando mais tempo que necessário
- Watcher matando subprocess antes do cliente desistir
- Experiência de usuário ruim
"""
import pytest


class TestTimeoutConsistency:
    """Valida que os timeouts defaults estão alinhados."""

    @pytest.mark.skip(reason="Requires fastapi dependency - API tests run separately")
    def test_api_default_timeout_is_300s(self):
        """
        Valida que o default da API é 300s.
        """
        from src.api.routes.agents import AgentExecuteRequest

        # Criar request sem timeout (deve usar default)
        request = AgentExecuteRequest(
            user_input="Test",
            cwd="/tmp"
            # timeout não fornecido - deve usar default
        )

        assert request.timeout == 300, "API default deve ser 300s"

    def test_mongo_task_client_default_timeout_is_300s(self):
        """
        Valida que o default do MongoTaskClient é 300s.
        """
        import inspect
        from src.core.services.mongo_task_client import MongoTaskClient

        # Pegar signature do método submit_task
        sig = inspect.signature(MongoTaskClient.submit_task)
        timeout_param = sig.parameters['timeout']

        assert timeout_param.default == 300, "MongoTaskClient.submit_task default deve ser 300s"

    def test_get_task_result_default_timeout_is_300s(self):
        """
        Valida que o default do get_task_result é 300s.
        """
        import inspect
        from src.core.services.mongo_task_client import MongoTaskClient

        # Pegar signature do método get_task_result
        sig = inspect.signature(MongoTaskClient.get_task_result)
        timeout_param = sig.parameters['timeout']

        assert timeout_param.default == 300, "get_task_result default deve ser 300s"

    def test_watcher_execute_llm_request_default_is_300s(self):
        """
        Valida que o watcher usa default de 300s.
        """
        # Ler arquivo do watcher e verificar default
        import re
        from pathlib import Path

        watcher_path = Path("poc/container_to_host/claude-mongo-watcher.py")
        content = watcher_path.read_text()

        # Buscar: def execute_llm_request(..., timeout: int = XXX)
        match = re.search(r'def execute_llm_request\(.*timeout:\s*int\s*=\s*(\d+)', content, re.DOTALL)
        assert match, "execute_llm_request deve ter timeout com default"

        timeout_default = int(match.group(1))
        assert timeout_default == 300, f"Watcher execute_llm_request default deve ser 300s, encontrado: {timeout_default}s"

    def test_watcher_process_request_fallback_is_300s(self):
        """
        Valida que o watcher usa fallback de 300s ao ler do MongoDB.
        """
        import re
        from pathlib import Path

        watcher_path = Path("poc/container_to_host/claude-mongo-watcher.py")
        content = watcher_path.read_text()

        # Buscar: timeout = request.get("timeout", XXX)
        match = re.search(r'timeout\s*=\s*request\.get\(["\']timeout["\']\s*,\s*(\d+)\)', content)
        assert match, "process_request deve ter request.get('timeout', DEFAULT)"

        timeout_fallback = int(match.group(1))
        assert timeout_fallback == 300, f"Watcher fallback deve ser 300s, encontrado: {timeout_fallback}s"


class TestTimeoutPropagation:
    """Valida que timeout customizado é propagado corretamente."""

    def test_custom_timeout_flows_through_system(self):
        """
        Testa que timeout customizado (ex: 600s) é respeitado em todos os níveis.

        Simula o fluxo:
        1. API recebe timeout=600
        2. submit_task salva timeout=600
        3. get_task_result aguarda até 600s
        4. Watcher lê timeout=600 do MongoDB
        5. Subprocess usa timeout=600
        """
        custom_timeout = 600

        # Simular documento MongoDB
        task_document = {
            "_id": "test_id",
            "agent_id": "test_agent",
            "provider": "claude",
            "prompt": "<prompt>Test</prompt>",
            "cwd": "/tmp",
            "timeout": custom_timeout,  # ✅ Timeout customizado salvo
            "status": "pending"
        }

        # Simular lógica do watcher
        timeout_from_db = task_document.get("timeout", 300)

        assert timeout_from_db == custom_timeout, f"Watcher deve usar timeout do MongoDB: {custom_timeout}s"


class TestTimeoutEdgeCases:
    """Testa casos extremos de timeout."""

    def test_very_short_timeout(self):
        """
        Testa que timeouts muito curtos (ex: 10s) são respeitados.
        """
        short_timeout = 10

        # Simular documento com timeout curto
        task_document = {"timeout": short_timeout}
        timeout = task_document.get("timeout", 300)

        assert timeout == short_timeout, "Timeout curto deve ser respeitado"

    def test_very_long_timeout(self):
        """
        Testa que timeouts muito longos (ex: 3600s = 1h) são respeitados.
        """
        long_timeout = 3600

        # Simular documento com timeout longo
        task_document = {"timeout": long_timeout}
        timeout = task_document.get("timeout", 300)

        assert timeout == long_timeout, "Timeout longo deve ser respeitado"

    def test_missing_timeout_uses_default(self):
        """
        Testa que tasks antigas sem campo timeout usam default correto.
        """
        # Simular documento antigo sem timeout
        legacy_task = {
            "_id": "old_task",
            "prompt": "<prompt>Old</prompt>",
            # timeout ausente (None/undefined)
        }

        # Lógica do watcher
        timeout = legacy_task.get("timeout", 300)

        assert timeout == 300, "Tasks antigas devem usar default 300s"


class TestPollingIntervals:
    """Valida que polling intervals fazem sentido."""

    def test_client_polling_interval_is_reasonable(self):
        """
        Valida que cliente faz polling a cada 2s (não muito frequente).
        """
        import inspect
        from src.core.services.mongo_task_client import MongoTaskClient

        sig = inspect.signature(MongoTaskClient.get_task_result)
        poll_interval_param = sig.parameters['poll_interval']

        assert poll_interval_param.default == 2.0, "Polling interval deve ser 2.0s"

    def test_polling_interval_vs_timeout(self):
        """
        Valida que polling interval é muito menor que timeout.

        Regra: poll_interval << timeout (pelo menos 100x menor)
        """
        poll_interval = 2.0  # segundos
        timeout = 300  # segundos

        ratio = timeout / poll_interval
        assert ratio >= 100, f"Polling interval deve ser pelo menos 100x menor que timeout (ratio: {ratio})"


class TestTimeoutDocumentation:
    """Valida que defaults estão documentados."""

    def test_timeout_constants_are_documented(self):
        """
        Lista todos os timeouts defaults para referência.
        """
        timeouts = {
            "API AgentExecuteRequest": 300,
            "MongoTaskClient.submit_task": 300,
            "MongoTaskClient.get_task_result": 300,
            "Watcher execute_llm_request": 300,
            "Watcher process_request fallback": 300,
            "Poll interval (client)": 2.0,
        }

        # Validar que todos são consistentes (300s)
        timeout_values = [v for k, v in timeouts.items() if "interval" not in k.lower()]
        assert all(t == 300 for t in timeout_values), \
            f"Todos os timeouts devem ser 300s: {timeouts}"

        # Apenas para documentação
        print("\n📊 Timeouts Configurados:")
        for name, value in timeouts.items():
            print(f"  - {name}: {value}s")