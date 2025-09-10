# src/core/tools/core_tools.py
import datetime

def get_current_time() -> str:
    """Retorna a data e hora atuais no formato ISO."""
    return datetime.datetime.now().isoformat()

# Ferramentas são registradas em uma lista para fácil importação
CORE_TOOLS = [get_current_time]