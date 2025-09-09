# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0003-C

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é criar uma **Fachada de Serviço** (`Service Facade`) para a lógica de carregamento de agentes. Em vez de o código cliente precisar saber como instanciar um `FileSystemStorage` e chamar seis métodos diferentes (`load_definition`, `load_persona`, etc.), ele simplesmente chamará um único método `agent_service.load_agent_instance()`. Isso encapsula a complexidade, simplifica o código cliente e cria um ponto central para adicionar lógica futura, como caching ou validação.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Separação de Camadas:** A nova `AgentService` **DEVE** residir em `src/core/agent_service.py`, pois contém a lógica de coordenação do domínio. A nova `AgentInstance` **DEVE** ser adicionada a `src/core/domain.py`, pois faz parte do nosso modelo de dados canônico.
- **Injeção de Dependência:** A `AgentService` **NÃO DEVE** instanciar seu próprio repositório de armazenamento. Em vez disso, ela **DEVE** receber uma instância de um repositório (como `FileSystemStorage`) em seu construtor. Isso é crucial para a testabilidade e para permitir a troca de backends de armazenamento.
- **Tratamento de Erros:** O serviço **DEVE** implementar um tratamento de erro básico. Se um agente solicitado não for encontrado no armazenamento, o serviço deve levantar uma exceção clara e específica (ex: `AgentNotFoundError`).

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar `src/core/domain.py` e criar um novo arquivo `src/core/agent_service.py`.

**1. Adicionar ao arquivo `src/core/domain.py`:**

```python
# No final do arquivo src/core/domain.py

@dataclass(frozen=True)
class AgentInstance:
    """
    Representa um agente totalmente carregado em memória, com todos os seus artefatos.
    """
    definition: AgentDefinition
    persona: AgentPersona
    playbook: AgentPlaybook
    knowledge: AgentKnowledge
    history: List[HistoryEntry]
```

**2. Criar o arquivo `src/core/agent_service.py`:**

```python
# src/core/agent_service.py

from src.core.domain import AgentInstance
# A classe de armazenamento será usada como uma interface, então importamos para type hinting
from src.infrastructure.filesystem_storage import FileSystemStorage 

class AgentNotFoundError(Exception):
    pass

class AgentService:
    def __init__(self, storage_repository):
        # Usamos um nome genérico para a dependência, pois pode ser qualquer tipo de armazenamento
        self.storage = storage_repository

    def load_agent_instance(self, agent_name: str) -> AgentInstance:
        """
        Orquestra o carregamento completo de uma instância de agente a partir do repositório.
        """
        # Implementar a lógica que:
        # 1. Usa o self.storage para carregar cada artefato individualmente.
        # 2. Constrói e retorna um objeto AgentInstance com os artefatos carregados.
        # 3. Levanta AgentNotFoundError se o agente não for encontrado.
        pass
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- A `dataclass AgentInstance` foi adicionada corretamente ao `src/core/domain.py`.
- O arquivo `src/core/agent_service.py` foi criado.
- A classe `AgentService` e a exceção `AgentNotFoundError` foram implementadas conforme a especificação.
- O método `load_agent_instance` chama corretamente os métodos do repositório injetado para construir e retornar um `AgentInstance`.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
