# Análise de Segurança da Arquitetura (SAGA-017)

## Vetor de Ameaça: Carregamento de Tool Plugins

A funcionalidade de `tool_plugins` introduzida na SAGA-016 permite carregar código Python de diretórios especificados no `config.yaml`. Isso representa o principal vetor de ameaça da nova arquitetura.

### Riscos Identificados

1.  **Path Traversal:** Um usuário mal-intencionado poderia configurar um caminho como `../../../../etc/` para tentar carregar ou inspecionar arquivos do sistema.
2.  **Execução de Código Malicioso:** Um usuário pode, intencionalmente ou não, apontar para um diretório de plugin que contém código malicioso, que seria executado na inicialização do `ConductorService`.

### Mitigações Implementadas (Estágio 24)

1.  **Validação de Caminho:** O `ConductorService` agora verifica se o caminho absoluto do diretório do plugin é um subdiretório do diretório do projeto. Isso mitiga efetivamente os ataques de Path Traversal, garantindo que apenas o código dentro do escopo do projeto possa ser carregado dinamicamente.
2.  **Logging Explícito:** Um `WARNING` é explicitamente logado sempre que um plugin é carregado. Isso aumenta a visibilidade e ajuda na auditoria.

### Riscos Residuais e Recomendações

-   O risco de execução de código malicioso persiste. A responsabilidade final recai sobre o operador que configura o `config.yaml`.
-   **Recomendação:** A documentação deve instruir claramente os usuários a **nunca** carregar plugins de fontes não confiáveis.
-   **Futuro:** Em um ambiente de produção mais restrito, considerar a implementação de uma "allow-list" de plugins permitidos ou a assinatura de código para os plugins.