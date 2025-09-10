# Especificação Técnica e Plano de Execução: 0029-depreciar-agent-logic

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação. Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa comunica formalmente a obsolescência do `AgentLogic`, prevenindo seu uso acidental em novo código e estabelecendo um passo claro no processo de limpeza de débito técnico, conforme as melhores práticas de engenharia de software.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Mecanismo Padrão:** O aviso de depreciação **DEVE** usar o módulo `warnings` e a classe `DeprecationWarning` do Python.
- **Comunicação Dupla:** A depreciação **DEVE** ser comunicada tanto em tempo de execução (através do warning) quanto na documentação estática (através do docstring da classe).

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar o arquivo `src/core/agent_logic.py` para adicionar o código de depreciação.

**Arquivo 1 (Modificar): `src/core/agent_logic.py`**
```python
# src/core/agent_logic.py
import warnings
# ... (outros imports existentes) ...

class AgentLogic:
    """
    DEPRECATED: Esta classe foi substituída pelo AgentExecutor e ConductorService.
    Não deve ser usada em novo código. Será removida em uma versão futura.

    Core business logic for agent embodiment and interaction.
    # ... (resto do docstring original) ...
    """

    def __init__(self, state_repository: StateRepository, llm_client: LLMClient):
        """
        Initialize agent logic with injected dependencies.
        """
        warnings.warn(
            "A classe AgentLogic está depreciada e será removida em breve. "
            "Use AgentExecutor e ConductorService.",
            DeprecationWarning,
            stacklevel=2
        )
        self.state_repository = state_repository
        # ... (resto do __init__ original) ...

    # ... (resto da classe sem alterações) ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `src/core/agent_logic.py` for modificado para incluir o `DeprecationWarning` no `__init__` e o aviso no docstring da classe.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
