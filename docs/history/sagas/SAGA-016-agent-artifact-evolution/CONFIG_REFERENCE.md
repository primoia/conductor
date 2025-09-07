# Guia de Referência: `config.yaml` (SAGA-16)

**Status:** Defined
**SAGA Relacionada:** SAGA-16

Este documento detalha a estrutura e os parâmetros do arquivo de configuração principal do Conductor, `config.yaml`. Este arquivo reside na raiz do projeto e controla o comportamento fundamental da aplicação.

---

## 1. Visão Geral

O `config.yaml` é o ponto de entrada para a configuração de uma instância do Conductor. Ele define onde o estado dos agentes é armazenado e quais conjuntos de ferramentas customizadas devem ser carregados na inicialização.

---

## 2. Estrutura de Configuração

### 2.1. `storage_backend`

*   **Obrigatório:** Sim
*   **Propósito:** Define qual backend de persistência será usado para armazenar e gerenciar as **Instâncias de Agente**.

#### Opção A: `filesystem` (Padrão)

Esta é a configuração padrão, ideal para uso local e para novos usuários, pois não requer dependências externas.

*   **Exemplo:**
    ```yaml
    storage_backend:
      type: filesystem
      # Opcional: define o caminho para o workspace. O padrão é ".conductor_workspace" na raiz.
      workspace_path: ".conductor_workspace"
    ```

#### Opção B: `mongodb`

Esta configuração é recomendada para equipes, ambientes de produção e cenários que exigem um estado centralizado e escalável.

*   **Exemplo:**
    ```yaml
    storage_backend:
      type: mongodb
      # String de conexão para o MongoDB. Pode usar variáveis de ambiente.
      connection_string: "mongodb://localhost:27017"
      database_name: "conductor_db"
      # Opcional: nomes das coleções, se desejar customizar.
      collections:
        agents: "agents"
        history: "history"
        sessions: "sessions"
    ```

### 2.2. `tool_plugins`

*   **Obrigatório:** Não
*   **Propósito:** Define uma lista de diretórios onde o Conductor deve procurar por módulos de **Ferramentas Customizadas (Plugins)** para carregar na inicialização.

*   **Exemplo:**
    ```yaml
    # Lista de caminhos absolutos para os diretórios dos plugins.
    tool_plugins:
      - "/home/user/conductor_tools/sap_integration/"
      - "/home/user/conductor_tools/internal_api_clients/"
    ```

---

## 3. Exemplo de Arquivo Completo

```yaml
# Exemplo de configuração para um ambiente de desenvolvimento local.
storage_backend:
  type: filesystem
  workspace_path: ".conductor_workspace"

# Carrega um conjunto de ferramentas customizadas para um projeto específico.
tool_plugins:
  - "/mnt/c/Users/Cezar/Projects/conductor-custom-tools/project_x_tools/"

```

```yaml
# Exemplo de configuração para um ambiente de produção compartilhado.
storage_backend:
  type: mongodb
  connection_string: "mongodb://prod-mongo-01.mycompany.com:27017"
  database_name: "conductor_prod"

# Carrega o conjunto de ferramentas padrão da empresa.
tool_plugins:
  - "/opt/conductor/company_standard_tools/"
```
