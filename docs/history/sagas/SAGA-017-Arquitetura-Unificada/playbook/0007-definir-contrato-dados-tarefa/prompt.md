# Especificação Técnica e Plano de Execução: 0007-definir-contrato-dados-tarefa

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa estabelece a estrutura de dados canônica para a execução de trabalho no sistema. Ao definir DTOs claros e fortemente tipados para tarefas e seus resultados, criamos uma API interna estável que melhora a legibilidade, a manutenibilidade e serve como base para futuras integrações externas (APIs, filas de mensagens).

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização dos DTOs:** As novas estruturas de dados **DEVEM** ser adicionadas ao arquivo `src/core/domain.py`.
- **Implementação:** As estruturas **DEVEM** ser implementadas como `@dataclass` do Python para simplicidade e clareza.
- **Clareza e Tipagem:** Todos os campos **DEVEM** ter dicas de tipo explícitas do módulo `typing`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve **adicionar novas classes** ao arquivo `src/core/domain.py`. O conteúdo a ser adicionado **DEVE** ser exatamente como especificado abaixo. Não altere outras classes que possam existir no arquivo.

**Arquivo 1 (Modificar): `src/core/domain.py`**
```python
# src/core/domain.py
from dataclasses import dataclass, field
from typing import List, Dict, Any

# ... (AgentDefinition e outras classes existentes) ...

@dataclass(frozen=True)
class TaskDTO:
    """
    Data Transfer Object para encapsular uma requisição de tarefa.
    """
    agent_id: str
    user_input: str
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TaskResultDTO:
    """
    Data Transfer Object para encapsular o resultado de uma tarefa executada.
    """
    status: str  # Ex: 'success', 'error'
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando as classes `TaskDTO` e `TaskResultDTO` forem adicionadas ao arquivo `src/core/domain.py` exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
