# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0005-E

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é implementar uma **Estratégia de Persistência** escalável e robusta usando MongoDB. Isso permite que o Conductor transcenda as limitações de um único sistema de arquivos, possibilitando a operação em ambientes distribuídos, o gerenciamento de um número muito maior de agentes e o aproveitamento de recursos avançados de banco de dados, como consultas complexas, indexação e backups gerenciados.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Separação de Camadas:** A lógica de persistência para MongoDB **DEVE** residir em um novo arquivo em `src/infrastructure/mongodb_storage.py`.
- **Interface Implícita:** A classe `MongoDbStorage` **DEVE** implementar a mesma "interface implícita" da `FileSystemStorage`, com os mesmos nomes de métodos e assinaturas. Isso é crucial para que a `RepositoryFactory` possa trocá-los de forma transparente.
- **Estrutura de Coleções:** A persistência **DEVE** usar uma estrutura de coleções normalizada:
    - Uma coleção `agents` para o documento principal de cada agente (contendo `definition`, `persona`, `playbook`, `knowledge`).
    - Uma coleção `history` para armazenar `HistoryEntry` como documentos individuais, ligados por um `agent_id`.
    - Uma coleção `sessions` para armazenar `AgentSession`, que **DEVE** ter um índice TTL para expiração automática.
- **Dependência Externa:** A biblioteca `pymongo` **DEVE** ser adicionada como uma dependência do projeto.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Adicionar `pymongo` às dependências (ex: em `pyproject.toml`):**
```toml
[tool.poetry.dependencies]
...
pymongo = "^4.3"
...
```

**2. Criar o arquivo `src/infrastructure/mongodb_storage.py`:**
```python
# src/infrastructure/mongodb_storage.py

from typing import List
from pymongo import MongoClient

from src.core.domain import (
    AgentDefinition, AgentPersona, AgentPlaybook, AgentKnowledge, HistoryEntry, AgentSession
)

class MongoDbStorage:
    def __init__(self, connection_string: str, db_name: str = "conductor"):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.agents_collection = self.db["agents"]
        self.history_collection = self.db["history"]
        self.sessions_collection = self.db["sessions"]
        # Criar índice TTL na coleção de sessões, se não existir
        # self.sessions_collection.create_index("createdAt", expireAfterSeconds=86400)

    # Implementar todos os mesmos métodos públicos que FileSystemStorage
    # Exemplo:
    def load_definition(self, agent_name: str) -> AgentDefinition:
        """Carrega a definição de um agente a partir do MongoDB."""
        # Lógica para encontrar o documento do agente e extrair a sub-seção 'definition'.
        pass

    def save_definition(self, agent_name: str, definition: AgentDefinition):
        """Salva (ou atualiza) a definição de um agente no MongoDB."""
        # Lógica para usar 'update_one' com '$set' para atualizar a definição.
        pass
    
    # ... e assim por diante para todos os outros métodos:
    # load_persona, save_persona, load_playbook, save_playbook,
    # load_knowledge, save_knowledge, load_history, append_to_history,
    # load_session, save_session

```

**3. Atualizar `src/infrastructure/repository_factory.py`:**

```python
# Em repository_factory.py
# Descomentar a importação
from src.infrastructure.mongodb_storage import MongoDbStorage

# Na classe RepositoryFactory
# ...
        elif repo_type == 'mongodb':
            return MongoDbStorage(
                connection_string=config.get('connection_string'),
                db_name=config.get('db_name', 'conductor')
            )
# ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- `pymongo` foi adicionado como dependência.
- O arquivo `mongodb_storage.py` foi criado com a classe `MongoDbStorage` e todos os métodos necessários.
- A `RepositoryFactory` foi atualizada para instanciar e retornar `MongoDbStorage` quando apropriado.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
