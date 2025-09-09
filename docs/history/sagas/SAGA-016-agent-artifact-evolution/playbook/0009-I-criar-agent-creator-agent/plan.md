# Plano: 0009-I - Meta-Agentes: `AgentCreator_Agent`

## Contexto

Continuando a criação dos meta-agentes, este plano foca no `AgentCreator_Agent`. Este agente é responsável por criar o scaffolding (a estrutura de diretórios e arquivos iniciais) para um novo agente, a partir de um requisito de alto nível fornecido pelo usuário.

Ele usará as ferramentas de manipulação de arquivos para criar a pasta do agente e os arquivos `definition.yaml` e `persona.md` iniciais.

## Checklist de Verificação

- [x] Criar a estrutura de diretórios: `.conductor_workspace/agents/AgentCreator_Agent/`.
- [x] Criar o arquivo `definition.yaml` com `name`, `version`, `description`, `tags: ["meta", "onboarding"]`, `capabilities: ["create_agent_scaffold"]`.
- [x] Em `allowed_tools`, incluir `file.write` e `shell.run` (para `mkdir`).
- [x] Criar o arquivo `persona.md` que instrui o agente a:
    1. Receber uma descrição de um novo agente (ex: "Quero um agente que refatora código Kotlin").
    2. Extrair o nome, as capacidades e as tags dessa descrição.
    3. Gerar um `definition.yaml` básico com essas informações.
    4. Gerar uma `persona.md` inicial com uma estrutura padrão.
    5. Usar as ferramentas para criar a pasta e salvar os arquivos no workspace.
