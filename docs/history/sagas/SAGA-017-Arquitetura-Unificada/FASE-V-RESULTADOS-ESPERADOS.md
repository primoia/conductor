# SAGA-017: Resultados Esperados da Fase V - Migração do Ecossistema de Agentes

## 1. Visão Geral do Resultado

Ao concluir a **Fase V: Migração do Ecossistema de Agentes**, teremos alinhado completamente nossos ativos de agentes existentes com a nova arquitetura unificada. A ponte entre o passado e o presente foi atravessada, e todo o nosso ecossistema de agentes agora "fala a mesma língua", operando sob a estrutura de artefatos da SAGA-016.

O resultado principal é um **ecossistema de agentes totalmente migrado e funcional**, onde não existem mais agentes no formato legado. Além disso, teremos consolidado a configuração do sistema, removendo formalmente os últimos vestígios da estrutura de configuração antiga.

## 2. Artefatos e Capacidades Concretas Entregues

Ao final dos estágios 25 a 28 da Fase V, teremos os seguintes entregáveis concretos:

1.  **Ferramenta de Migração Reutilizável (`migrate_legacy_agents.py`):**
    *   O diretório `scripts/` conterá um script robusto e documentado para converter agentes do formato antigo para o novo. Esta é uma ferramenta valiosa para a manutenção do projeto a longo prazo.

2.  **Agentes Migrados e Operacionais:**
    *   Todos os agentes que antes existiam em `projects/_common/agents/` e `projects/desafio-meli/agents/` terão sido processados.
    *   Seus novos artefatos (`definition.yaml`, `persona.md`) correspondentes existirão no diretório do workspace (ex: `.conductor_workspace/agents/`), prontos para serem lidos pelo `ConductorService`.

3.  **Validação da Descoberta e Execução:**
    *   Teremos a confirmação de que o `ConductorService` é capaz de descobrir e executar com sucesso os agentes recém-migrados, provando que a migração e a nova arquitetura são compatíveis.

4.  **Configuração Legada Removida:**
    *   O arquivo `config/workspaces.yaml` terá sido renomeado para `config/workspaces.yaml.DEPRECATED`.
    *   Qualquer lógica de código que o lia terá sido removida, consolidando o `config.yaml` como a única fonte da verdade para a configuração.

## 3. O Que Este Resultado Nos Permite Fazer

*   **Operar um Ecossistema 100% Unificado:** Todos os agentes, sejam meta-agentes ou agentes de projeto, agora seguem o mesmo padrão de artefatos e são gerenciados pela mesma lógica de serviço.
*   **Simplificar o Desenvolvimento Futuro:** Novos desenvolvedores só precisam aprender um único padrão de como os agentes são definidos, armazenados e configurados.
*   **Iniciar a Consolidação Final:** Com todos os ativos migrados e a configuração limpa, estamos prontos para a fase final de limpeza de código (remover `AgentLogic`) e atualização da documentação.

## 4. O Que **NÃO** Teremos ao Final da Fase V

*   **Documentação Atualizada:** Embora a migração técnica esteja completa, a documentação do projeto (`README.md`, guias) ainda não foi atualizada para refletir o novo estado do mundo. Isso é o foco da Fase VI.
*   **Código Legado Removido:** O `AgentLogic` ainda existe, embora agora esteja totalmente órfão.

Em resumo, a Fase V é a "arrumação da casa" após a grande reforma. Nós pegamos todos os móveis antigos, os adaptamos para a nova casa e jogamos fora os mapas e plantas arquitetônicas antigas que não servem mais.
