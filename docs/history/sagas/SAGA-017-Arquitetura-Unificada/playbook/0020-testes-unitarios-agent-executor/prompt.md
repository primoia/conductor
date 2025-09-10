# Especificação Técnica e Plano de Execução: 0020-testes-unitarios-agent-executor

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa garante a confiabilidade do nosso "worker" de execução. Ao testar o `AgentExecutor` de forma isolada, validamos que a orquestração interna de uma tarefa (construção de prompt, chamada ao LLM, tratamento de resultado) está correta, independentemente do comportamento das suas dependências. Isso é crucial para a estabilidade de todas as execuções de agentes.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** Os testes **DEVEM** ser criados em um novo arquivo `tests/core/test_agent_executor.py`.
- **Framework:** Os testes **DEVEM** usar `pytest` e `unittest.mock`.
- **Isolamento:** As dependências do `AgentExecutor` (`PromptEngine`, `LLMClient`) **DEVEM** ser completamente mockadas para focar o teste na lógica de orquestração do executor.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** representar a estrutura e os principais casos de teste a serem implementados.

**Arquivo 1 (Novo): `tests/core/test_agent_executor.py`**
```python
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
        agent_id="test_agent", name="Test Agent", version="1.0", description="A test agent"
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
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `tests/core/test_agent_executor.py` for criado com uma estrutura de testes robusta que cubra os cenários de sucesso e falha do `AgentExecutor` usando mocks.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
