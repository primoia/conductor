# Desafio Meli - API de Detalhes do Item

API desenvolvida como parte do desafio técnico de backend do Mercado Livre.

Este projeto cria uma API containerizada para servir detalhes de produtos, seguindo as melhores práticas de arquitetura de software, testes e automação.

**Stack Tecnológica:**
*   Python 3.11+
*   FastAPI
*   Poetry
*   Pytest
*   Docker & Docker Compose

## Como Executar

Este projeto é totalmente containerizado. O único pré-requisito é ter **Docker** e **Docker Compose** instalados.

Para instruções detalhadas de como construir a imagem, iniciar a aplicação, parar a aplicação e rodar os testes, por favor, consulte o documento:

➡️ **[./run.md](./run.md)**

## Diagrama de Arquitetura

A aplicação segue uma arquitetura em camadas (Ports and Adapters) que separa claramente as responsabilidades:

```mermaid
graph TD
    A[Client/HTTP Requests] --> B[FastAPI - API Layer]
    B --> C[Service Layer]
    C --> D[Repository Layer] 
    D --> E[Data Layer - JSON File]
    
    subgraph "API Layer"
        B1[GET /api/v1/items/{id}]
        B2[POST /api/v1/items]  
        B3[PUT /api/v1/items/{id}]
        B4[DELETE /api/v1/items/{id}]
    end
    
    subgraph "Service Layer"
        C1[ItemService]
        C2[Business Logic]
        C3[ItemNotFoundException]
    end
    
    subgraph "Repository Layer"  
        D1[ItemRepository]
        D2[find_by_id]
        D3[save]
        D4[delete]
    end
    
    subgraph "Data Layer"
        E1[items.json]
        E2[Configuration via .env]
    end
    
    subgraph "Cross-Cutting Concerns"
        F1[JSON Structured Logging]
        F2[Pydantic Validation]
        F3[Exception Handling]
    end
    
    B --> B1
    B --> B2  
    B --> B3
    B --> B4
    
    C --> C1
    C --> C2
    C --> C3
    
    D --> D1
    D --> D2
    D --> D3  
    D --> D4
    
    E --> E1
    E --> E2
    
    C -.-> F1
    B -.-> F2
    B -.-> F3
```

**Benefícios da Arquitetura:**
- **Separação de Responsabilidades:** Cada camada tem uma função específica
- **Testabilidade:** Camadas isoladas permitem testes unitários eficazes
- **Manutenibilidade:** Mudanças em uma camada não afetam outras
- **Escalabilidade:** Fácil substituição de componentes (ex: JSON → Database)

## Estratégia de Logging e Observabilidade

Este projeto implementa uma estratégia de logging estruturado que facilita a integração com qualquer plataforma de observabilidade moderna.

### Abordagem de Logging

**Formato Estruturado JSON:** Todos os logs são emitidos em formato JSON estruturado para `stdout`, facilitando:
- Parsing automático por sistemas de agregação de logs
- Filtragem e busca eficientes por campos específicos  
- Integração nativa com stacks como ELK, Splunk, Datadog, etc.

**Exemplo de saída de log:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "name": "app.services.item_service",
  "message": "Item found: iPhone 14 Pro Max (ID: MLB123456789)",
  "module": "item_service",
  "function": "get_item_by_id",
  "line": 56
}
```

### Integração com Plataformas de Observabilidade

O padrão de logging para `stdout` permite integração transparente com qualquer sistema:

**Exemplo - Papertrail via Syslog Driver:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logs.papertrailapp.com:XXXXX"
        tag: "desafio-meli-api"
```

**Outras integrações suportadas:**
- AWS CloudWatch Logs (driver `awslogs`)
- Google Cloud Logging (driver `gcplogs`) 
- Fluentd (driver `fluentd`)
- Splunk (driver `splunk`)

## Estrutura do Projeto

### Saga 01 - Fundação
A arquitetura do projeto estabelece a fundação para o desenvolvimento:

-   `app/main.py`: Ponto de entrada da aplicação FastAPI e endpoint "Hello World".
-   `tests/test_api.py`: Teste de integração para o endpoint "Hello World".
-   `Dockerfile`: Receita para construir a imagem da aplicação.
-   `docker-compose.yml`: Orquestra a execução do container.
-   `pyproject.toml` / `poetry.lock`: Gerenciamento de dependências.
-   `docs/sagas/`: Documentação incremental da arquitetura e decisões de projeto.

## Decisões Arquitetônicas Chave

Este projeto foi construído com várias decisões de arquitetura intencionais para garantir robustez, manutenibilidade e alinhamento com as práticas modernas de engenharia de software:

1.  **Arquitetura em Camadas (Ports and Adapters):** A aplicação é dividida em camadas distintas (API, Serviços, Repositório) para separar as responsabilidades. Isso garante que a lógica de negócio (`services`) não dependa de detalhes de implementação, como o framework web (`api`) ou o método de persistência (`repository`).

