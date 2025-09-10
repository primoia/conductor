# Especificação Técnica e Plano de Execução: 0028.10-implementar-fs-discovery

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa habilitar o `FileSystemStateRepository` a descobrir e carregar corretamente os artefatos JSON dos agentes, resolvendo as falhas nos testes de integração do Maestro-Executor e permitindo a validação da Fase VII.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar o arquivo `src/infrastructure/persistence/state_repository.py`.

**Arquivo 1 (Modificar): `src/infrastructure/persistence/state_repository.py`**

```python
# src/infrastructure/persistence/state_repository.py
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path # Adicionar import de Path
from src.ports.state_repository import IStateRepository as StateRepository
from src.core.exceptions import StatePersistenceError

logger = logging.getLogger(__name__)


class FileStateRepository(StateRepository):
    """
    Implementação do StateRepository que usa arquivos state.json.
    """

    def __init__(self, base_path: str = ".conductor_workspace"):
        self.base_path = Path(base_path)
        self.agents_path = self.base_path / "agents"
        self.agents_path.mkdir(parents=True, exist_ok=True)

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        # O load_state agora recebe apenas o agent_id e carrega o JSON completo do agente
        agent_file_path = self.agents_path / f"{agent_id}.json"
        try:
            if agent_file_path.exists():
                with open(agent_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            # Retorna um estado inicial padrão se o arquivo não existir
            return {"definition": {"name": "", "version": "", "schema_version": "", "description": "", "author": "", "tags": [], "capabilities": [], "allowed_tools": []}}
        except Exception as e:
            logger.error(f"Failed to load agent state from {agent_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to load agent state from {agent_file_path}: {e}"
            )

    def save_state(
        self, agent_id: str, state_data: Dict[str, Any]
    ) -> bool:
        # O save_state agora salva o JSON completo do agente
        agent_file_path = self.agents_path / f"{agent_id}.json"
        try:
            self.agents_path.mkdir(parents=True, exist_ok=True)
            with open(agent_file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save agent state to {agent_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to save agent state to {agent_file_path}: {e}"
            )

    def list_agents(self) -> List[str]:
        """Lista os IDs de todos os agentes disponíveis no backend de armazenamento."""
        agent_ids = []
        for item in self.agents_path.iterdir():
            if item.is_file() and item.suffix == ".json":
                agent_ids.append(item.stem)
        return agent_ids


class MongoStateRepository(StateRepository):
    # ... (manter __init__ e close)

    def load_state(self, agent_id: str) -> Dict[str, Any]: # Ajustar assinatura
        # ... (lógica existente, mas agora recebe apenas agent_id)
        # O _generate_document_id precisará ser ajustado ou removido se não for mais necessário
        pass # Manter pass por enquanto, foco no FileSystem

    def save_state(
        self, agent_id: str, state_data: Dict[str, Any]
    ) -> bool: # Ajustar assinatura
        # ... (lógica existente, mas agora recebe apenas agent_id)
        pass # Manter pass por enquanto, foco no FileSystem

    def list_agents(self) -> List[str]:
        """Lista os IDs de todos os agentes disponíveis no backend de armazenamento."""
        return [] # Manter vazio por enquanto, foco no FileSystem
```

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
