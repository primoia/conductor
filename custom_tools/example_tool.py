# custom_tools/example_tool.py

from src.core.tools import tool

@tool
def say_hello(name: str) -> str:
    """Uma ferramenta de exemplo que retorna uma saudação."""
    return f"Hello, {name}!"