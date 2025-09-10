# Especificação Técnica e Plano de Execução: 0002-implementar-carregador-config

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa estabelece a fundação da autoconsciência do sistema. Ao implementar um carregador de configuração robusto e validado por schema, garantimos que o `ConductorService` sempre opere com parâmetros válidos e conhecidos, eliminando erros em tempo de execução causados por configurações malformadas e centralizando a fonte da verdade do sistema no `config.yaml`.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Validação por Schema:** A validação da configuração **DEVE** ser feita usando Pydantic para garantir a tipagem e a estrutura corretas.
- **Localização dos Schemas:** Os modelos Pydantic para a configuração **DEVEM** ser definidos em um novo arquivo `src/core/config_schema.py`.
- **Localização do Serviço:** A classe `ConductorService` **DEVE** ser criada em `src/core/conductor_service.py` e **DEVE** implementar a interface `IConductorService` de `src/ports/conductor_service.py`.
- **Tratamento de Erros:** Em caso de falha de leitura ou validação, o `__init__` do serviço **DEVE** lançar uma exceção customizada `ConfigurationError` (que deve ser criada em `src/core/exceptions.py`).

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar/modificar três arquivos. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `src/core/config_schema.py`**
```python
# src/core/config_schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class StorageConfig(BaseModel):
    type: str
    path: str = Field(default=None) # Ex: .conductor_workspace
    connection_string: str = Field(default=None) # Ex: mongodb://...

class GlobalConfig(BaseModel):
    storage: StorageConfig
    tool_plugins: List[str] = Field(default_factory=list)
```

**Arquivo 2 (Modificar): `src/core/exceptions.py`**
```python
# src/core/exceptions.py
# ... (conteúdo existente) ...

class ConfigurationError(Exception):
    """Exceção para erros de configuração."""
    pass
```

**Arquivo 3 (Novo): `src/core/conductor_service.py`**
```python
# src/core/conductor_service.py
import yaml
from typing import List
from src.ports.conductor_service import IConductorService
from src.core.config_schema import GlobalConfig
from src.core.exceptions import ConfigurationError

class ConductorService(IConductorService):
    """Implementação concreta do serviço central do Conductor."""

    def __init__(self, config_path: str = "config.yaml"):
        self._config = self._load_and_validate_config(config_path)

    def _load_and_validate_config(self, config_path: str) -> GlobalConfig:
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return GlobalConfig(**config_data)
        except FileNotFoundError:
            raise ConfigurationError(f"Arquivo de configuração não encontrado em: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Erro ao carregar ou validar a configuração: {e}")

    def discover_agents(self) -> List['AgentDefinition']:
        raise NotImplementedError

    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        raise NotImplementedError

    def load_tools(self) -> None:
        raise NotImplementedError
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando os arquivos `src/core/config_schema.py`, `src/core/conductor_service.py` e `src/core/exceptions.py` forem criados/modificados exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
