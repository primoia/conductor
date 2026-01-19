# src/api/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

# Grupos válidos para agentes
AgentGroup = Literal[
    'development',    # 🔧 Desenvolvimento & Arquitetura
    'crm',            # 📊 CRM & Vendas
    'documentation',  # 📝 Documentação & Conteúdo
    'devops',         # 🛡️ DevOps & Segurança
    'orchestration',  # 🎼 Orquestração & Meta-Agentes
    'testing',        # 🧪 Testes & Qualidade
    'career',         # 💼 Carreira & Profissional
    'other'           # 📦 Outros
]

VALID_GROUPS = ['development', 'crm', 'documentation', 'devops', 'orchestration', 'testing', 'career', 'other']

class AgentSummary(BaseModel):
    """Modelo para listagem de agentes"""
    id: str = Field(..., description="agent_id - identificador único do agente")
    name: str = Field(..., description="Nome de exibição do agente")
    emoji: str = Field(default="🤖", description="Emoji do agente")
    description: str = Field(default="", description="Descrição curta do agente")
    group: str = Field(default="other", description="Grupo/categoria do agente")
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
    group: str = Field(..., description="Grupo/categoria do agente (development, crm, documentation, devops, orchestration, testing, career, other)")
    emoji: str = Field(default="🤖", description="Emoji representativo")
    tags: List[str] = Field(default_factory=list, description="Tags para busca e organização")
    persona_content: str = Field(..., min_length=50, description="Persona do agente em Markdown (mín 50 chars, deve começar com #)")
    mcp_configs: List[str] = Field(default_factory=list, description="Lista de sidecars MCP habilitados")

class AgentUpdateRequest(BaseModel):
    """Modelo para atualização de agente existente"""
    name: Optional[str] = Field(None, description="Nome de exibição do agente")
    description: Optional[str] = Field(None, min_length=10, max_length=200, description="Descrição do agente (10-200 chars)")
    group: Optional[str] = Field(None, description="Grupo/categoria do agente")
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