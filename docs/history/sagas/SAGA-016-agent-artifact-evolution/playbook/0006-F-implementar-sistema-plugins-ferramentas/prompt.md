# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0006-F

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é criar um **Sistema de Extensibilidade** para as ferramentas do Conductor. Em vez de ter todas as ferramentas como parte do código-fonte principal, o que leva ao inchaço e dificulta a manutenção, nós implementaremos um sistema de "plugins". Isso permite que novas ferramentas sejam adicionadas ao sistema simplesmente colocando um arquivo Python em um diretório, tornando o Conductor modular, mais leve e permitindo que a comunidade ou equipes específicas estendam suas capacidades sem precisar modificar o núcleo.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Descoberta Dinâmica:** As ferramentas **DEVEM** ser carregadas dinamicamente durante a inicialização da aplicação. Não deve haver um registro manual ou importações estáticas das ferramentas de plugins no código principal.
- **Carregamento Baseado em Configuração:** Os diretórios a serem escaneados em busca de plugins **DEVEM** ser definidos na seção `tool_plugins` do arquivo `config.yaml`.
- **Mecanismo de Registro Explícito:** Uma função **NÃO DEVE** ser considerada uma ferramenta por padrão. Ela **DEVE** ser explicitamente marcada com um decorador `@tool` para ser descoberta e registrada pelo `ToolManager`.
- **Separação de Camadas:** A lógica de gerenciamento de ferramentas **DEVE** residir em `src/core/tool_manager.py`, e o decorador `@tool` em `src/core/tools.py`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Criar o arquivo `src/core/tools.py`:**
```python
# src/core/tools.py

def tool(func):
    """
    Decorador para marcar uma função como uma ferramenta registrável pelo ToolManager.
    """
    setattr(func, '_is_tool', True)
    return func
```

**2. Criar o arquivo `src/core/tool_manager.py`:**
```python
# src/core/tool_manager.py

import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Callable

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, function: Callable):
        if name in self.tools:
            print(f"Aviso: A ferramenta '{name}' está sendo sobrescrita.")
        self.tools[name] = function

    def load_plugins_from_config(self, config: Dict):
        """
        Escaneia diretórios de plugins definidos na configuração, carrega os módulos
        e registra as funções marcadas com @tool.
        """
        plugin_paths = config.get('tool_plugins', [])
        for path_str in plugin_paths:
            self._load_from_directory(Path(path_str))

    def _load_from_directory(self, dir_path: Path):
        """Carrega ferramentas de todos os arquivos .py em um diretório."""
        for file_path in dir_path.glob("*.py"):
            self._load_from_file(file_path)
            
    def _load_from_file(self, file_path: Path):
        """Carrega um módulo Python e registra suas ferramentas."""
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, func in inspect.getmembers(module, inspect.isfunction):
                if getattr(func, '_is_tool', False):
                    self.register_tool(func.__name__, func)
        except Exception as e:
            print(f"Erro ao carregar o plugin '{file_path}': {e}")
```

**3. Criar diretório e arquivo de exemplo `custom_tools/example_tool.py`:**
```python
# custom_tools/example_tool.py

from src.core.tools import tool

@tool
def say_hello(name: str) -> str:
    """Uma ferramenta de exemplo que retorna uma saudação."""
    return f"Hello, {name}!"
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- Os arquivos `tools.py` e `tool_manager.py` foram criados com o conteúdo especificado.
- O `ToolManager` carrega e registra com sucesso as ferramentas de um diretório de plugin definido no `config.yaml`.
- Funções sem o decorador `@tool` não são registradas.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
