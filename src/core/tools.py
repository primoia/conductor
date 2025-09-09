# src/core/tools.py

def tool(func):
    """
    Decorador para marcar uma função como uma ferramenta registrável pelo ToolManager.
    """
    setattr(func, '_is_tool', True)
    return func