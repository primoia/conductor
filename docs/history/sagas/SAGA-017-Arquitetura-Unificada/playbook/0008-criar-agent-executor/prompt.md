# Especificação Técnica e Plano de Execução: 0008-criar-agent-executor

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa cria o componente de execução fundamental da nova arquitetura. Ao projetar o `AgentExecutor` para ser stateless, criamos um "worker" que é inerentemente escalável e pode ser instanciado por tarefa, pavimentando o caminho para execuções paralelas e a arquitetura de data plane que vislumbramos.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** A nova classe `AgentExecutor` **DEVE** ser localizada em um novo arquivo `src/core/agent_executor.py`.
- **Stateless:** A classe **NÃO DEVE** manter estado entre chamadas ao método `run`. Todo o contexto necessário para uma execução **DEVE** ser passado via `__init__` (para configuração de longo prazo) ou para o próprio método `run` (para dados da tarefa).
- **Injeção de Dependência:** O `AgentExecutor` **DEVE** receber suas dependências (como o cliente LLM e as ferramentas) através de seu construtor, seguindo o padrão de Injeção de Dependência.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `src/core/agent_executor.py`**
```python
# src/core/agent_executor.py
from typing import Dict, Callable, Any, List
from src.core.domain import TaskDTO, TaskResultDTO, AgentDefinition
# Supondo que um cliente LLM e um PromptEngine existam e serão injetados.
# Criaremos placeholders por enquanto.

class PlaceholderLLMClient:
    def invoke(self, prompt: str) -> str:
        return f"Resposta simulada para o prompt: {prompt[:50]}..."

class PlaceholderPromptEngine:
    def build_prompt(self, message: str) -> str:
        return f"Este é um prompt construído para: {message}"

class AgentExecutor:
    """
    Executa uma única tarefa para um agente, de forma stateless.
    Recebe todo o contexto necessário para operar, sem manter estado interno entre as execuções.
    """
    def __init__(
        self,
        agent_definition: AgentDefinition,
        llm_client: Any, # Usando Any para o placeholder
        prompt_engine: Any, # Usando Any para o placeholder
        allowed_tools: Dict[str, Callable[..., Any]]
    ):
        self._agent_definition = agent_definition
        self._llm_client = llm_client
        self._prompt_engine = prompt_engine
        self._allowed_tools = allowed_tools

    def run(self, task: TaskDTO) -> TaskResultDTO:
        """
        Executa o ciclo de vida de uma tarefa: constrói o prompt, invoca o LLM e retorna o resultado.
        """
        try:
            # Lógica de integração com PromptEngine virá no próximo estágio
            final_prompt = self._prompt_engine.build_prompt(task.user_input)

            # Invocar o LLM
            response = self._llm_client.invoke(final_prompt)

            return TaskResultDTO(
                status="success",
                output=response,
                metadata={"agent_id": self._agent_definition.agent_id}
            )
        except Exception as e:
            return TaskResultDTO(
                status="error",
                output=str(e),
                metadata={"agent_id": self._agent_definition.agent_id}
            )

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `src/core/agent_executor.py` for criado exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
