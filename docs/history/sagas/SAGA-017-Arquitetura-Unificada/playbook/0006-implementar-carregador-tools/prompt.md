# Especificação Técnica e Plano de Execução: 0006-implementar-carregador-tools

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa implementa a capacidade de extensibilidade do Conductor, uma promessa central da SAGA-016. Ao criar um carregador de ferramentas que suporta plugins, transformamos o Conductor de uma aplicação monolítica em um framework extensível, permitindo que os usuários adaptem suas capacidades a necessidades específicas sem alterar o código do núcleo.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Registro Centralizado:** As ferramentas carregadas **DEVEM** ser mantidas em um dicionário privado dentro do `ConductorService` (ex: `self._tools`).
- **Carregamento Dinâmico:** O carregamento de plugins **DEVE** usar `importlib` e `pkgutil` para escanear e importar módulos de diretórios de forma dinâmica.
- **Estrutura de Ferramentas:** Para esta tarefa, assumiremos que uma "ferramenta" é simplesmente uma função Python. Uma estrutura mais formal (classes de ferramentas) pode ser implementada posteriormente.
- **Segurança:** O caminho para os plugins **DEVE** ser validado para evitar path traversal.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo e modificar um existente. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `src/core/tools/core_tools.py`**
```python
# src/core/tools/core_tools.py
import datetime

def get_current_time() -> str:
    """Retorna a data e hora atuais no formato ISO."""
    return datetime.datetime.now().isoformat()

# Ferramentas são registradas em uma lista para fácil importação
CORE_TOOLS = [get_current_time]
```

**Arquivo 2 (Modificar): `src/core/conductor_service.py`**
```python
# src/core/conductor_service.py
import yaml
import importlib
import pkgutil
import sys
from pathlib import Path
from typing import List, Dict, Callable, Any
# ... (outros imports existentes) ...
from src.core.tools.core_tools import CORE_TOOLS

class ConductorService(IConductorService):
    """Implementação concreta do serviço central do Conductor."""

    def __init__(self, config_path: str = "config.yaml"):
        self._config = self._load_and_validate_config(config_path)
        self.repository = self._create_storage_backend(self._config.storage)
        self._tools: Dict[str, Callable[..., Any]] = {}
        self.load_tools()

    # ... (_load_and_validate_config, _create_storage_backend existentes) ...

    def discover_agents(self) -> List[AgentDefinition]:
        # ... (implementação existente) ...
        agent_ids = self.repository.list_agents()
        definitions = []
        for agent_id in agent_ids:
            state = self.repository.load_state(agent_id)
            if "definition" in state:
                definitions.append(AgentDefinition(**state["definition"]))
        return definitions

    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        raise NotImplementedError

    def load_tools(self) -> None:
        # Carregar Core Tools
        for tool in CORE_TOOLS:
            self._tools[tool.__name__] = tool

        # Carregar Tool Plugins
        for plugin_path_str in self._config.tool_plugins:
            plugin_path = Path(plugin_path_str).resolve()
            if not plugin_path.is_dir():
                print(f"Aviso: Caminho do plugin não é um diretório: {plugin_path}")
                continue
            
            # Adicionar ao path e importar módulos
            sys.path.insert(0, str(plugin_path.parent))
            for finder, name, ispkg in pkgutil.iter_modules([str(plugin_path)]):
                module = importlib.import_module(f"{plugin_path.name}.{name}")
                # Assumir que plugins também têm uma lista 'PLUGIN_TOOLS'
                if hasattr(module, 'PLUGIN_TOOLS'):
                    for tool in module.PLUGIN_TOOLS:
                        self._tools[tool.__name__] = tool
            sys.path.pop(0)
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `core_tools.py` for criado e o `conductor_service.py` for modificado exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
