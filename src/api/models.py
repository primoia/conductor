# src/api/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

# Squads válidos para agentes (1 agente pode pertencer a N squads)
VALID_SQUADS = [
    'development',    # Desenvolvimento & Arquitetura
    'crm',            # CRM & Vendas
    'content',        # Conteudo & Redes Sociais
    'documentation',  # Documentacao Tecnica
    'devops',         # DevOps & Seguranca
    'orchestration',  # Orquestracao & Meta-Agentes
    'testing',        # Testes & Qualidade
    'career',         # Carreira & Profissional
    'other',          # Outros
]

# Backward compat alias
VALID_GROUPS = VALID_SQUADS

class AgentSummary(BaseModel):
    """Modelo para listagem de agentes"""
    id: str = Field(..., description="agent_id - identificador único do agente")
    name: str = Field(..., description="Nome de exibição do agente")
    emoji: str = Field(default="🤖", description="Emoji do agente")
    description: str = Field(default="", description="Descrição curta do agente")
    group: str = Field(default="other", description="Grupo principal (backward compat)")
    squads: List[str] = Field(default_factory=lambda: ["other"], description="Squads do agente (1:N)")
    tags: List[str] = Field(default_factory=list, description="Tags para busca")
    created_at: Optional[str] = Field(default=None, description="Data de criação do agente (ISO format)")

class AgentListResponse(BaseModel):
    """Modelo baseado na estrutura atual da API"""
    total: int = Field(..., description="Total de agentes encontrados")
    agents: List[AgentSummary] = Field(..., description="Lista de agentes")

class AgentDetailResponse(BaseModel):
    """Modelo para detalhes completos do agente"""
    name: str
    version: str
    schema_version: str
    description: str
    author: str
    tags: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    agent_id: Optional[str] = None
    ai_provider: Optional[str] = None
    mcp_configs: List[str] = Field(default_factory=list, description="List of MCP names (e.g., ['prospector', 'database'])")
    emoji: Optional[str] = None
    color: Optional[str] = None

class AgentCreationRequest(BaseModel):
    """Modelo normalizado para criação de novo agente (web e terminal)"""
    name: str = Field(..., description="Nome do agente (deve terminar com _Agent)")
    description: str = Field(..., min_length=10, max_length=200, description="Descrição do propósito do agente (10-200 chars)")
    group: Optional[str] = Field(None, description="(deprecated) Use 'squads' instead. Kept for backward compat.")
    squads: List[str] = Field(default_factory=lambda: ["other"], description="Squads do agente. Valores: development, crm, content, documentation, devops, orchestration, testing, career, other")
    emoji: str = Field(default="🤖", description="Emoji representativo")
    tags: List[str] = Field(default_factory=list, description="Tags para busca e organização")
    persona_content: str = Field(..., min_length=50, description="Persona do agente em Markdown (mín 50 chars, deve começar com #)")
    mcp_configs: List[str] = Field(default_factory=list, description="Lista de sidecars MCP habilitados")

class AgentUpdateRequest(BaseModel):
    """Modelo para atualização de agente existente"""
    name: Optional[str] = Field(None, description="Nome de exibição do agente")
    description: Optional[str] = Field(None, min_length=10, max_length=200, description="Descrição do agente (10-200 chars)")
    group: Optional[str] = Field(None, description="(deprecated) Use 'squads' instead")
    squads: Optional[List[str]] = Field(None, description="Squads do agente (1:N)")
    emoji: Optional[str] = Field(None, description="Emoji representativo")
    tags: Optional[List[str]] = Field(None, description="Tags para busca e organização")
    persona_content: Optional[str] = Field(None, min_length=50, description="Persona do agente em Markdown")
    mcp_configs: Optional[List[str]] = Field(None, description="Lista de sidecars MCP habilitados")


class ValidationResult(BaseModel):
    """Modelo para resultado de validação"""
    is_valid: bool = Field(..., description="Se o agente é válido")
    errors: List[str] = Field(default_factory=list, description="Lista de erros encontrados")
    warnings: List[str] = Field(default_factory=list, description="Lista de avisos")
    agent_id: str = Field(..., description="ID do agente validado")


# ============================================================================
# Observation Models - Para injeção de estado dinâmico via Task Observations
# ============================================================================

class ObservationSubscribeRequest(BaseModel):
    """Request para inscrever agente em uma task"""
    capability: str = Field(..., description="Nome semântico da capability (ex: 'observability')")
    project_id: int = Field(..., description="ID do projeto no Construction PM")
    task_id: int = Field(..., description="ID da task a observar")
    description: str = Field(default="", description="Descrição para contexto")
    include_subtasks: bool = Field(default=False, description="Se deve incluir detalhes de subtasks")


class ObservationEntry(BaseModel):
    """Uma observação individual de um agente"""
    capability: str = Field(..., description="Nome semântico da capability")
    project_id: int = Field(..., description="ID do projeto no Construction PM")
    task_id: int = Field(..., description="ID da task observada")
    description: str = Field(default="", description="Descrição para contexto")
    include_subtasks: bool = Field(default=False, description="Se inclui subtasks")
    subscribed_at: str = Field(..., description="Data de inscrição (ISO format)")


class ObservationSubscribeResponse(BaseModel):
    """Response de inscrição em task"""
    status: str = Field(..., description="Status da operação")
    agent_id: str = Field(..., description="ID do agente")
    observation: ObservationEntry = Field(..., description="Observação criada")


class ObservationUnsubscribeResponse(BaseModel):
    """Response de remoção de inscrição"""
    status: str = Field(..., description="Status da operação")
    agent_id: str = Field(..., description="ID do agente")
    task_id: int = Field(..., description="ID da task removida")


class ObservationListResponse(BaseModel):
    """Lista de observações de um agente"""
    agent_id: str = Field(..., description="ID do agente")
    observations: List[ObservationEntry] = Field(default_factory=list, description="Lista de observações")
    count: int = Field(..., description="Total de observações")


class SubtaskState(BaseModel):
    """Estado de uma subtask"""
    id: int = Field(..., description="ID da subtask")
    name: str = Field(..., description="Nome da subtask")
    progress: int = Field(..., description="Progresso (0-100)")
    status: str = Field(..., description="Status da subtask")


class CapabilitySource(BaseModel):
    """Fonte de dados de uma capability"""
    project_id: int = Field(..., description="ID do projeto")
    task_id: int = Field(..., description="ID da task")
    task_name: str = Field(default="", description="Nome da task")


class CapabilityState(BaseModel):
    """Estado de uma capability observada"""
    name: str = Field(..., description="Nome da capability")
    progress: int = Field(..., description="Progresso (0-100)")
    status: str = Field(..., description="Status (not_started, in_progress, completed, delayed, blocked)")
    description: str = Field(default="", description="Descrição da capability")
    source: CapabilitySource = Field(..., description="Fonte dos dados")
    subtasks: Optional[List[SubtaskState]] = Field(default=None, description="Lista de subtasks (se include_subtasks=true)")
    summary: str = Field(default="", description="Resumo textual do estado")


class AgentWorldStateResponse(BaseModel):
    """Estado consolidado do mundo para um agente"""
    agent_id: str = Field(..., description="ID do agente")
    timestamp: str = Field(..., description="Timestamp da consulta (ISO format)")
    capabilities: List[CapabilityState] = Field(default_factory=list, description="Lista de capabilities observadas")