# tests/core/test_agent_executor.py
import pytest
from unittest.mock import MagicMock
from src.core.agent_executor import AgentExecutor
from src.core.domain import AgentDefinition, TaskDTO

@pytest.fixture
def mock_dependencies():
    """Fixture para fornecer dependências mockadas para o AgentExecutor."""
    mock_llm = MagicMock()
    mock_prompt_engine = MagicMock()
    mock_agent_def = AgentDefinition(
        name="Test Agent", 
        version="1.0", 
        schema_version="1.0",
        description="A test agent", 
        author="test",
        tags=[],
        capabilities=[],
        allowed_tools=[]
    )
    return {
        "llm_client": mock_llm,
        "prompt_engine": mock_prompt_engine,
        "agent_definition": mock_agent_def,
        "allowed_tools": {}
    }

def test_run_success_scenario(mock_dependencies):
    """Testa o fluxo de execução bem-sucedido de uma tarefa."""
    # Setup
    mock_dependencies["prompt_engine"].build_prompt.return_value = "Prompt final"
    mock_dependencies["llm_client"].invoke.return_value = "Resposta da IA"
    
    executor = AgentExecutor(**mock_dependencies)
    task = TaskDTO(agent_id="test_agent", user_input="Olá")
    
    # Execução
    result = executor.run(task)
    
    # Verificação
    mock_dependencies["prompt_engine"].build_prompt.assert_called_once_with(
        conversation_history=[], message="Olá"
    )
    mock_dependencies["llm_client"].invoke.assert_called_once_with("Prompt final")
    assert result.status == "success"
    assert result.output == "Resposta da IA"
    assert result.metadata["agent_id"] == "test_agent"

def test_run_llm_failure_scenario(mock_dependencies):
    """Testa o tratamento de erro quando o cliente LLM falha."""
    # Setup
    mock_dependencies["prompt_engine"].build_prompt.return_value = "Prompt final"
    mock_dependencies["llm_client"].invoke.side_effect = Exception("Falha na API")
    
    executor = AgentExecutor(**mock_dependencies)
    task = TaskDTO(agent_id="test_agent", user_input="Olá")
    
    # Execução
    result = executor.run(task)
    
    # Verificação
    assert result.status == "error"
    assert "Falha na API" in result.output