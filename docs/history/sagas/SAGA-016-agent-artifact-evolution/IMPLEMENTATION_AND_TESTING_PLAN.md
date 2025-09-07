# SAGA-16: Plano de Implementação e Testes

**Status:** Defined
**SAGA Relacionada:** SAGA-16

## 1. Objetivo

Atualizar a base de código do Conductor para implementar a arquitetura de "Backend Flexível" e o novo modelo de artefatos de agente, conforme definido nos documentos de planejamento da SAGA-16. Este plano guiará a refatoração dos componentes `admin.py`, `agent.py` e `run_conductor.py`, entre outros, e estabelece a estratégia de testes para garantir uma transição segura e robusta.

---

## 2. Estratégia de Testes

Esta estratégia é dividida em duas fases para garantir que a funcionalidade existente não seja perdida e que a nova arquitetura seja completamente validada.

### Fase A: Testes de Regressão (Rede de Segurança)

**Objetivo:** Criar testes que validem o comportamento da arquitetura *antiga*. Estes testes irão falhar durante a refatoração e deverão ser adaptados ou substituídos, mas garantem que entendemos e cobrimos os casos de uso atuais.

*   **Plano de Ação:**
    1.  **`tests/regression/test_legacy_agent_loading.py`**: Criar testes que verifiquem se a classe `Agent` atual consegue carregar e parsear um `state.json` antigo.
    2.  **`tests/regression/test_legacy_admin_cli.py`**: Criar testes para os comandos atuais do `admin.py`, como o antigo processo de "deploy".
    3.  **`tests/regression/test_legacy_run_conductor.py`**: Criar um teste de integração que executa um plano simples usando a estrutura de arquivos antiga.

### Fase B: Testes da Nova Arquitetura (Test-Driven Development)

**Objetivo:** Desenvolver um conjunto completo de testes para a nova arquitetura. Estes testes devem ser escritos *antes* ou *durante* a implementação de cada novo componente.

*   **Plano de Ação:**
    1.  **`tests/storage/test_filesystem_backend.py`**: Testar todos os métodos do `FileSystemBackend`, incluindo:
        *   Criação do diretório `.conductor_workspace`.
        *   "Onboarding" (cópia) dos `_agent_templates/` na primeira execução.
        *   Leitura e escrita de cada tipo de artefato (`definition.yaml`, `persona.md`, `playbook.yaml`, `knowledge.json`, `history.log`).
    2.  **`tests/storage/test_mongodb_backend.py`**: Usando um mock do `pymongo` ou um banco de dados de teste, validar todos os métodos do `MongoDbBackend`.
    3.  **`tests/core/test_orchestrator.py`**: Testar a lógica do Orquestrador em `run_conductor.py`:
        *   Seleção de agente por `tags` e `capabilities`.
        *   Fallback para o `AgentCreator_Agent` quando nenhum agente é encontrado.
    4.  **`tests/core/test_tool_loader.py`**: Testar o carregamento de "Core Tools" e "Custom Tools" a partir dos caminhos definidos no `config.yaml`.
    5.  **`tests/cli/test_new_admin.py`**: Testar os novos comandos do `admin.py` (ex: `agents list`, `agents describe`).

---

## 3. Plano de Refatoração por Componente

### 3.1. Camada de Persistência (Nova)

*   **Ação:** Criar um novo diretório `src/storage/`.
*   **`src/storage/base.py`**: Definir uma classe base abstrata `BaseStorageBackend` com métodos como `get_agent_instance`, `update_knowledge`, `add_history_event`, etc.
*   **`src/storage/filesystem.py`**: Implementar a classe `FileSystemBackend` que herda de `BaseStorageBackend` e implementa a lógica de manipulação de arquivos no `.conductor_workspace/`.
*   **`src/storage/mongodb.py`**: Implementar a classe `MongoDbBackend` que herda de `BaseStorageBackend` e implementa a lógica de interação com o MongoDB.

### 3.2. Configuração e Carregamento (Novos/Refatorados)

*   **`src/config.py`**: Criar um módulo para carregar o `config.yaml` da raiz do projeto e fornecer os valores de forma global e validada.
*   **`src/tool_loader.py`**: Criar um módulo que lê a chave `tool_plugins` do `config.py` e carrega dinamicamente os módulos de ferramentas customizadas.

### 3.3. `run_conductor.py` (Refatoração Pesada)

*   **Ação:** Este arquivo será o ponto de entrada principal e conterá a lógica do Orquestrador.
*   Remover completamente a lógica antiga de carregamento de agentes.
*   Adicionar a lógica para:
    1.  Carregar a configuração do `config.py`.
    2.  Instanciar o `StorageBackend` correto com base na configuração.
    3.  Executar o ciclo de vida do Orquestrador (Análise da Tarefa -> Filtragem -> Decisão -> Execução) conforme detalhado no `README.md` da SAGA.

### 3.4. `agent.py` (Refatoração Pesada)

*   **Ação:** A classe `Agent` atual será refatorada ou substituída por uma classe `AgentInstance`.
*   Esta classe não terá mais a responsabilidade de ler/escrever seus próprios arquivos. Ela será um contêiner de dados que recebe seus artefatos (`persona`, `knowledge`, etc.) do `StorageBackend` através do Orquestrador.

### 3.5. `admin.py` (Refatoração Pesada)

*   **Ação:** O CLI de administração será atualizado para refletir a nova arquitetura.
*   Remover comandos antigos como `deploy-agent`.
*   Adicionar novos comandos que interagem com o `StorageBackend` configurado:
    *   `conductor-admin agents list`: Lista todas as instâncias de agentes.
    *   `conductor-admin agents describe <agent_id>`: Mostra os detalhes de uma instância.
    *   `conductor-admin agents tune <agent_id>`: Inicia uma sessão com o `AgentTuner_Agent` para modificar o agente alvo.

---

## 4. Sequência de Implementação Sugerida

Recomenda-se a seguinte ordem para a implementação:

1.  **Escrever os Testes de Regressão (Fase A)** para estabelecer a linha de base.
2.  **Implementar a Camada de Persistência (`storage`)** e seus respectivos testes (Fase B). Este é o novo alicerce.
3.  **Implementar os Módulos de Configuração e Tool Loader** com seus testes.
4.  **Refatorar `run_conductor.py`** para usar a nova camada de persistência e a lógica do Orquestrador. Adaptar/criar os testes conforme necessário.
5.  **Refatorar a classe `Agent`** para o novo modelo `AgentInstance`.
6.  **Refatorar `admin.py`** com os novos comandos e testes.
7.  **Verificação Final:** Garantir que todos os testes (Fase A adaptados e Fase B) estão passando.
