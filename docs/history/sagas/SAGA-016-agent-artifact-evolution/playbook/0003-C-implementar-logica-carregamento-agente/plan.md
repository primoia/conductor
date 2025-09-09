# Plano: 0003-C - Core: Lógica de Carregamento de Agentes

## Contexto

Agora que temos as estruturas de dados (`domain`) e a persistência (`filesystem_storage`), podemos unir as duas partes. O objetivo deste plano é criar um serviço de alto nível, `AgentService`, que orquestra o carregamento completo de uma "Instância de Agente" do workspace.

Este serviço atuará como a principal porta de entrada para interagir com os dados de um agente. Ele esconderá os detalhes de implementação de onde os dados estão armazenados (seja filesystem ou MongoDB no futuro).

Vamos criar um novo `AgentInstance` dataclass em `domain.py` para representar um agente totalmente carregado em memória e um novo `agent_service.py` para a lógica.

## Checklist de Verificação

- [x] Em `src/core/domain.py`, criar uma nova dataclass `AgentInstance` que contém todos os artefatos: `definition: AgentDefinition`, `persona: AgentPersona`, `playbook: AgentPlaybook`, `knowledge: AgentKnowledge`, `history: List[HistoryEntry]`.
- [x] Criar um novo arquivo `src/core/agent_service.py`.
- [x] Em `agent_service.py`, criar uma classe `AgentService`.
- [x] O construtor do `AgentService` deve receber uma instância de um repositório (inicialmente, o `FileSystemStorage`).
- [x] Implementar um método `load_agent_instance(agent_name: str) -> AgentInstance` no `AgentService`.
- [x] O método `load_agent_instance` deve usar o repositório injetado para carregar cada artefato individualmente (`definition`, `persona`, etc.) e montá-los em um objeto `AgentInstance`.
- [x] Adicionar tratamento de erro básico para o caso de um diretório de agente não ser encontrado.
