# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0001-A

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa é a pedra angular da arquitetura da SAGA-016. Seu propósito é estabelecer um **Modelo de Dados Canônico** para todo o sistema Conductor. Ao criar uma fonte da verdade única, inequívoca e fortemente tipada para nossos conceitos centrais (Agente, Persona, Playbook, Conhecimento), nós eliminamos a inconsistência de dados e criamos uma fundação estável sobre a qual toda a persistência, lógica e serviços futuros serão construídos. Este é o passo mais crítico para garantir a manutenibilidade e a escalabilidade a longo prazo.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Separação de Camadas:** Todas as classes definidas neste plano representam o **Domínio** principal da aplicação. Como tal, elas **DEVEM** ser localizadas em um novo arquivo em `src/core/domain.py`. Nenhuma outra localização é aceitável.
- **Imutabilidade:** Todas as estruturas de dados **DEVEM** ser implementadas como `@dataclass(frozen=True)` do Python. Isso impõe a imutabilidade, um princípio central desta nova arquitetura para garantir um gerenciamento de estado previsível.
- **Clareza e Tipagem:** Todos os campos dentro das dataclasses **DEVEM** ter dicas de tipo explícitas importadas do módulo `typing`. Nenhum campo deve ficar sem tipo.
- **Sem Lógica de Negócios:** Estas classes são contêineres puros de dados. Elas **NÃO DEVEM** conter nenhum método ou lógica de negócios. Sua única responsabilidade é definir a forma de nossos dados.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um único arquivo, `src/core/domain.py`. O arquivo **DEVE** conter o seguinte conteúdo exatamente. Não adicione, remova ou altere nenhuma parte desta especificação.

```python
# src/core/domain.py

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass(frozen=True)
class AgentDefinition:
    """
    Representa a identidade estática e versionada de um agente. É o "plano de construção" do agente.
    """
    name: str
    version: str
    schema_version: str
    description: str
    author: str
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class AgentPersona:
    """
    Contém as instruções comportamentais para o LLM.
    """
    content: str

@dataclass(frozen=True)
class PlaybookBestPractice:
    """
    Uma única regra estruturada de "boa prática".
    """
    id: str
    title: str
    description: str

@dataclass(frozen=True)
class PlaybookAntiPattern:
    """
    Uma única regra estruturada de "anti-padrão" a ser evitado.
    """
    id: str
    title: str
    description: str

@dataclass(frozen=True)
class AgentPlaybook:
    """
    Uma coleção estruturada de regras e diretrizes para um agente.
    """
    best_practices: List[PlaybookBestPractice] = field(default_factory=list)
    anti_patterns: List[PlaybookAntiPattern] = field(default_factory=list)

@dataclass(frozen=True)
class KnowledgeItem:
    """
    Metadados sobre um único artefato gerenciado pelo agente.
    """
    summary: str
    purpose: str
    last_modified_by_task: str

@dataclass(frozen=True)
class AgentKnowledge:
    """
    A memória semântica do agente sobre os artefatos que ele gerencia.
    A chave do dicionário é o caminho do artefato.
    """
    artifacts: Dict[str, KnowledgeItem] = field(default_factory=dict)

@dataclass(frozen=True)
class HistoryEntry:
    """
    Uma entrada de log imutável de uma única tarefa concluída.
    """
    _id: str
    agent_id: str
    task_id: str
    status: str
    summary: str
    git_commit_hash: str

@dataclass(frozen=True)
class AgentSession:
    """
    O estado volátil da tarefa atual de um agente. É efêmero.
    """
    current_task_id: str
    state: Dict = field(default_factory=dict)

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho será considerado concluído **somente quando** o arquivo `src/core/domain.py` for criado e seu conteúdo for uma correspondência exata com o bloco de código fornecido na Especificação Técnica acima. O arquivo deve estar livre de quaisquer erros de sintaxe. Nenhum outro arquivo deve ser criado ou modificado.

#### **6. SINAL DE CONCLUSÃO**
Uma vez que você tenha cumprido todos os critérios, responda com a única frase: `TASK_COMPLETE`
