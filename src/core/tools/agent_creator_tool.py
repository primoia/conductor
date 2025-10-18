# src/core/tools/agent_creator_tool.py
import json
import logging
import os
import yaml
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from src.core.domain import AgentDefinition, AgentPersona

logger = logging.getLogger(__name__)


def _detect_storage_config() -> Dict[str, Any]:
    """Detecta configuração de storage do config.yaml."""
    try:
        config_path = os.path.join(os.getcwd(), 'config.yaml')
        logger.info(f"🔍 Lendo configuração de: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        storage_config = config.get('storage', {})
        logger.info(f"📦 Storage config detectado: {storage_config}")
        return storage_config

    except Exception as e:
        logger.warning(f"⚠️ Erro ao ler config.yaml: {e}, usando filesystem como padrão")
        return {'type': 'filesystem', 'path': '.conductor_workspace'}


def _create_storage():
    """Factory que cria storage baseado na configuração atual."""
    config = _detect_storage_config()
    storage_type = config.get('type', 'filesystem')

    if storage_type == 'mongodb':
        logger.info("🍃 Criando MongoDB storage")
        from src.infrastructure.mongodb_storage import MongoDbStorage
        from dotenv import load_dotenv

        # Carregar variáveis de ambiente do .env
        load_dotenv()

        # Usar variáveis de ambiente do .env ou config padrão
        connection_string = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        db_name = os.getenv('MONGO_DATABASE', 'conductor_state')

        logger.info(f"🔗 Conectando MongoDB: {connection_string}")
        logger.info(f"📊 Database: {db_name}")

        return MongoDbStorage(connection_string=connection_string, db_name=db_name)

    else:
        logger.info("📁 Criando Filesystem storage")
        from src.infrastructure.filesystem_storage import FileSystemStorage

        storage_path = config.get('path', '.conductor_workspace')
        return FileSystemStorage(base_path=storage_path)


class AgentCreationRequest(BaseModel):
    """Pydantic model para criação de agentes - garante JSON perfeito da LLM."""

    name: str = Field(..., description="Nome do agente (ex: 'MongoDBKotlin_Agent')")
    description: str = Field(..., description="Descrição clara do que o agente faz")
    capabilities: List[str] = Field(..., description="Lista de capacidades do agente")
    tags: List[str] = Field(..., description="Tags para categorizar o agente")
    persona_content: str = Field(..., description="Conteúdo da persona em Markdown")
    author: str = Field(default="PrimoIA", description="Autor do agente")
    version: str = Field(default="1.0.0", description="Versão do agente")
    allowed_tools: List[str] = Field(default_factory=list, description="Ferramentas permitidas")

    @validator('name')
    def validate_name(cls, v):
        """Valida formato do nome do agente."""
        if not v.endswith('_Agent'):
            raise ValueError("Nome deve terminar com '_Agent' (ex: 'MongoDBExpert_Agent')")
        if ' ' in v:
            raise ValueError("Nome não pode conter espaços, use underscore")
        if not v.replace('_', '').replace('Agent', '').isalnum():
            raise ValueError("Nome deve conter apenas letras, números e underscore")
        return v

    @validator('description')
    def validate_description(cls, v):
        """Valida descrição."""
        if len(v) < 10:
            raise ValueError("Descrição deve ter pelo menos 10 caracteres")
        if len(v) > 200:
            raise ValueError("Descrição deve ter no máximo 200 caracteres")
        return v

    @validator('capabilities')
    def validate_capabilities(cls, v):
        """Valida capacidades."""
        if not v:
            raise ValueError("Deve ter pelo menos uma capacidade")
        if len(v) > 10:
            raise ValueError("Máximo 10 capacidades permitidas")
        return v

    @validator('persona_content')
    def validate_persona(cls, v):
        """Valida conteúdo da persona."""
        if len(v) < 50:
            raise ValueError("Persona deve ter pelo menos 50 caracteres")
        if not v.strip().startswith('#'):
            raise ValueError("Persona deve começar com um cabeçalho Markdown (#)")
        return v


def create_agent(json_data: str) -> Dict[str, Any]:
    """
    Ferramenta para criar novos agentes de forma padronizada.

    Funciona com filesystem OU MongoDB automaticamente.
    Usa validação Pydantic para garantir dados corretos.

    Args:
        json_data: JSON string com os dados do agente

    Returns:
        Dict com resultado da operação

    Example:
        json_data = '''
        {
            "name": "MongoDBKotlin_Agent",
            "description": "Especialista em MongoDB com Kotlin",
            "capabilities": ["mongodb_queries", "kotlin_development"],
            "tags": ["mongodb", "kotlin", "database"],
            "persona_content": "# Especialista MongoDB\\n\\nVocê é um expert..."
        }
        '''
    """
    logger.info("🛠️ create_agent() chamada")
    logger.info(f"📥 JSON recebido: {json_data[:200]}{'...' if len(json_data) > 200 else ''}")

    try:
        # 1. Parse JSON
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro de parsing JSON: {str(e)}")
            return {
                "success": False,
                "error": "JSON_PARSE_ERROR",
                "message": f"JSON inválido: {str(e)}",
                "hint": "Verifique se o JSON está bem formado com aspas duplas"
            }

        # 2. Validar com Pydantic
        try:
            request = AgentCreationRequest(**data)
            logger.info(f"✅ Validação Pydantic OK para agente: {request.name}")
        except Exception as e:
            logger.error(f"❌ Erro de validação Pydantic: {str(e)}")
            return {
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": f"Dados inválidos: {str(e)}",
                "hint": "Corrija os dados e tente novamente"
            }

        # 3. Criar objetos de domínio tipados
        agent_definition = AgentDefinition(
            name=request.name,
            version=request.version,
            schema_version="1.0",
            description=request.description,
            author=request.author,
            tags=request.tags,
            capabilities=request.capabilities,
            allowed_tools=request.allowed_tools
        )

        agent_persona = AgentPersona(content=request.persona_content)

        # 4. Salvar usando storage unificado (funciona com filesystem OU MongoDB)
        try:
            logger.info("🏗️ Criando storage baseado na configuração atual")
            storage = _create_storage()
            logger.info(f"📦 Storage criado: {type(storage).__name__}")

            # Verificar se agente já existe
            try:
                storage.load_definition(request.name)
                logger.warning(f"⚠️ Agente '{request.name}' já existe")
                return {
                    "success": False,
                    "error": "AGENT_EXISTS",
                    "message": f"Agente '{request.name}' já existe",
                    "hint": "Use um nome diferente ou delete o agente existente"
                }
            except FileNotFoundError:
                logger.info(f"✅ Agente '{request.name}' não existe, pode criar")
                pass  # Agente não existe, pode criar

            # Salvar definition e persona
            logger.info(f"💾 Salvando definition para: {request.name}")
            storage.save_definition(request.name, agent_definition)
            logger.info(f"💾 Salvando persona para: {request.name}")
            storage.save_persona(request.name, agent_persona)

            # Detectar tipo de storage baseado na configuração
            config = _detect_storage_config()
            storage_type = "MongoDB" if config.get('type') == 'mongodb' else "Filesystem"

            logger.info(f"🎉 Agente '{request.name}' criado com sucesso no {storage_type}!")
            return {
                "success": True,
                "agent_id": request.name,
                "message": f"Agente '{request.name}' criado com sucesso!",
                "storage_type": storage_type
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar no storage: {str(e)}")
            return {
                "success": False,
                "error": "STORAGE_ERROR",
                "message": f"Erro ao salvar agente: {str(e)}",
                "hint": "Verifique conectividade do banco ou permissões de arquivo"
            }

    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        return {
            "success": False,
            "error": "UNEXPECTED_ERROR",
            "message": f"Erro inesperado: {str(e)}",
            "hint": "Contacte o suporte se o erro persistir"
        }


def get_agent_creation_schema() -> str:
    """Retorna o schema JSON para a LLM usar."""
    logger.info("📋 get_agent_creation_schema() chamada")
    schema = AgentCreationRequest.schema()
    logger.info(f"✅ Schema gerado com {len(schema)} campos")
    return json.dumps(schema, indent=2)


# Registrar ferramenta
AGENT_CREATION_TOOLS = [create_agent, get_agent_creation_schema]

# Exportar funções públicas
__all__ = ['create_agent', 'get_agent_creation_schema', 'AGENT_CREATION_TOOLS']