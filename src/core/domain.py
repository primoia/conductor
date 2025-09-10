# src/core/domain.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field as PydanticField


# Exceptions
class AgentNotEmbodied(Exception):
    """Raised when trying to interact with an agent that hasn't been embodied."""
    pass


class StateRepositoryError(Exception):
    """Raised when there are issues with the state repository."""
    pass


class ConfigurationError(Exception):
    """Raised when there are configuration issues."""
    pass


# Core data structures

@dataclass
class ConversationEntryDTO:
    """
    Unified conversation entry representing a user prompt and AI response pair.
    
    This DTO serves as the single source of truth for conversation history,
    replacing both the legacy {prompt, response, timestamp} format and the
    {role, content, timestamp} format.
    """
    user_input: str
    ai_response: str
    timestamp: Optional[float] = None
    
    @classmethod
    def from_legacy_format(cls, data: dict) -> 'ConversationEntryDTO':
        """Create from legacy {prompt, response, timestamp} format."""
        return cls(
            user_input=data["prompt"],
            ai_response=data["response"], 
            timestamp=data.get("timestamp")
        )
    
    def to_legacy_format(self) -> dict:
        """Convert to legacy {prompt, response, timestamp} format for LLM clients."""
        return {
            "prompt": self.user_input,
            "response": self.ai_response,
            "timestamp": self.timestamp
        }
    
    def to_messages_format(self) -> list:
        """Convert to list of separate role-based messages for modern LLM APIs."""
        messages = [
            {"role": "user", "content": self.user_input}
        ]
        if self.ai_response:
            messages.append({"role": "assistant", "content": self.ai_response})
        return messages
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_input": self.user_input,
            "ai_response": self.ai_response,
            "timestamp": self.timestamp
        }


@dataclass 
class ConversationMessage:
    """
    DEPRECATED: Use ConversationEntryDTO instead.
    Kept for backward compatibility during migration.
    """
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
    agent_id: Optional[str] = None  # Optional field for compatibility

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

@dataclass(frozen=True)
class TaskDTO:
    """
    Data Transfer Object para encapsular uma requisição de tarefa.
    """
    agent_id: str
    user_input: str
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TaskResultDTO:
    """
    Data Transfer Object para encapsular o resultado de uma tarefa executada.
    """
    status: str  # Ex: 'success', 'error'
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)

# --- Modelos de API (Pydantic) ---

class ExecuteTaskRequest(BaseModel):
    """
    Modelo para uma requisição de execução de tarefa via API.
    """
    agent_id: str = PydanticField(..., description="O ID do agente a ser executado.")
    user_input: str = PydanticField(..., description="O input/prompt do usuário para o agente.")
    context: Dict[str, Any] = PydanticField(default_factory=dict, description="Contexto adicional opcional para a tarefa.")

class TaskCreationResponse(BaseModel):
    """
    Modelo para a resposta imediata após a criação de uma tarefa.
    """
    task_id: str = PydanticField(..., description="O ID único da tarefa que foi iniciada.")
    status: str = PydanticField(default="pending", description="O status inicial da tarefa.")

class TaskStatusResponse(BaseModel):
    """
    Modelo para a resposta ao consultar o status de uma tarefa.
    """
    task_id: str = PydanticField(..., description="O ID da tarefa.")
    status: str = PydanticField(..., description="O status atual da tarefa (ex: pending, in_progress, success, error).")
    output: Optional[str] = PydanticField(default=None, description="A saída final da tarefa, se concluída.")
    metadata: Dict[str, Any] = PydanticField(default_factory=dict, description="Metadados adicionais sobre a execução.")