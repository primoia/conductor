# Segurança e Confiabilidade

A segurança é um pilar fundamental do design do framework.

**Principais Medidas:**
- **Escopo de Escrita (`output_scope`):** Impede que agentes modifiquem arquivos fora de seu diretório de trabalho designado.
- **Confirmação Humana:** No modo interativo (`--repl`), qualquer operação de escrita de arquivo exige a confirmação explícita do usuário.
- **Executores Separados:** A separação entre `admin.py` (tarefas do framework) e `genesis_agent.py` (tarefas de projeto) previne que um agente de projeto modifique a configuração do próprio framework.
- **Arquitetura de Ambientes:** Isola logicamente os ambientes de `desenvolvimento` e `produção` através do `workspaces.yaml`.
