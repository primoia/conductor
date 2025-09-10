# Especificação Técnica e Plano de Execução: 0016-refatorar-cli-admin

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa executa a primeira parte da "cirurgia de transplante", conectando a interface de usuário do `admin.py` ao novo `ConductorService`. Isso unifica o comportamento do meta-agente com a nova arquitetura, garantindo que ele opere sob as mesmas regras (configuração, armazenamento, ferramentas) que o resto do sistema.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Preservação da Interface:** A interface de linha de comando (os argumentos que o usuário passa) do `admin.py` **NÃO DEVE** ser alterada. O script deve continuar a funcionar da mesma forma do ponto de vista do usuário.
- **Remoção da Lógica Legada:** Toda a lógica de descoberta de caminhos de agente e a instanciação direta do `AgentLogic` **DEVEM** ser removidas do `AdminCLI`.
- **Uso do Serviço Central:** O `AdminCLI` **DEVE** obter sua instância do `ConductorService` a partir do container de DI e usá-la para todas as operações.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar o arquivo `src/cli/admin.py`. O código abaixo representa a **estrutura final esperada** da classe `AdminCLI`. Você deve refatorar a classe existente para corresponder a esta nova estrutura, removendo a lógica antiga e adicionando a nova.

**Arquivo 1 (Modificar): `src/cli/admin.py`**
```python
# src/cli/admin.py
# ... (manter imports de Path, sys, e CLI shared) ...
from src.container import container
from src.core.domain import TaskDTO

class AdminCLI:
    """
    Admin CLI - agora uma casca fina sobre o ConductorService.
    """
    def __init__(
        self,
        agent_id: str,
        # ... (manter outros parâmetros como new_agent_id, debug_mode etc.) ...
    ):
        # ... (configuração de logger e outros atributos) ...
        self.agent_id = agent_id # Armazenar o agent_id alvo
        
        # Obter o serviço central
        self.conductor_service = container.conductor_service()
        
        # O "embody" agora é implícito na execução da tarefa pelo serviço
        print(f"✅ AdminCLI inicializado. Usando ConductorService.")

    @property
    def embodied(self) -> bool:
        """Verifica se o agente alvo existe no ecossistema."""
        try:
            # A nova forma de verificar é ver se o serviço consegue encontrar o agente
            agents = self.conductor_service.discover_agents()
            return any(agent.agent_id == self.agent_id for agent in agents)
        except Exception:
            return False

    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Envia uma mensagem ao agente através do ConductorService."""
        if not self.embodied:
            return f"❌ Agente '{self.agent_id}' não encontrado pelo ConductorService."

        try:
            # 1. Construir o DTO da tarefa
            # O contexto (meta, new_agent_id) é passado no DTO
            task_context = {
                "meta": self.meta,
                "new_agent_id": self.new_agent_id,
                "debug_save_input": debug_save_input,
                "simulate_mode": self.simulate_mode
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
            self.logger.error(f"Erro no chat do AdminCLI: {e}")
            return f"❌ Erro fatal no AdminCLI: {e}"

    # ... (outros métodos como save_agent_state podem ser adaptados ou removidos
    #      se o estado agora for gerenciado inteiramente pelo serviço) ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando a classe `AdminCLI` em `src/cli/admin.py` for refatorada para usar o `ConductorService`, removendo a lógica legada, mas preservando o comportamento externo do script.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
