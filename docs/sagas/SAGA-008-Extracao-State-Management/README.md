# SAGA-008: Extração e Abstração do Gerenciamento de Estado

**Autor:** Primo (Gemini)
**Status:** Proposto

## 1. Resumo Executivo

Esta saga propõe uma refatoração arquitetural para extrair a lógica de gerenciamento de estado (atualmente acoplada ao `genesis_core.py`) para um módulo independente e abstrato. A implementação seguirá o **Repository Pattern**, introduzindo uma interface `StateRepository` que desacopla o `GenesisAgent` do método de armazenamento subjacente (seja `state.json` ou um banco de dados como MongoDB).

O objetivo é aumentar a modularidade, a testabilidade e a flexibilidade do framework, permitindo que diferentes estratégias de persistência de estado sejam implementadas e trocadas sem impactar a lógica de negócio central do agente.

## 2. Justificativa Técnica

A arquitetura atual, embora funcional, apresenta um forte acoplamento entre a lógica do agente e a forma como seu estado é persistido (leitura/escrita de um arquivo `state.json`). Isso resulta em várias limitações:

- **Baixa Coesão:** A classe `GenesisAgent` tem múltiplas responsabilidades: orquestrar a lógica do agente **e** gerenciar a persistência de arquivos.
- **Dificuldade de Teste:** Testar o `GenesisAgent` requer a manipulação de arquivos reais no sistema de arquivos, tornando os testes mais lentos e complexos. É difícil usar mocks ou versões em memória do estado.
- **Falta de Flexibilidade:** Se quisermos mover o armazenamento de estado para um banco de dados (para melhor escalabilidade e consultas), seríamos forçados a alterar o código central do `GenesisAgent`.

A adoção do Repository Pattern resolve esses problemas ao introduzir uma camada de abstração, alinhando o código a princípios de design robustos como a **Inversão de Dependência**.

## 3. Plano de Implementação Detalhado

A refatoração será executada nos seguintes passos:

### Passo 1: Definir a Interface `StateRepository`

- **Ação:** Criar um novo arquivo `scripts/core/state_repository.py`.
- **Conteúdo:** Definir uma classe base abstrata que estabelece o "contrato" para todos os repositórios de estado.

```python
# scripts/core/state_repository.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class StateRepository(ABC):
    """
    Interface abstrata para gerenciamento de persistência de estado do agente.
    """

    @abstractmethod
    def load_state(self, agent_home_path: str, state_file_name: str) -> Dict[str, Any]:
        """
        Carrega o estado de um agente.

        Retorna um dicionário com o estado ou um estado inicial padrão se não existir.
        """
        pass

    @abstractmethod
    def save_state(self, agent_home_path: str, state_file_name: str, state_data: Dict[str, Any]) -> bool:
        """
        Salva o estado de um agente.

        Retorna True em caso de sucesso, False caso contrário.
        """
        pass
```

### Passo 2: Criar a Implementação `FileStateRepository`

- **Ação:** No mesmo arquivo `state_repository.py`, criar a implementação concreta para o `state.json`.
- **Lógica:** Mover o código dos métodos `_load_agent_state_v2` e `save_agent_state_v2` do `genesis_core.py` para os métodos `load_state` e `save_state` desta nova classe.

```python
# scripts/core/state_repository.py (continuação)
import os
import json
from datetime import datetime

class FileStateRepository(StateRepository):
    """
    Implementação do StateRepository que usa arquivos state.json.
    """
    def load_state(self, agent_home_path: str, state_file_name: str) -> Dict[str, Any]:
        state_file_path = os.path.join(agent_home_path, state_file_name)
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # Retorna um estado inicial padrão se o arquivo não existir
            return {"conversation_history": []}
        except Exception:
            # Logar o erro no futuro
            return {"conversation_history": []}

    def save_state(self, agent_home_path: str, state_file_name: str, state_data: Dict[str, Any]) -> bool:
        state_file_path = os.path.join(agent_home_path, state_file_name)
        try:
            os.makedirs(os.path.dirname(state_file_path), exist_ok=True)
            with open(state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            # Logar o erro no futuro
            return False
```

### Passo 3: Refatorar a Classe `GenesisAgent`

- **Ação:** Modificar `scripts/core/genesis_core.py` para usar a nova abstração.
- **Lógica:**
    1.  Alterar o `__init__` para receber uma instância de `StateRepository` via **injeção de dependência**.
    2.  Substituir as chamadas aos métodos antigos pelos métodos do repositório.

```python
# Em scripts/core/genesis_core.py

# ... outros imports
from .state_repository import StateRepository # Importar a nova classe

class GenesisAgent:
    def __init__(self, ..., state_repository: StateRepository): # Adicionar ao construtor
        # ...
        self.state_repository = state_repository # Armazenar a instância
        # ...

    def embody_agent_v2(self, agent_id: str) -> bool:
        # ...
        # Substituir a chamada direta ao método antigo
        # self._load_agent_state_v2(str(state_file_path))
        
        # Nova chamada usando o repositório
        state_data = self.state_repository.load_state(
            self.agent_home_path,
            self.agent_config.get("state_file_path", "state.json")
        )
        self.llm_client.conversation_history = state_data.get("conversation_history", [])
        # ...

    def save_agent_state_v2(self):
        # ...
        # Substituir a lógica de salvar arquivo por uma chamada ao repositório
        state_data = {
            'conversation_history': self.llm_client.conversation_history,
            'last_modified': datetime.now().isoformat(),
            # ... outros dados
        }
        self.state_repository.save_state(
            self.agent_home_path,
            self.agent_config.get("state_file_path", "state.json"),
            state_data
        )
```

### Passo 4: Atualizar os Pontos de Entrada (`agent.py` e `admin.py`)

- **Ação:** Modificar os scripts `agent.py` e `admin.py` para que eles criem e injetem a dependência do `FileStateRepository`.
- **Lógica:**

```python
# Em scripts/agent.py (e similarmente em admin.py)

from core import GenesisAgent
from core.state_repository import FileStateRepository # Importar a implementação

def main():
    # ...
    # Instanciar o repositório
    state_repo = FileStateRepository()

    # Injetar o repositório no construtor do GenesisAgent
    agent = GenesisAgent(
        environment=args.environment,
        project=args.project,
        # ... outros args
        state_repository=state_repo # Passar a instância
    )
    # ...
```

## 4. Plano de Testes

1.  **Testes Unitários:** Criar testes para `FileStateRepository` para garantir que ele lê e escreve arquivos JSON corretamente.
2.  **Testes de Integração:** Modificar os testes existentes do `GenesisAgent` para injetar um `FileStateRepository` (ou um mock) e verificar que o ciclo de carregar e salvar estado continua funcionando perfeitamente através da nova camada de abstração.

## 5. Conclusão

Esta refatoração representa um salto de maturidade na arquitetura do Conductor. Ao desacoplar o gerenciamento de estado, abrimos caminho para futuras expansões (como múltiplos backends de armazenamento) e tornamos o sistema mais limpo, modular e profissional.
