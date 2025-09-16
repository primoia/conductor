# Guide: Creating Tool Plugins

Conductor's architecture is designed to be extensible. You can add your own custom tools (plugins) without modifying the main source code.

## 1. The Concept

Conductor has two types of tools:
-   **Core Tools:** Essential tools that come with the system.
-   **Tool Plugins:** Tools that you create and register in a custom directory.

## 2. Creating Your Plugin

### Step 1: Create a Plugin Directory
Create a new directory anywhere within your project. For example:
`custom_tools/`

### Step 2: Create the Tool Module
Inside your new directory, create a Python file. The file name will be the module name.
`custom_tools/my_api_tools.py`

### Step 3: Write and Export Your Tools
Inside your file, write your tools as Python functions. Then, add the function names to a special list called `PLUGIN_TOOLS`.

```python
# custom_tools/my_api_tools.py
import requests

def get_weather(city: str) -> str:
    """Fetches the current weather for a city."""
    # (API call implementation)
    return f"The weather in {city} is sunny."

# The convention is to export the tools in a list
PLUGIN_TOOLS = [get_weather]
```

## 3. Registering Your Plugin

The final step is to tell Conductor where to find your new plugin. Open `config.yaml` and add the path to your plugin directory to the `tool_plugins` list.

```yaml
# config.yaml
storage:
  type: filesystem
  path: .conductor_workspace

tool_plugins:
  - custom_tools/
  - other_plugins/another_set_of_tools/
```

The next time Conductor starts, it will scan the `custom_tools/` directory, import the `my_api_tools` module, and the `get_weather` tool will be available to any agent that has permission to use it in its `agent.yaml`.

## 4. Security Considerations

**IMPORTANT NOTICE:** The plugin functionality dynamically loads and executes Python code.

-   **Trust:** **NEVER** add a plugin path from a source you do not fully trust. Doing so can lead to the execution of malicious code.
-   **Scope:** As a security measure, Conductor will only load plugins from directories that are inside the project folder.