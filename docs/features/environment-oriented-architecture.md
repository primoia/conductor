# Arquitetura Orientada a Ambientes

Para garantir segurança e organização, o framework opera com um conceito de **ambientes** e **workspaces**. Isso impede que um agente destinado a um ambiente de `desenvolvimento` modifique acidentalmente um ambiente de `produção`.

**Configuração Chave:**
- **`config/workspaces.yaml`**: Mapeia nomes de ambientes lógicos (ex: `develop`) para caminhos de diretório físicos no seu sistema.

**Execução:**
- O comando `genesis_agent.py` exige o parâmetro `--environment` para garantir que o agente seja carregado e executado no contexto correto e seguro.
