# src/core/domain.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# Exceptions
class AgentNotEmbodied(Exception):
    """Raised when trying to interact with an agent that hasn't been embodied."""
    pass


class StateRepositoryError(Exception):
    """Raised when there are issues with the state repository."""
    pass


# Core data structures
@dataclass
class ConversationMessage:
    """A message in a conversation."""
    role: str
    content: str
    timestamp: Optional[str] = None


@dataclass
class AgentState:
    """Current state of an agent."""
    agent_id: str
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: str
    definition: 'AgentDefinition'
    settings: Dict[str, Any] = field(default_factory=dict)

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