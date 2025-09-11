# Plano 007: Remover Lógica de Caminhos Legados do AdminCLI

## 1. Meta

Refatorar o `AdminCLI` para eliminar completamente qualquer lógica de caminhos hardcoded (como `_common`) e fazer com que ele dependa exclusivamente do `ConductorService` para toda a descoberta e carregamento de agentes. O CLI não deve ter conhecimento da estrutura de diretórios.

## 2. Problema

O `AdminCLI` ainda exibe e utiliza caminhos legados (`_common`) durante sua inicialização. Isso causa confusão e mantém uma dependência de uma estrutura de diretórios obsoleta, criando um comportamento de "cérebro dividido" onde a interface do CLI reporta uma coisa, enquanto o serviço de backend executa outra (a correta).

## 3. Resultado Esperado

O `AdminCLI` deve ser agnóstico à localização dos agentes. Ele apenas informa um `agent_id` ao `ConductorService` e confia que o serviço o encontrará.

**Checklist de Implementação:**

1.  **Refatorar `src/cli/admin.py`:**
    -   Remover a lógica no `__init__` que define `self.environment` e `self.project` como `"_common"` quando a flag `--meta` é usada.
    -   Remover o parâmetro `destination_path` e qualquer lógica associada a ele.
    -   Remover as linhas no `main()` que imprimem `Target: _common/agents/`. O CLI não deve mais exibir essa informação.
2.  **Simplificar `_build_enhanced_message`:**
    -   Remover as partes que adicionam `AGENT_ENVIRONMENT`, `AGENT_PROJECT`, e `DESTINATION_PATH` à mensagem. O contexto agora é gerenciado inteiramente pelo `ConductorService` e pelo estado do agente.

## 4. Regras e Restrições (Guardrails)

-   **PROIBIDO O USO DE `_common`:** O nome `_common` não deve mais existir no código do `AdminCLI`.
-   **CLI DEVE SER AGNÓSTICO:** O `AdminCLI` não deve construir, manipular ou ter conhecimento de nenhum caminho de sistema de arquivos relacionado aos agentes. Sua única responsabilidade é passar o `agent_id` para o `ConductorService`.

## 5. Critério de Aceitação Final

- Após a refatoração, a execução do comando `python -m src.cli.admin --meta --agent AgentCreator_Agent --repl` deve iniciar com sucesso, e o log de inicialização **não deve** mais conter a linha `Target: _common/agents/`.
- A execução de uma tarefa simples (ex: "olá") deve continuar funcionando normalmente.
