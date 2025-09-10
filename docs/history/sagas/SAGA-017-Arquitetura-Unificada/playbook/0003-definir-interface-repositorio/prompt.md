# Especificação Técnica e Plano de Execução: 0003-definir-interface-repositorio

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa estabelece a abstração da camada de persistência. Ao definir um contrato formal (`IStateRepository`), desacoplamos a lógica de negócios (`ConductorService`) dos detalhes de implementação do armazenamento (filesystem, MongoDB). Isso torna o sistema modular, testável e extensível, permitindo a adição de novos backends de armazenamento no futuro sem alterar o núcleo da aplicação.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização da Interface:** A interface **DEVE** ser localizada em um arquivo já existente, `src/ports/state_repository.py`.
- **Abstração Pura:** A classe **DEVE** herdar de `abc.ABC` e todos os seus métodos **DEVEM** ser decorados com `@abstractmethod`. Nenhuma lógica de implementação é permitida.
- **Clareza e Tipagem:** Todos os métodos e argumentos **DEVEM** ter dicas de tipo explícitas do módulo `typing`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve **substituir o conteúdo existente** do arquivo `src/ports/state_repository.py`. O novo conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Sobrescrever): `src/ports/state_repository.py`**
```python
# src/ports/state_repository.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IStateRepository(ABC):
    """
    Define o contrato para a camada de persistência de estado dos agentes.
    Qualquer backend de armazenamento (filesystem, MongoDB, etc.) deve implementar esta interface.
    """

    @abstractmethod
    def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Salva o dicionário de estado completo para um determinado agente.
        Retorna True em caso de sucesso, False caso contrário.
        """
        raise NotImplementedError

    @abstractmethod
    def load_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Carrega o dicionário de estado completo para um determinado agente.
        Retorna um dicionário vazio se o estado não for encontrado.
        """
        raise NotImplementedError

    @abstractmethod
    def list_agents(self) -> List[str]:
        """
        Lista os IDs de todos os agentes disponíveis no backend de armazenamento.
        """
        raise NotImplementedError
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o conteúdo do arquivo `src/ports/state_repository.py` for uma correspondência exata com o bloco de código fornecido na Especificação Técnica acima.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
