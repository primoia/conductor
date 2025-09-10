### Plano de Execução: Estágio 30 - Remover `src/core/agent_logic.py`

#### Contexto Arquitetônico

O arquivo `src/core/agent_logic.py` foi formalmente depreciado no estágio anterior e já não possui nenhuma referência no código de produção. Manter o arquivo no projeto agora constitui débito técnico: ele polui o código-fonte, pode confundir novos desenvolvedores e arrisca ser reintroduzido acidentalmente. Esta tarefa consiste na remoção física e definitiva do arquivo.

#### Propósito Estratégico

O objetivo é concluir o ciclo de vida do componente legado e limpar o código-fonte. A remoção do `AgentLogic` é um marco simbólico e técnico, representando o ponto sem retorno na adoção da nova arquitetura. Isso simplifica a base de código e torna o projeto mais fácil de entender e manter a longo prazo.

#### Checklist de Execução

- [ ] Deletar o arquivo `src/core/agent_logic.py`.
- [ ] Executar uma busca global por "AgentLogic" para garantir que nenhuma referência (ex: em imports não utilizados ou em testes legados) permaneceu.
- [ ] Executar a suíte de testes completa (`poetry run pytest`).
- [ ] A execução dos testes deve continuar passando, provando que a remoção do arquivo não teve impacto no sistema funcional.
