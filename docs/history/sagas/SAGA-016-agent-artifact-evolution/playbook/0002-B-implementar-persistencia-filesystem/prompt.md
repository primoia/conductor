# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0002-B

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo deste plano é implementar a primeira **Estratégia de Persistência** concreta para nosso Modelo de Dados. Ao criar uma camada dedicada para o `filesystem`, desacoplamos a lógica de domínio de como os dados são salvos. Isso nos permite começar com uma solução simples, sem dependências externas, garantindo que o núcleo do sistema possa operar de forma autônoma, enquanto pavimentamos o caminho para estratégias mais complexas (como MongoDB) no futuro.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Separação de Camadas:** Toda a lógica de persistência para o filesystem **DEVE** residir em um novo arquivo em `src/infrastructure/filesystem_storage.py`. Isso reforça a barreira entre o domínio (o quê) e a infraestrutura (como).
- **Interface Implícita:** A classe `FileSystemStorage` deve expor métodos públicos (ex: `load_definition`, `save_definition`) que formarão uma "interface implícita". Futuros provedores de armazenamento (MongoDB) implementarão os mesmos métodos, permitindo que sejam trocados sem alterar o código que os consome.
- **Serialização Padrão:** A serialização para arquivos **DEVE** usar formatos padrão e legíveis por humanos: `YAML` para arquivos de configuração (`definition.yaml`, `playbook.yaml`) e `JSON` para arquivos de dados (`knowledge.json`, `session.json`). O `history.log` **DEVE** usar o formato `JSON Lines`.
- **Manipulação Segura de Arquivos:** O código **DEVE** usar `pathlib.Path` para manipulação de caminhos e garantir que os diretórios existam antes de tentar escrever arquivos (`os.makedirs(exist_ok=True)` ou `Path.mkdir(parents=True, exist_ok=True)`).

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um único arquivo, `src/infrastructure/filesystem_storage.py`. O arquivo **DEVE** conter o esqueleto de classe e os métodos definidos abaixo. Você será responsável por implementar a lógica interna de cada método.

```python
# src/infrastructure/filesystem_storage.py

import json
import yaml
from pathlib import Path
from typing import List

from src.core.domain import (
    AgentDefinition, AgentPersona, AgentPlaybook, AgentKnowledge, HistoryEntry, AgentSession
)

class FileSystemStorage:
    """
    Implementa a persistência de artefatos de agente usando o sistema de arquivos local.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        # Garante que o diretório base do agente exista.
        self.base_path.mkdir(parents=True, exist_ok=True)

    def load_definition(self) -> AgentDefinition:
        """Carrega a definição do agente de definition.yaml."""
        # Implementar a lógica de leitura e parsing do YAML.
        pass

    def save_definition(self, definition: AgentDefinition):
        """Salva a definição do agente em definition.yaml."""
        # Implementar a lógica de serialização para YAML e escrita.
        pass

    def load_persona(self) -> AgentPersona:
        """Carrega a persona do agente de persona.md."""
        # Implementar a lógica de leitura do arquivo de texto.
        pass

    def save_persona(self, persona: AgentPersona):
        """Salva a persona do agente em persona.md."""
        # Implementar a lógica de escrita no arquivo de texto.
        pass

    def load_playbook(self) -> AgentPlaybook:
        """Carrega o playbook do agente de playbook.yaml."""
        # Implementar a lógica de leitura e parsing do YAML.
        pass

    def save_playbook(self, playbook: AgentPlaybook):
        """Salva o playbook do agente em playbook.yaml."""
        # Implementar a lógica de serialização para YAML e escrita.
        pass

    def load_knowledge(self) -> AgentKnowledge:
        """Carrega o conhecimento do agente de knowledge.json."""
        # Implementar a lógica de leitura e parsing do JSON.
        pass

    def save_knowledge(self, knowledge: AgentKnowledge):
        """Salva o conhecimento do agente em knowledge.json."""
        # Implementar a lógica de serialização para JSON e escrita.
        pass

    def load_history(self) -> List[HistoryEntry]:
        """Carrega o histórico de um agente a partir de history.log (JSON Lines)."""
        # Implementar a lógica de leitura linha por linha e parsing do JSON.
        pass

    def append_to_history(self, entry: HistoryEntry):
        """Adiciona uma nova entrada ao final de history.log (JSON Lines)."""
        # Implementar a lógica de serialização para JSON e escrita em modo 'append'.
        pass
    
    def load_session(self) -> AgentSession:
        """Carrega a sessão de session.json."""
        # Implementar a lógica de leitura e parsing do JSON.
        pass

    def save_session(self, session: AgentSession):
        """Salva a sessão em session.json."""
        # Implementar a lógica de serialização para JSON e escrita.
        pass

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho será considerado concluído quando o arquivo `src/infrastructure/filesystem_storage.py` for criado e contiver a classe `FileSystemStorage` com todos os métodos especificados acima, incluindo assinaturas de tipo corretas. A implementação interna de cada método deve manipular corretamente os arquivos e formatos de dados conforme especificado.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
