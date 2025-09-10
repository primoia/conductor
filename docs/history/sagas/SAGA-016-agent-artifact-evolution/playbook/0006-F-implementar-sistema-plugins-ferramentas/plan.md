# Plano: 0006-F - Core: Sistema de Extensibilidade (Tool Plugins)

## Contexto

Um dos pilares da nova arquitetura é a extensibilidade. Este plano foca na implementação do sistema de `tool_plugins`, que permite carregar módulos de ferramentas personalizadas de diretórios externos especificados no `config.yaml`.

O objetivo é criar um `ToolManager` que, durante a inicialização, inspeciona os diretórios de plugins, carrega dinamicamente os módulos Python e registra as ferramentas encontradas (funções marcadas com um decorador `@tool`) em um registro central.

## Checklist de Verificação

- [x] Criar um novo arquivo `src/core/tool_manager.py`.
- [x] No `tool_manager.py`, criar uma classe `ToolManager`.
- [x] O `ToolManager` deve ter um método `load_plugins_from_config(config: AppConfig)`.
- [x] O método `load_plugins_from_config` deve:
    1. Ler a lista de caminhos de `config.tool_plugins`.
    2. Para cada caminho, iterar sobre os arquivos `.py`.
    3. Usar `importlib` para carregar dinamicamente cada arquivo como um módulo.
    4. Inspecionar os membros de cada módulo em busca de funções que tenham um atributo especial (indicando que são uma ferramenta, por exemplo, `_is_tool = True`).
- [x] Criar um decorador `@tool` em um arquivo `src/core/tools.py` que simplesmente adiciona o atributo `_is_tool = True` à função decorada.
- [x] O `ToolManager` deve manter um registro (`Dict[str, Callable]`) de todas as ferramentas carregadas, mapeando o nome da ferramenta para a função.
- [x] Integrar a chamada `tool_manager.load_plugins_from_config()` no processo de inicialização da aplicação.
- [x] Criar um diretório de exemplo `custom_tools/` com um arquivo `my_tool.py` contendo uma função de exemplo decorada com `@tool` para fins de teste.
