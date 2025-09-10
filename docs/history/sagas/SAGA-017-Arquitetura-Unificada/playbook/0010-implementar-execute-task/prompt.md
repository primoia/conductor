# Especificação Técnica e Plano de Execução: 0010-implementar-execute-task

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa é a culminação da Fase I, unindo todos os componentes do novo núcleo de serviços. A implementação de `execute_task` cria o ponto de entrada funcional para toda a lógica de execução de agentes, estabelecendo um fluxo de orquestração limpo e desacoplado que servirá de base para todas as futuras interfaces (CLIs, APIs).

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Orquestração no Serviço:** Toda a lógica de "conectar as peças" (carregar estado, instanciar executor, etc.) **DEVE** residir no `ConductorService`.
- **Injeção de Dependência:** O `ConductorService` **DEVE** injetar todas as dependências necessárias no `AgentExecutor` durante sua instanciação.
- **Contrato de Dados:** O método **DEVE** aderir estritamente ao contrato de dados definido, aceitando um `TaskDTO` e retornando um `TaskResultDTO`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar um arquivo existente. O conteúdo do método `execute_task` **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Modificar): `src/core/conductor_service.py`**
```python
# src/core/conductor_service.py
# ... (imports existentes) ...
from src.core.domain import TaskDTO, TaskResultDTO
from src.core.agent_executor import AgentExecutor, PlaceholderLLMClient
from src.core.prompt_engine import PromptEngine

class ConductorService(IConductorService):
    # ... (__init__ e outros métodos existentes) ...

    def execute_task(self, task: TaskDTO) -> TaskResultDTO:
        try:
            # 1. Carregar o estado completo do agente
            agent_state = self.repository.load_state(task.agent_id)
            if not agent_state or "definition" not in agent_state:
                raise FileNotFoundError(f"Definição não encontrada para o agente: {task.agent_id}")

            agent_definition = AgentDefinition(**agent_state["definition"])
            
            # 2. Obter o caminho do agente (assumindo que está no estado)
            agent_home_path = agent_state.get("agent_home_path")
            if not agent_home_path:
                raise ValueError(f"agent_home_path não encontrado no estado do agente {task.agent_id}")

            # 3. Instanciar as dependências de execução
            #    (Usando placeholders por enquanto)
            llm_client = PlaceholderLLMClient() 
            prompt_engine = PromptEngine(agent_home_path=agent_home_path)
            
            # 4. Filtrar as ferramentas permitidas
            allowed_tools = {
                name: tool_func for name, tool_func in self._tools.items()
                if name in agent_state.get("allowed_tools", [])
            }

            # 5. Instanciar e executar o executor
            executor = AgentExecutor(
                agent_definition=agent_definition,
                llm_client=llm_client,
                prompt_engine=prompt_engine,
                allowed_tools=allowed_tools
            )
            
            result = executor.run(task)
            return result

        except Exception as e:
            return TaskResultDTO(status="error", output=str(e), metadata={})

    # ... (outros métodos existentes) ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o método `execute_task` em `src/core/conductor_service.py` for modificado exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
