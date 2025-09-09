# Plano: 0007-G - Segurança: Configuração Granular de Ferramentas

## Contexto

Agora que as ferramentas podem ser carregadas dinamicamente, precisamos de um mecanismo de segurança para restringir o que elas podem fazer. Este plano implementa a seção `tool_config` do `config.yaml`, que permite, por exemplo, definir uma lista de comandos permitidos para a ferramenta `shell.run`.

O objetivo é modificar o `ToolManager` ou criar um `ToolExecutor` que, antes de executar uma ferramenta, verifique se existem regras de configuração para ela e valide a chamada com base nessas regras.

## Checklist de Verificação

- [ ] Modificar o `ConfigManager` para carregar e validar a seção `tool_config` do `config.yaml`.
- [ ] Criar uma estrutura de dados (ex: uma `dataclass`) para representar a configuração de uma ferramenta (ex: `ToolSecurityConfig`).
- [ ] Criar (ou modificar) uma classe `ToolExecutor` responsável por executar uma ferramenta.
- [ ] O `ToolExecutor` deve receber o `ToolManager` e a `AppConfig` no seu construtor.
- [ ] Antes de executar uma ferramenta (ex: `shell.run`), o `ToolExecutor` deve:
    1. Verificar se existe uma entrada para `shell.run` em `config.tool_config`.
    2. Se existir, extrair a lista de `allowed_commands`.
    3. Validar se o comando que o agente está tentando executar está presente na lista de permitidos.
    4. Lançar uma exceção de segurança (`SecurityViolationError`) se a validação falhar.
- [ ] Refatorar a lógica de execução do agente para usar o `ToolExecutor` em vez de chamar diretamente as funções das ferramentas.
- [ ] Adicionar um exemplo de configuração para `shell.run` no `config.yaml` da raiz do projeto.
