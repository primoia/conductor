### Plano de Execução: Estágio 24 - Realizar Análise de Segurança Básica

#### Contexto Arquitetônico

A nova arquitetura introduziu a capacidade de carregar "Tool Plugins" de diretórios arbitrários especificados no `config.yaml`. Embora poderosa, essa funcionalidade representa um vetor de ataque potencial se não for tratada com cuidado. Por exemplo, um caminho malicioso poderia apontar para diretórios do sistema (`/etc/`), ou um plugin poderia conter código malicioso.

#### Propósito Estratégico

O objetivo é garantir que a nova flexibilidade não introduziu vulnerabilidades de segurança óbvias. Esta tarefa não é uma auditoria de segurança completa, mas uma análise de "bom senso" e a implementação de salvaguardas básicas. Isso demonstra uma preocupação com a segurança desde as fases iniciais de desenvolvimento e previne as classes mais comuns de vulnerabilidades relacionadas ao carregamento dinâmico de código.

#### Checklist de Execução

- [x] Revisar o código do carregador de plugins no `ConductorService`.
- [x] Implementar uma verificação para garantir que o caminho do plugin resolvido esteja dentro do diretório do projeto ou em uma lista de diretórios permitidos, para prevenir ataques de "Path Traversal".
- [x] Adicionar um log de aviso claro (`WARNING`) sempre que um plugin de um diretório externo for carregado.
- [x] Adicionar uma seção de "Segurança" ao guia de `creating_tool_plugins.md` (a ser criado na Fase VI), alertando os usuários sobre os riscos de carregar plugins de fontes não confiáveis.
- [x] Documentar os resultados da análise em um arquivo `docs/architecture/SECURITY_ANALYSIS.md`.
