# src/core/constants.py
"""
Constantes centralizadas do Conductor.
Centraliza paths, mensagens e configurações para evitar duplicação.
"""

class Paths:
    """Constantes de caminhos do sistema."""
    AGENTS_DIR = "agents"
    WORKSPACE_ROOT = ".conductor_workspace"
    CONFIG_FILE = "config.yaml"
    DEFINITION_FILE = "definition.yaml"
    PERSONA_FILE = "persona.md"
    SESSION_FILE = "session.json"
    KNOWLEDGE_FILE = "knowledge.json"
    HISTORY_FILE = "history.log"
    PLAYBOOK_FILE = "playbook.yaml"

class Messages:
    """Mensagens padronizadas do sistema."""
    AGENT_NOT_FOUND = "❌ Agente '{agent_id}' não encontrado em {location}"
    SUGGEST_SIMILAR = "💡 Agentes similares disponíveis: {suggestions}"
    USE_LIST_COMMAND = "📋 Use 'conductor list-agents' para ver todos os agentes disponíveis"
    EXECUTION_SUCCESS = "✅ Execução bem-sucedida:"
    EXECUTION_ERROR = "❌ Erro na execução:"
    CONFIG_VALID = "🎯 Configuração válida!"
    CONFIG_ERROR = "❌ Erro na validação: {error}"
    AGENTS_FOUND = "📊 Total: {count} agentes encontrados"
    NO_AGENTS_FOUND = "❌ Nenhum agente encontrado."
    CHECK_AGENTS_DIR = "💡 Verifique se há agentes em {location}"

class Defaults:
    """Valores padrão do sistema."""
    AGENT_VERSION = "1.0.0"
    SCHEMA_VERSION = "1.0"
    AGENT_AUTHOR = "Unknown"
    TIMEOUT_SECONDS = 600  # 10 minutes timeout for long-running operations
    MAX_SUGGESTIONS = 3
    SIMILARITY_THRESHOLD = 0.6

class Commands:
    """Comandos e subcomandos disponíveis."""
    LIST_AGENTS = "list-agents"
    EXECUTE = "execute"
    VALIDATE_CONFIG = "validate-config"
    INFO = "info"
    HEALTH = "health"

class AgentFields:
    """Campos válidos para AgentDefinition."""
    VALID_FIELDS = {
        'name', 'version', 'schema_version', 'description', 'author',
        'tags', 'capabilities', 'allowed_tools', 'ai_provider',
        'mcp_config', 'mcp_configs',  # MCP configuration fields
        'emoji', 'color'  # UI fields
    }
    REQUIRED_FIELDS = {
        'name', 'version', 'schema_version', 'description', 'author'
    }