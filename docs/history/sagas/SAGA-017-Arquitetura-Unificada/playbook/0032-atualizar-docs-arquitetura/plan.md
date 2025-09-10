### Plano de Execução: Estágio 32 - Atualizar Documentos de Arquitetura

#### Contexto Arquitetônico

Os documentos no diretório `docs/architecture/` descrevem o design e a filosofia do Conductor. Com a implementação da SAGA-017, esses documentos, que podem descrever o `AgentLogic` como o núcleo ou a estrutura de diretórios rígida, estão agora desatualizados e incorretos.

#### Propósito Estratégico

O objetivo é manter a documentação de arquitetura como uma fonte da verdade precisa para desenvolvedores que desejam entender o funcionamento interno do projeto. Documentação de arquitetura precisa é crucial para o onboarding de novos contribuidores, para a tomada de decisões de design futuras e para a manutenibilidade geral do sistema.

#### Checklist de Execução

- [ ] Revisar todos os documentos no diretório `docs/architecture/`.
- [ ] Identificar seções que descrevem a arquitetura legada (ex: o papel do `AgentLogic`, a descoberta de agentes baseada em pastas).
- [ ] Atualizar essas seções para descrever a nova arquitetura service-oriented.
- [ ] Introduzir o conceito do `ConductorService` como o novo "coração" do sistema.
- [ ] Explicar o papel do `AgentExecutor` como o "worker" stateless.
- [ ] Atualizar ou criar diagramas de arquitetura (se houver) para refletir o novo fluxo de dados (CLI -> Service -> Executor).
- [ ] Criar um novo documento `UNIFIED_ARCHITECTURE.md` que consolida a visão final.
