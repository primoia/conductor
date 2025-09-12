# Implementation Plan

- [ ] 1. Corrigir descoberta de agentes para usar apenas .conductor_workspace/agents
  - Analisar código atual de descoberta de agentes
  - Remover lógica que procura em paths legados (projects/_common/agents, projects/[env]/[projeto]/agents)
  - Garantir que AgentDiscoveryService procure apenas em .conductor_workspace/agents
  - _Requirements: 2.1, 2.2_

- [ ] 2. Limpar referências a workspaces.yaml deprecated
  - Encontrar e remover imports/referências a config/workspaces.yaml
  - Remover código que ainda usa workspaces.yaml
  - Verificar se há fallbacks ou lógica condicional relacionada
  - _Requirements: 4.1, 4.2_

- [ ] 3. Atualizar documentação para refletir estrutura atual
  - Corrigir README.md removendo referências a paths legados
  - Atualizar arquitetura_conductor.md
  - Corrigir documentação em docs/ que menciona estrutura antiga
  - _Requirements: 6.1, 6.2_

- [ ] 4. Melhorar tratamento de erros na descoberta de agentes
  - Implementar sugestões de agentes similares quando não encontrado
  - Adicionar mensagens de erro mais claras
  - Implementar validação de estrutura de agentes
  - _Requirements: 6.1, 6.3_

- [ ] 5. Validar e testar correções
  - Testar descoberta de agentes em .conductor_workspace/agents
  - Verificar que paths legados não são mais usados
  - Testar admin.py e agent.py com as correções
  - _Requirements: 1.1, 1.2, 3.1_