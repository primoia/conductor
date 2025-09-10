# Especificação Técnica e Plano de Execução: 0036-definir-dtos-api

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação. Você é um engenheiro de software definindo o contrato de dados para uma futura API.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa estabelece a fronteira de dados do nosso serviço, definindo como os clientes externos interagirão com ele no futuro. A criação de DTOs claros e validados por schema desde o início garante uma API robusta, bem documentada e estável, acelerando o desenvolvimento futuro.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** Os DTOs **DEVEM** ser adicionados ao arquivo `src/core/domain.py`.
- **Implementação:** As estruturas **DEVEM** ser implementadas como `pydantic.BaseModel` para aproveitar a validação de dados e a futura integração com frameworks de API como FastAPI.
- **Clareza:** Os campos **DEVEM** ter nomes claros, dicas de tipo explícitas e, opcionalmente, descrições.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve **adicionar novas classes** ao arquivo `src/core/domain.py`. O conteúdo a ser adicionado **DEVE** ser exatamente como especificado abaixo. Não altere outras classes que possam existir no arquivo.

**Arquivo 1 (Modificar): `src/core/domain.py`**
```python
# src/core/domain.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field as PydanticField

# ... (dataclasses existentes) ...

# --- Modelos de API (Pydantic) ---

class ExecuteTaskRequest(BaseModel):
    """
    Modelo para uma requisição de execução de tarefa via API.
    """
    agent_id: str = PydanticField(..., description="O ID do agente a ser executado.")
    user_input: str = PydanticField(..., description="O input/prompt do usuário para o agente.")
    context: Dict[str, Any] = PydanticField(default_factory=dict, description="Contexto adicional opcional para a tarefa.")

class TaskCreationResponse(BaseModel):
    """
    Modelo para a resposta imediata após a criação de uma tarefa.
    """
    task_id: str = PydanticField(..., description="O ID único da tarefa que foi iniciada.")
    status: str = PydanticField(default="pending", description="O status inicial da tarefa.")

class TaskStatusResponse(BaseModel):
    """
    Modelo para a resposta ao consultar o status de uma tarefa.
    """
    task_id: str = PydanticField(..., description="O ID da tarefa.")
    status: str = PydanticField(..., description="O status atual da tarefa (ex: pending, in_progress, success, error).")
    output: Optional[str] = PydanticField(default=None, description="A saída final da tarefa, se concluída.")
    metadata: Dict[str, Any] = PydanticField(default_factory=dict, description="Metadados adicionais sobre a execução.")
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando as classes Pydantic `ExecuteTaskRequest`, `TaskCreationResponse`, e `TaskStatusResponse` forem adicionadas ao arquivo `src/core/domain.py` exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
