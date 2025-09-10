# Especificação Técnica e Plano de Execução: 0019-testes-unitarios-conductor-service

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa constrói a principal rede de segurança de regressão para o núcleo da aplicação. Testes unitários robustos garantem a estabilidade do `ConductorService`, permitindo futuras refatorações com a confiança de que o comportamento fundamental do sistema está protegido e verificado.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** Os testes **DEVEM** ser criados em um novo arquivo `tests/core/test_conductor_service.py`.
- **Framework:** Os testes **DEVEM** usar `pytest` e `unittest.mock`.
- **Isolamento:** Os testes **DEVEM** ser testes unitários puros. Todas as dependências externas (sistema de arquivos, repositórios, etc.) **DEVEM** ser mockadas para que o teste se concentre exclusivamente na lógica do `ConductorService`.
- **Cobertura:** O objetivo é atingir uma cobertura de teste superior a 90% para o arquivo `src/core/conductor_service.py`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** representar a estrutura e os principais casos de teste a serem implementados.

**Arquivo 1 (Novo): `tests/core/test_conductor_service.py`**
```python
# tests/core/test_conductor_service.py
import pytest
from unittest.mock import patch, MagicMock
from src.core.conductor_service import ConductorService
from src.core.exceptions import ConfigurationError

# Exemplo de teste para o carregador de configuração
@patch('builtins.open')
@patch('yaml.safe_load')
def test_load_config_success(mock_safe_load, mock_open):
    """Testa o carregamento de configuração bem-sucedido."""
    mock_config = {
        "storage": {"type": "filesystem", "path": "/tmp/ws"},
        "tool_plugins": ["/plugins"]
    }
    mock_safe_load.return_value = mock_config
    service = ConductorService()
    assert service._config.storage.type == "filesystem"
    mock_open.assert_called_with("config.yaml", 'r')

def test_load_config_not_found():
    """Testa o erro quando o config.yaml não é encontrado."""
    with pytest.raises(ConfigurationError, match="não encontrado"):
        ConductorService(config_path="non_existent_file.yaml")

# Exemplo de teste para a StorageFactory
def test_storage_factory_filesystem():
    """Testa a criação do repositório de filesystem."""
    # Mockando o _load_and_validate_config para isolar a factory
    with patch.object(ConductorService, '_load_and_validate_config') as mock_load:
        mock_config = MagicMock()
        mock_config.storage.type = "filesystem"
        mock_load.return_value = mock_config
        
        service = ConductorService()
        from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
        assert isinstance(service.repository, FileSystemStateRepository)

# Exemplo de teste para a descoberta de agentes
def test_discover_agents():
    """Testa a orquestração da descoberta de agentes."""
    with patch.object(ConductorService, '_load_and_validate_config'):
        service = ConductorService()
        
        # Mockar o repositório
        mock_repo = MagicMock()
        mock_repo.list_agents.return_value = ["agent1"]
        mock_repo.load_state.return_value = {
            "definition": {"agent_id": "agent1", "name": "Test Agent", "version": "1.0", "description": ""}
        }
        service.repository = mock_repo
        
        agents = service.discover_agents()
        assert len(agents) == 1
        assert agents[0].name == "Test Agent"
        mock_repo.list_agents.assert_called_once()
        mock_repo.load_state.assert_called_with("agent1")

# ... (outros testes para load_tools, execute_task, etc.) ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `tests/core/test_conductor_service.py` for criado com uma estrutura de testes robusta que cubra os principais cenários de lógica do `ConductorService` usando mocks.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
