# Especificação Técnica e Plano de Execução: 0009-integrar-prompt-engine

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa garante que a nova arquitetura de execução aproveite a lógica de engenharia de prompt existente e testada do `PromptEngine`. Isso mantém a qualidade e a consistência do comportamento dos agentes, ao mesmo tempo que encapsula essa lógica complexa dentro do nosso novo worker stateless, o `AgentExecutor`.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Reutilização:** O `PromptEngine` existente em `src/core/prompt_engine.py` **DEVE** ser reutilizado.
- **Adaptação para Stateless:** O `PromptEngine` **DEVE** ser ligeiramente modificado para ser instanciado com um caminho de agente (`agent_home_path`) em seu construtor, em vez de descobri-lo.
- **Injeção de Dependência:** O `AgentExecutor` **NÃO DEVE** instanciar o `PromptEngine` diretamente. Ele **DEVE** receber uma instância do `PromptEngine` em seu construtor, para manter o desacoplamento e a testabilidade.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar dois arquivos existentes. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Modificar): `src/core/prompt_engine.py`**
```python
# src/core/prompt_engine.py
# (Preservar os imports existentes)
import os
import yaml
from typing import Dict, Any, List

class PromptEngine:
    # ... (manter o conteúdo existente, mas modificar o __init__ e load_context)

    def __init__(self, agent_home_path: str):
        """
        Inicializa o PromptEngine com o caminho para o diretório principal do agente.
        """
        self.agent_home_path = agent_home_path
        self.agent_config: Dict[str, Any] = {}
        self.persona_content: str = ""
        self.playbook: Dict[str, Any] = {}
        self.load_context() # Carrega o contexto na inicialização

    def load_context(self):
        """Carrega todos os artefatos de contexto do agente."""
        # Carregar agent.yaml
        config_path = os.path.join(self.agent_home_path, "agent.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.agent_config = yaml.safe_load(f)

        # Carregar persona.md
        persona_path = os.path.join(self.agent_home_path, "persona.md")
        if os.path.exists(persona_path):
            with open(persona_path, "r") as f:
                self.persona_content = f.read()

        # (Manter o resto da lógica de load_context, se houver)

    def build_prompt(self, conversation_history: List[Dict], message: str) -> str:
        # (A lógica de construção do prompt permanece a mesma, esta é apenas uma assinatura de exemplo)
        # Esta lógica será refinada, mas por enquanto, fazemos uma construção simples.
        system_prompt = f"PERSONA:\n{self.persona_content}\n\nHISTORY:\n{conversation_history}"
        full_prompt = f"{system_prompt}\n\nUSER_INPUT:\n{message}"
        return full_prompt
    
    # (Manter outros métodos existentes)
```

**Arquivo 2 (Modificar): `src/core/agent_executor.py`**
```python
# src/core/agent_executor.py
from typing import Dict, Callable, Any, List
from src.core.domain import TaskDTO, TaskResultDTO, AgentDefinition
from src.core.prompt_engine import PromptEngine
# Removido o PlaceholderPromptEngine

class PlaceholderLLMClient:
    def invoke(self, prompt: str) -> str:
        return f"Resposta simulada para o prompt: {prompt[:100]}..."

class AgentExecutor:
    """
    Executa uma única tarefa para um agente, de forma stateless.
    """
    def __init__(
        self,
        agent_definition: AgentDefinition,
        llm_client: Any,
        prompt_engine: PromptEngine, # Agora recebe uma instância real
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
            # Assume-se que o histórico da conversa está no contexto da tarefa
            conversation_history = task.context.get("conversation_history", [])
            
            final_prompt = self._prompt_engine.build_prompt(
                conversation_history=conversation_history,
                message=task.user_input
            )

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
Seu trabalho estará concluído quando os arquivos `prompt_engine.py` e `agent_executor.py` forem modificados exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