2.  **Containerização com Docker:** Todo o ambiente de desenvolvimento e produção é containerizado. Isso resolve o problema de "funciona na minha máquina", garante consistência entre ambientes e simplifica drasticamente a execução do projeto para qualquer pessoa. O `Dockerfile` multi-stage cria uma imagem final otimizada, contendo apenas o necessário para a execução.

3.  **Logging Estruturado para `stdout`:** Seguindo a metodologia "Twelve-Factor App", a aplicação não escreve logs em arquivos. Em vez disso, emite logs estruturados (JSON) para a saída padrão, delegando a responsabilidade de coleta e armazenamento para o ambiente de execução (Docker). Isso torna a aplicação agnóstica em relação à plataforma de observabilidade e pronta para integração com sistemas de monitoramento de nível empresarial.

4.  **Gerenciamento de Dependências com Poetry:** Usamos Poetry e seu arquivo `poetry.lock` para garantir builds 100% reprodutíveis. Qualquer pessoa que construir o projeto terá o mesmo conjunto exato de dependências, eliminando conflitos de versão.

## Estratégia Técnica e Uso de IA

A eficiência do desenvolvimento foi aprimorada através de uma combinação de ferramentas modernas e um fluxo de trabalho assistido por IA.

-   **Stack Tecnológica:** A escolha por **Python/FastAPI** foi deliberada para maximizar a velocidade de desenvolvimento, aproveitar a validação de dados nativa com Pydantic e obter documentação de API (Swagger UI) automaticamente.
-   **Fluxo de Trabalho Arquiteto/Implementador:** Utilizamos um modelo de colaboração onde uma IA (Gemini) atua como o **Arquiteto de Software**, responsável pelo planejamento, design, documentação e revisão. Outra IA (Claude) atua como o **Implementador**, focada em traduzir os blueprints do arquiteto em código limpo e funcional. Este processo, documentado em `prompts.md`, permitiu uma separação clara de responsabilidades e acelerou o ciclo de desenvolvimento.

## Plano de Projeto

Este projeto foi desenvolvido seguindo uma metodologia incremental documentada através de "sagas". Cada saga representa uma etapa de desenvolvimento com objetivos específicos e critérios de aceitação bem definidos.

**Documentação Completa do Plano:** A pasta `docs/sagas/` contém a documentação detalhada de cada fase do projeto:

- **Saga 01 - Fundação:** Estrutura básica, containerização e "Hello World"
- **Saga 02 - O Item:** Implementação da lógica de negócio com arquitetura limpa  
- **Saga 02a - Observabilidade:** Logging estruturado JSON para monitoramento
- **Saga 03 - Configuração e Modificação:** Configurações externas e endpoint POST
- **Saga 03.1 - CRUD Completo:** Implementação de UPDATE e DELETE com testes E2E
- **Saga 04 - Documentação Final:** Diagramas de arquitetura e empacotamento

## API Endpoints

A API oferece operações CRUD completas para gerenciamento de itens:

### **GET** `/api/v1/items/{item_id}`
Busca um item específico pelo ID.
- **Status**: `200 OK` | `404 Not Found`
- **Response**: Objeto `Item` com todos os campos

### **POST** `/api/v1/items`  
Cria um novo item.
- **Status**: `201 Created` | `422 Validation Error`
- **Payload**: `ItemCreateModel` (todos os campos exceto `id`)
- **Response**: Objeto `Item` criado com `id` gerado automaticamente

### **PUT** `/api/v1/items/{item_id}`
Atualiza um item existente (atualização parcial suportada).
- **Status**: `200 OK` | `404 Not Found` | `422 Validation Error`  
- **Payload**: `ItemUpdateModel` (todos os campos opcionais)
- **Response**: Objeto `Item` atualizado

### **DELETE** `/api/v1/items/{item_id}`
Remove um item.
- **Status**: `204 No Content` | `404 Not Found`
- **Response**: Corpo vazio

### Estrutura do Projeto

### Saga 01 - Fundação
Estrutura básica e containerização:

-   `app/main.py`: Ponto de entrada da aplicação FastAPI e endpoint "Hello World"
-   `tests/test_api.py`: Suíte de testes de integração abrangente
-   `Dockerfile`: Receita para construir a imagem da aplicação  
-   `docker-compose.yml`: Orquestra a execução do container
-   `pyproject.toml` / `poetry.lock`: Gerenciamento de dependências
-   `docs/sagas/`: Documentação incremental da arquitetura e decisões

### Saga 02-04 - Implementação Completa  
Funcionalidades completas com arquitetura limpa:

-   `app/models/item.py`: Modelos Pydantic (Item, ItemCreateModel, ItemUpdateModel)
-   `app/repository/item_repository.py`: Camada de persistência com operações CRUD
-   `app/services/item_service.py`: Lógica de negócio e exceções customizadas  
-   `app/api/v1/items.py`: Endpoints REST completos com injeção de dependência
-   `app/core/config.py`: Configuração centralizada com pydantic-settings
-   `app/core/logging_config.py`: Logging estruturado JSON para observabilidade
-   `data/items.json`: Base de dados simulada para desenvolvimento
-   `tests/`: Suíte completa com testes unitários, integração e E2E
