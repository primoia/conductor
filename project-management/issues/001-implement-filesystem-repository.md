# Problema 001: Implementar a Camada de Persistência `FileSystemStateRepository`

## 1. Descrição do Problema

A investigação da arquitetura revelou que o `FileSystemStateRepository`, componente central responsável por salvar e carregar o estado dos agentes no disco, não está implementado. Os métodos `save_state`, `load_state` e `list_agents` contêm apenas stubs e dados mockados, tornando a camada de persistência da nova arquitetura inoperante.

Essa falha faz com que o sistema dependa de mecanismos de salvamento legados e quebrados no CLI, resultando em comportamento incorreto e na persistência de estado em diretórios obsoletos.

## 2. Requisitos (Comportamento Esperado)

Como guardião dos requisitos da SAGA-017, a implementação correta deve seguir o contrato `IStateRepository` e as seguintes diretrizes:

1.  **Utilização do Workspace Configurado:** A implementação deve operar exclusivamente dentro do `base_path` fornecido em sua inicialização (que corresponde ao `storage.path` do `config.yaml`, ou seja, `.conductor_workspace`).

2.  **Implementação de `save_state`:**
    *   Recebe `agent_id` e um dicionário `state_data`.
    *   O `state_data` contém as chaves `session` e `memory`.
    *   O método deve criar o diretório `<base_path>/agents/<agent_id>/` se ele não existir.
    *   Deve serializar e salvar o conteúdo de `state_data['session']` no arquivo `<base_path>/agents/<agent_id>/session.json`.
    *   Deve serializar e salvar o conteúdo de `state_data['memory']` no arquivo `<base_path>/agents/<agent_id>/memory.json`.

3.  **Implementação de `load_state`:**
    *   Recebe `agent_id`.
    *   Deve ler os arquivos `session.json` e `memory.json` de dentro do diretório do agente.
    *   Deve reconstruir e retornar um dicionário único no formato `{ "session": {...}, "memory": {...} }`.
    *   Deve retornar um dicionário com as chaves e valores vazios (`{ "session": {}, "memory": {} }`) caso os arquivos ou o diretório não existam.

4.  **Implementação de `list_agents`:**
    *   Deve escanear o diretório `<base_path>/agents/`.
    *   Deve retornar uma lista de strings com os nomes de todos os subdiretórios, pois cada um representa um agente.

## 3. Critérios de Aceitação

1.  Os stubs e dados mockados em `src/infrastructure/storage/filesystem_repository.py` são substituídos por uma lógica funcional de manipulação de arquivos.
2.  A chamada ao `conductor_service.save_state(agent_id, data)` resulta na criação/atualização dos arquivos `session.json` e `memory.json` no diretório correto dentro de `.conductor_workspace`.
3.  A chamada ao `conductor_service.load_state(agent_id)` reconstrói o estado corretamente a partir dos arquivos JSON.
4.  O bug original que causava a escrita no diretório `_common` é resolvido como efeito colateral da implementação correta.
