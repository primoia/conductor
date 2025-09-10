### Plano de Execução: Estágio 5 - Implementação da Descoberta de Agentes

#### Contexto Arquitetônico

Com o `ConductorService` agora equipado com um repositório de estado funcional (via `StorageFactory`), podemos implementar a primeira grande funcionalidade do serviço: a descoberta de agentes. Esta tarefa consiste em implementar o método `discover_agents()`. Este método usará a instância do `IStateRepository` para consultar o backend de armazenamento e retornar uma lista de todas as definições de agentes disponíveis.

#### Propósito Estratégico

O objetivo é centralizar a lógica de descoberta de agentes no `ConductorService`, removendo-a completamente dos CLIs legados. Ao fazer isso, os CLIs não precisarão mais conhecer a estrutura de diretórios ou os detalhes do armazenamento. Eles simplesmente perguntarão ao serviço: "Quais agentes existem?". Isso completa uma parte crucial da unificação, garantindo que a descoberta de agentes seja consistente, independentemente do backend utilizado ou do ponto de entrada que a solicita.

#### Checklist de Execução

- [ ] Implementar o método `list_agents()` na classe placeholder `FileSystemStateRepository`. Por enquanto, ele pode retornar uma lista mockada de IDs de agente (ex: `["CodeReviewer_Agent"]`).
- [ ] Modificar o `ConductorService` em `src/core/conductor_service.py`.
- [ ] Implementar a lógica do método `discover_agents()`.
- [ ] A lógica deve chamar `self.repository.list_agents()` para obter a lista de IDs.
- [ ] Em seguida, para cada ID, deve chamar `self.repository.load_state(agent_id)` para obter os dados do agente.
- [ ] Assumir que os dados carregados contêm uma chave `definition` que pode ser mapeada para um `AgentDefinition` DTO (que precisará ser definido em `src/core/domain.py`).
- [ ] O método deve retornar uma lista de objetos `AgentDefinition`.
