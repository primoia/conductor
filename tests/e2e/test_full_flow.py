# tests/e2e/test_full_flow.py
import pytest
import yaml
import json
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
    # O FileSystemStateRepository espera arquivos .json diretamente no subdiretório 'agents'
    agents_dir = workspace_path / "agents"
    agents_dir.mkdir(parents=True)
    
    # Criar diretório específico do agente para agent.yaml e persona.md
    fs_agent_dir = agents_dir / "fs_agent"
    fs_agent_dir.mkdir(parents=True)
    
    # Criar agent.yaml para o PromptEngine
    with open(fs_agent_dir / "agent.yaml", "w") as f:
        yaml.dump({
            "name": "FS Agent", 
            "version": "1.0", 
            "schema_version": "1.0",
            "description": "A test agent for filesystem flow", 
            "author": "test",
            "tags": [],
            "capabilities": [],
            "allowed_tools": []
        }, f)
    
    # Criar persona.md para o PromptEngine
    with open(fs_agent_dir / "persona.md", "w") as f:
        f.write("You are a helpful test agent for filesystem operations.")
    
    # Conteúdo do agente mock no formato JSON para o FileSystemStateRepository
    agent_content = {
        "definition": {
            "name": "FS Agent", 
            "version": "1.0", 
            "schema_version": "1.0",
            "description": "A test agent for filesystem flow", 
            "author": "test",
            "tags": [],
            "capabilities": [],
            "allowed_tools": []
        },
        "agent_home_path": str(fs_agent_dir.resolve()), # Caminho para o diretório do agente
        "allowed_tools": []
    }
    
    # Salvar como arquivo JSON para o FileSystemStateRepository
    with open(agents_dir / "fs_agent.json", "w") as f:
        json.dump(agent_content, f, indent=2)

    return ConductorService(config_path=str(config_path))

# Mockando o LLM para todos os testes neste arquivo
@patch('src.core.conductor_service.PlaceholderLLMClient')
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