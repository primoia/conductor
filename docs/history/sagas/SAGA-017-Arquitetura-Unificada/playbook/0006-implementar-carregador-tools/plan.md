### Plano de Execução: Estágio 6 - Implementação do Carregador de Ferramentas Híbrido

#### Contexto Arquitetônico

Uma capacidade central da SAGA-016 é a extensibilidade através de um sistema de ferramentas híbrido, que combina um conjunto de "Core Tools" com "Tool Plugins" customizados definidos pelo usuário. Esta tarefa consiste em implementar a lógica de carregamento dessas ferramentas dentro do `ConductorService`, tornando-o o ponto central de registro e disponibilização de todas as ferramentas no ecossistema.

#### Propósito Estratégico

O objetivo é materializar a visão de um framework extensível. Ao implementar o carregamento de plugins, permitimos que os usuários estendam as capacidades do Conductor sem modificar seu código-fonte, prevenindo o "inchaço" do core e promovendo um ecossistema de ferramentas reutilizáveis. Esta funcionalidade é crítica para a adoção do Conductor em cenários diversos, onde cada equipe pode ter seu próprio conjunto de ferramentas proprietárias.

#### Checklist de Execução

- [ ] Criar uma estrutura para as "Core Tools" (ex: um diretório `src/core/tools/`).
- [ ] Implementar uma ferramenta de exemplo (ex: `src/core/tools/file_tools.py`).
- [ ] Modificar o `ConductorService` em `src/core/conductor_service.py`.
- [ ] Implementar o método `load_tools()`.
- [ ] A lógica deve primeiro carregar as "Core Tools".
- [ ] Em seguida, deve ler a lista de diretórios de `tool_plugins` do `self._config`.
- [ ] Para cada diretório, deve escanear dinamicamente por módulos Python, importá-los e registrar as ferramentas encontradas.
- [ ] Manter um registro interno de ferramentas carregadas (ex: `self._tools: Dict[str, Tool]`).
- [ ] Chamar `self.load_tools()` no final do `__init__` do serviço.
