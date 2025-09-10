# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0004-D

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é desacoplar a lógica de negócios da seleção e configuração da infraestrutura de armazenamento, implementando os padrões **Factory** e **Dependency Injection**. Ao centralizar a lógica de decisão ("qual banco de dados usar?") em uma `RepositoryFactory` e ler essa decisão de um arquivo de configuração externo, tornamos o sistema flexível e configurável. Isso nos permite alternar entre os modos `filesystem` e `mongodb` sem alterar uma única linha de código nos serviços principais.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Configuração Externa:** O comportamento da aplicação **DEVE** ser controlado por um arquivo `config.yaml` na raiz do projeto. O código não deve ter valores "hardcoded" para o tipo de armazenamento.
- **Validação de Configuração:** O `ConfigManager` **DEVE** validar o conteúdo do `config.yaml` durante o carregamento. Se a seção `storage_backend` estiver ausente ou o `type` for inválido (diferente de 'filesystem' ou 'mongodb'), uma exceção `InvalidConfigurationError` **DEVE** ser levantada.
- **Separação de Camadas:** A lógica da fábrica de repositórios **DEVE** residir em `src/infrastructure/repository_factory.py`, pois está diretamente relacionada à camada de infraestrutura.
- **Ponto de Entrada Único:** A inicialização e injeção de dependências (carregar config -> criar repositório -> criar serviço) **DEVE** ocorrer em um único local centralizado, preferencialmente em `src/container.py`, para gerenciar o ciclo de vida dos objetos da aplicação.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Criar o arquivo `config.yaml` na raiz do projeto:**

```yaml
# config.yaml
storage_backend:
  type: filesystem
  workspace_path: ".conductor_workspace"
  # connection_string será usado pelo mongodb no futuro
  # connection_string: "mongodb://localhost:27017/"

tool_plugins:
  # - "/path/to/my/custom_tools/"
```

**2. Modificar `src/config.py` (assumindo a existência de `ConfigManager`):**

```python
# Em src/config.py
class InvalidConfigurationError(Exception):
    pass

class ConfigManager:
    # ... (métodos existentes)
    def load_storage_config(self) -> Dict:
        """Carrega e valida a seção storage_backend do config.yaml."""
        # Implementar a lógica para:
        # 1. Ler o config.yaml.
        # 2. Validar a presença de 'storage_backend' e 'type'.
        # 3. Validar se 'type' é 'filesystem' ou 'mongodb'.
        # 4. Levantar InvalidConfigurationError se a validação falhar.
        # 5. Retornar a seção de configuração do armazenamento.
        pass
```

**3. Criar o arquivo `src/infrastructure/repository_factory.py`:**

```python
# src/infrastructure/repository_factory.py

from src.config import ConfigManager
from src.infrastructure.filesystem_storage import FileSystemStorage
# from src.infrastructure.mongodb_storage import MongoDbStorage # Será descomentado no próximo plano

class RepositoryFactory:
    @staticmethod
    def get_repository(config: Dict):
        """Cria e retorna a instância de repositório apropriada com base na configuração."""
        repo_type = config.get('type')
        if repo_type == 'filesystem':
            # Assumindo que o path está na config
            return FileSystemStorage(base_path=config.get('workspace_path'))
        elif repo_type == 'mongodb':
            # Lógica a ser implementada no próximo plano
            # return MongoDbStorage(...)
            raise NotImplementedError("MongoDB backend não está implementado ainda.")
        else:
            raise ValueError(f"Tipo de repositório desconhecido: {repo_type}")

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- O arquivo `config.yaml` foi criado na raiz do projeto.
- O `ConfigManager` foi atualizado para carregar e validar a configuração de armazenamento.
- O arquivo `repository_factory.py` e a `RepositoryFactory` foram criados conforme a especificação.
- O ponto de entrada da aplicação foi refatorado para usar a fábrica para injetar o repositório correto no `AgentService`.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
