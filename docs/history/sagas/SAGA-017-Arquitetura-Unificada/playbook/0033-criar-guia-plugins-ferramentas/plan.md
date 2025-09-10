### Plano de Execução: Estágio 33 - Criar Guia de Plugins de Ferramentas

#### Contexto Arquitetônico

Uma das capacidades mais poderosas da nova arquitetura é a extensibilidade através de "Tool Plugins". No entanto, essa funcionalidade é inútil se os usuários não souberem como criar e registrar suas próprias ferramentas. Atualmente, não há documentação que explique este processo.

#### Propósito Estratégico

O objetivo é capacitar os usuários e contribuidores a estender o Conductor. Um guia claro e prático sobre como criar um plugin de ferramenta reduz a barreira de entrada, incentiva a contribuição da comunidade e permite que as equipes adaptem o Conductor às suas necessidades específicas. Isso é fundamental para a visão do Conductor como um framework, e não apenas como uma aplicação.

#### Checklist de Execução

- [ ] Criar um novo arquivo em `docs/guides/creating_tool_plugins.md`.
- [ ] O guia deve começar com uma explicação conceitual do que são as Core Tools e os Tool Plugins.
- [ ] Fornecer um exemplo passo a passo de como criar um novo diretório de plugin (ex: `my_custom_tools/`).
- [ ] Mostrar um exemplo de código para um arquivo de ferramenta dentro do plugin (ex: `my_custom_tools/api_tools.py`).
- [ ] Explicar a convenção de exportar uma lista `PLUGIN_TOOLS` no módulo.
- [ ] Mostrar como registrar o novo diretório de plugin no `config.yaml`.
- [ ] Incluir a seção de "Segurança" que foi planejada no Estágio 24, alertando sobre os riscos.
