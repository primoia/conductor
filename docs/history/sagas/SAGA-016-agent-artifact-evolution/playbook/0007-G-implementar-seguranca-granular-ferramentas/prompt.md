# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0007-G

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é implementar uma **Camada de Segurança (Policy Enforcement Layer)** para a execução de ferramentas. Com um sistema de plugins aberto, é fundamental ter um mecanismo centralizado que imponha políticas de segurança, garantindo o **Princípio do Privilégio Mínimo**. Este plano impede que os agentes executem operações perigosas (como comandos de shell arbitrários), permitindo que os operadores do sistema definam uma "lista de permissões" explícita para ferramentas de alto risco.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITO NÃO FUNCIONAL)**
- **Execução Centralizada:** A execução de todas as ferramentas **DEVE** passar por uma classe `ToolExecutor`. Os agentes não devem mais ter acesso direto ao registro de ferramentas do `ToolManager`.
- **Configuração de Políticas:** As políticas de segurança **DEVEM** ser definidas na seção `tool_config` do `config.yaml`, permitindo que a segurança seja configurada sem alterar o código.
- **Falha Segura:** Se uma política de segurança for violada, o `ToolExecutor` **DEVE** levantar uma exceção `SecurityViolationError` e interromper a execução. O sistema nunca deve "falhar aberto" e permitir a ação.
- **Separação de Camadas:** A nova classe `ToolExecutor` **DEVE** residir em `src/core/tool_executor.py`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Atualizar `config.yaml`:**
```yaml
# Em config.yaml
# ... (seções anteriores)

# Configuração de segurança granular para tools
tool_config:
  shell_run: # O nome da função da ferramenta
    allowed_commands: ["git", "ls", "cat", "npm", "pytest"]
```

**2. Criar o arquivo `src/core/tool_executor.py`:**
```python
# src/core/tool_executor.py

from typing import Dict, Callable

class SecurityViolationError(Exception):
    pass

class ToolExecutor:
    def __init__(self, tool_manager, config: Dict):
        self.tools: Dict[str, Callable] = tool_manager.tools
        self.config: Dict = config.get('tool_config', {})

    def execute(self, tool_name: str, **kwargs):
        """
        Executa uma ferramenta após verificar as políticas de segurança.
        """
        if tool_name not in self.tools:
            raise ValueError(f"Ferramenta '{tool_name}' não encontrada.")

        # Aplicar política de segurança específica para 'shell_run'
        if tool_name == 'shell_run':
            self._enforce_shell_policy(kwargs.get('command'))

        tool_func = self.tools[tool_name]
        return tool_func(**kwargs)

    def _enforce_shell_policy(self, command: str):
        """Verifica se o comando de shell é permitido pela política."""
        policy = self.config.get('shell_run', {})
        allowed = policy.get('allowed_commands')

        if allowed is None: # Se a chave 'allowed_commands' não existe, nada é permitido.
            raise SecurityViolationError("Execução de 'shell_run' não é permitida. Nenhuma 'allowed_commands' definida na política.")
        
        # O comando real pode ter argumentos (ex: "ls -la"). Verificamos o comando base.
        command_base = command.split()[0]
        if command_base not in allowed:
            raise SecurityViolationError(
                f"Comando de shell '{command_base}' não é permitido pela política de segurança."
            )

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- A seção `tool_config` foi adicionada ao `config.yaml`.
- O arquivo `tool_executor.py` e a classe `ToolExecutor` foram criados conforme a especificação.
- O método `execute` invoca corretamente a política de segurança antes de executar a ferramenta.
- A aplicação é refatorada para usar o `ToolExecutor` em vez de chamar as ferramentas diretamente.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
