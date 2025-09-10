# Especificação Técnica e Plano de Execução: 0005-implementar-descoberta-agentes

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa centraliza a lógica de descoberta de agentes no `ConductorService`, removendo a responsabilidade dos CLIs e garantindo que a descoberta funcione de forma consistente em qualquer backend de armazenamento. É um passo fundamental para desacoplar os pontos de entrada dos detalhes de implementação da persistência.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **DTOs no Domínio:** A estrutura de dados `AgentDefinition` **DEVE** ser definida em `src/core/domain.py` usando `dataclasses`.
- **Lógica no Serviço:** A lógica de orquestração da descoberta (chamar o repositório, mapear os dados) **DEVE** residir exclusivamente no método `discover_agents` do `ConductorService`.
- **Implementação Mockada:** A implementação do `list_agents` e `load_state` no `FileSystemStateRepository` será mockada por enquanto, retornando dados fixos para permitir o desenvolvimento do serviço.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar três arquivos existentes. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Modificar): `src/core/domain.py`**
```python
# src/core/domain.py
from dataclasses import dataclass, field
from typing import List

# (Adicione esta nova classe, mantendo outras que possam existir)
@dataclass(frozen=True)
class AgentDefinition:
    """
    Representa a identidade estática e versionada de um agente.
    """
    agent_id: str
    name: str
    version: str
    description: str
    # Adicione outros campos conforme necessário no futuro
```

**Arquivo 2 (Modificar): `src/infrastructure/storage/filesystem_repository.py`**
```python
# src/infrastructure/storage/filesystem_repository.py
from src.ports.state_repository import IStateRepository
from typing import Dict, Any, List

class FileSystemStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em sistema de arquivos."""

    def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        # A ser implementado
        return True

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # Retorna um mock para fins de desenvolvimento
        if agent_id == "CodeReviewer_Agent":
            return {
                "definition": {
                    "agent_id": "CodeReviewer_Agent",
                    "name": "Code Reviewer Agent",
                    "version": "1.0.0",
                    "description": "Um agente especialista em revisar código."
                }
            }
        return {}

    def list_agents(self) -> List[str]:
        # Retorna uma lista mockada para fins de desenvolvimento
        return ["CodeReviewer_Agent"]
```

**Arquivo 3 (Modificar): `src/core/conductor_service.py`**
```python
# src/core/conductor_service.py
# ... (imports existentes) ...
from src.core.domain import AgentDefinition

class ConductorService(IConductorService):
    # ... (__init__ e outros métodos existentes) ...

    def discover_agents(self) -> List[AgentDefinition]:
        agent_ids = self.repository.list_agents()
        definitions = []
        for agent_id in agent_ids:
            state = self.repository.load_state(agent_id)
            if "definition" in state:
                # Assumindo que a 'definition' no estado corresponde aos campos do DTO
                definitions.append(AgentDefinition(**state["definition"]))
        return definitions

    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        raise NotImplementedError

    def load_tools(self) -> None:
        raise NotImplementedError
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando os arquivos `domain.py`, `filesystem_repository.py` e `conductor_service.py` forem modificados exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
