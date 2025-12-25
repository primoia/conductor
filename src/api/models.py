# src/api/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentSummary(BaseModel):
    """Modelo baseado na resposta atual do endpoint /agents"""
    id: str = Field(..., description="ID único do agente")
    name: str = Field(..., description="Nome de exibição do agente")

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
    emoji: str = Field(default="🤖", description="Emoji representativo")
    tags: List[str] = Field(default_factory=list, description="Tags para busca e organização")
    persona_content: str = Field(..., min_length=50, description="Persona do agente em Markdown (mín 50 chars, deve começar com #)")
    mcp_configs: List[str] = Field(default_factory=list, description="Lista de sidecars MCP habilitados")

class ValidationResult(BaseModel):
    """Modelo para resultado de validação"""
    is_valid: bool = Field(..., description="Se o agente é válido")
    errors: List[str] = Field(default_factory=list, description="Lista de erros encontrados")
    warnings: List[str] = Field(default_factory=list, description="Lista de avisos")
    agent_id: str = Field(..., description="ID do agente validado")