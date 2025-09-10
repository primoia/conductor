# Especificação Técnica e Plano de Execução: 0004-implementar-storage-factory

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa implementa o padrão de design Factory para centralizar a lógica de seleção do backend de armazenamento. Isso desacopla o `ConductorService` das implementações concretas do repositório, tornando o sistema mais limpo, fácil de manter e trivialmente extensível a novos tipos de armazenamento no futuro.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização da Lógica:** A lógica da factory **DEVE** ser implementada como um método privado dentro da classe `ConductorService` em `src/core/conductor_service.py`.
- **Criação de Placeholders:** Para que o código seja sintaticamente válido, você **DEVE** criar os arquivos e classes para `FileSystemStateRepository` e `MongoStateRepository` em `src/infrastructure/storage/`, mas eles devem conter apenas um `pass` por enquanto.
- **Tratamento de Erros:** A factory **DEVE** lançar uma `ConfigurationError` se um tipo de armazenamento desconhecido for especificado no `config.yaml`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar dois novos arquivos e modificar um existente. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `src/infrastructure/storage/filesystem_repository.py`**
```python
# src/infrastructure/storage/filesystem_repository.py
from src.ports.state_repository import IStateRepository

class FileSystemStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em sistema de arquivos."""
    pass
```

**Arquivo 2 (Novo): `src/infrastructure/storage/mongo_repository.py`**
```python
# src/infrastructure/storage/mongo_repository.py
from src.ports.state_repository import IStateRepository

class MongoStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em MongoDB."""
    pass
```

**Arquivo 3 (Modificar): `src/core/conductor_service.py`**
```python
# src/core/conductor_service.py
import yaml
from typing import List
from src.ports.conductor_service import IConductorService
from src.ports.state_repository import IStateRepository
from src.core.config_schema import GlobalConfig, StorageConfig
from src.core.exceptions import ConfigurationError
from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
from src.infrastructure.storage.mongo_repository import MongoStateRepository


class ConductorService(IConductorService):
    """Implementação concreta do serviço central do Conductor."""

    def __init__(self, config_path: str = "config.yaml"):
        self._config = self._load_and_validate_config(config_path)
        self.repository = self._create_storage_backend(self._config.storage)

    def _load_and_validate_config(self, config_path: str) -> GlobalConfig:
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return GlobalConfig(**config_data)
        except FileNotFoundError:
            raise ConfigurationError(f"Arquivo de configuração não encontrado em: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Erro ao carregar ou validar a configuração: {e}")

    def _create_storage_backend(self, storage_config: StorageConfig) -> IStateRepository:
        if storage_config.type == "filesystem":
            return FileSystemStateRepository()
        elif storage_config.type == "mongodb":
            return MongoStateRepository()
        else:
            raise ConfigurationError(f"Tipo de armazenamento desconhecido: {storage_config.type}")

    def discover_agents(self) -> List['AgentDefinition']:
        raise NotImplementedError

    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        raise NotImplementedError

    def load_tools(self) -> None:
        raise NotImplementedError
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando os arquivos `filesystem_repository.py` e `mongo_repository.py` forem criados e o `conductor_service.py` for modificado exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
