# Especificação Técnica e Plano de Execução: 0021-testes-integracao-novo-fluxo

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa valida que os componentes individuais da nova arquitetura (serviço, repositório, executor) se integram e funcionam corretamente em conjunto. Testes de integração são cruciais para detectar problemas na "fiação" entre as camadas e garantir que o sistema como um todo se comporta como esperado em cenários realistas.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** Os testes **DEVEM** ser criados em `tests/e2e/test_full_flow.py`.
- **Ambiente Real:** Os testes **DEVEM** interagir com implementações reais dos repositórios (`FileSystemStateRepository` e `MongoStateRepository`). O ambiente `docker-compose` deve ser usado para o `mongodb`.
- **Mocking Mínimo:** Apenas dependências externas, como o cliente LLM, **DEVEM** ser mockadas. O fluxo interno do `ConductorService` e sua interação com o repositório **NÃO DEVEM** ser mockados.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** representar a estrutura e os principais casos de teste a serem implementados.

**Arquivo 1 (Novo): `tests/e2e/test_full_flow.py`**
```python
# tests/e2e/test_full_flow.py
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch
from src.core.conductor_service import ConductorService
from src.core.domain import TaskDTO

# Simula um config.yaml para o teste de filesystem
FILESYSTEM_CONFIG = {
    "storage": {"type": "filesystem", "path": "./.test_workspace"},
    "tool_plugins": []
}

@pytest.fixture
def filesystem_service(tmp_path):
    """Fixture para criar um ConductorService com backend de filesystem."""
    # Criar config e workspace de teste
    config_path = tmp_path / "config.yaml"
    workspace_path = tmp_path / ".test_workspace"
    workspace_path.mkdir()
    
    FILESYSTEM_CONFIG["storage"]["path"] = str(workspace_path)
    with open(config_path, "w") as f:
        yaml.dump(FILESYSTEM_CONFIG, f)

    # Criar um agente mock no workspace
    agent_dir = workspace_path / "agents" / "fs_agent"
    agent_dir.mkdir(parents=True)
    with open(agent_dir / "agent.yaml", "w") as f:
        # Simplificando a estrutura do estado para o teste
        yaml.dump({"definition": {"agent_id": "fs_agent", "name": "FS Agent", "version": "1.0", "description": ""}}, f)

    return ConductorService(config_path=str(config_path))

# Mockando o LLM para todos os testes neste arquivo
@patch('src.core.agent_executor.PlaceholderLLMClient')
def test_filesystem_flow(MockLLMClient, filesystem_service):
    """Testa o fluxo completo com o backend de filesystem."""
    # Setup mock do LLM
    mock_llm_instance = MockLLMClient.return_value
    mock_llm_instance.invoke.return_value = "Resposta do FS"

    # 1. Testar Descoberta
    agents = filesystem_service.discover_agents()
    assert len(agents) == 1
    assert agents[0].agent_id == "fs_agent"

    # 2. Testar Execução
    task = TaskDTO(agent_id="fs_agent", user_input="Olá")
    result = filesystem_service.execute_task(task)
    
    assert result.status == "success"
    assert result.output == "Resposta do FS"

# Testes para MongoDB seriam similares, mas exigiriam uma fixture
# para se conectar ao DB do docker-compose, inserir dados e limpar.
# Ex: @pytest.mark.usefixtures("docker_services")
def test_mongodb_flow_placeholder():
    """Placeholder para o teste de integração com MongoDB."""
    pytest.skip("Teste de MongoDB a ser implementado com fixture de DB.")

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `tests/e2e/test_full_flow.py` for criado com um teste de integração funcional para o backend de filesystem, demonstrando o padrão a ser seguido para outros backends.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
