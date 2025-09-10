# Especificação Técnica e Plano de Execução: 0017-refatorar-cli-agent

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa completa a unificação da camada de entrada, garantindo que o `agent.py` também opere sobre o novo `ConductorService`. Isso elimina a última peça de lógica de descoberta legada do sistema, tornando a arquitetura interna totalmente coesa e consistente, conforme o mandato da SAGA-017.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Preservação da Interface:** A interface de linha de comando do `agent.py` (`--environment`, `--project`, etc.) **NÃO DEVE** ser alterada.
- **Remoção da Lógica Legada:** Toda a lógica de construção de caminhos de agente e a instanciação do `AgentLogic` **DEVEM** ser removidas.
- **Uso do Serviço Central:** O `AgentCLI` **DEVE** obter e usar a instância singleton do `ConductorService` para todas as operações.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar o arquivo `src/cli/agent.py`. O código abaixo representa a **estrutura final esperada** da classe `AgentCLI`. Você deve refatorar a classe existente para corresponder a esta nova estrutura.

**Arquivo 1 (Modificar): `src/cli/agent.py`**
```python
# src/cli/agent.py
# ... (manter imports de Path, sys, e CLI shared) ...
from src.container import container
from src.core.domain import TaskDTO

class AgentCLI:
    """
    Agent CLI - agora uma casca fina sobre o ConductorService.
    """
    def __init__(
        self,
        environment: str,
        project: str,
        agent_id: str,
        # ... (outros parâmetros como debug_mode etc.) ...
    ):
        # ... (configuração de logger e outros atributos) ...
        self.agent_id = agent_id
        self.environment = environment
        self.project = project
        
        # Obter o serviço central
        self.conductor_service = container.conductor_service()
        
        print(f"✅ AgentCLI inicializado. Usando ConductorService.")

    @property
    def embodied(self) -> bool:
        """Verifica se o agente alvo existe no ecossistema."""
        try:
            agents = self.conductor_service.discover_agents()
            return any(agent.agent_id == self.agent_id for agent in agents)
        except Exception:
            return False

    def chat(self, message: str) -> str:
        """Envia uma mensagem ao agente através do ConductorService."""
        if not self.embodied:
            return f"❌ Agente '{self.agent_id}' não encontrado pelo ConductorService."

        try:
            # 1. Construir o DTO da tarefa
            task_context = {
                "environment": self.environment,
                "project": self.project
            }
            task = TaskDTO(
                agent_id=self.agent_id,
                user_input=message,
                context=task_context
            )

            # 2. Delegar a execução para o serviço central
            result = self.conductor_service.execute_task(task)

            # 3. Processar o resultado
            if result.status == "success":
                return result.output
            else:
                return f"❌ Erro na execução da tarefa: {result.output}"

        except Exception as e:
            self.logger.error(f"Erro no chat do AgentCLI: {e}")
            return f"❌ Erro fatal no AgentCLI: {e}"

    # ... (outros métodos como get_output_scope podem ser adaptados
    #      para obter a informação do serviço ou removidos) ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando a classe `AgentCLI` em `src/cli/agent.py` for refatorada para usar o `ConductorService`, removendo a lógica legada e preservando o comportamento externo do script.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
