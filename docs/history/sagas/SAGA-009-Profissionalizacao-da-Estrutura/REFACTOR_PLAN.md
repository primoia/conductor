**Para:** Agente Implementador (Claude)
**De:** Arquiteto de Software (Gemini)
**Assunto:** Plano de Refatoração Arquitetural: Profissionalizando o Conductor

## 1. Visão e Objetivos

O projeto `conductor` provou seu valor, mas sua estrutura de scripts monolíticos impede a escalabilidade e a manutenção. O objetivo desta refatoração é evoluir o `conductor` para um framework de software robusto, aplicando os princípios de design exemplificados no projeto de referência `desafio-meli`.

**Princípios a serem aplicados:**

1.  **Arquitetura Limpa (Ports and Adapters):** Isolar o core da aplicação de detalhes de implementação (CLI, persistência, clientes de IA).
2.  **Injeção de Dependência (DI):** Desacoplar os componentes, permitindo substituição e testes fáceis.
3.  **Observabilidade Profissional:** Implementar logging JSON estruturado para integração com plataformas de monitoramento.
4.  **Gerenciamento de Dependências Formal:** Introduzir o `Poetry` para garantir builds determinísticos e um ambiente de desenvolvimento profissional.
5.  **Configuração Segura e Centralizada:** Utilizar `pydantic-settings` para carregar configurações de forma validada e segura.

## 2. Arquitetura Alvo

A seguir, o diagrama de componentes da nova arquitetura e a estrutura de arquivos de destino.

### Diagrama de Componentes (Ports and Adapters)

```mermaid
graph TD
    subgraph Adapters Primários (Driving)
        A[CLI - admin.py]
        B[CLI - agent.py]
    end

    subgraph Core (Lógica de Negócio)
        C{Use Case: Embody Agent}
        D{Use Case: Run REPL Session}
        E[GenesisAgent - Entidade Core]
    end

    subgraph Adapters Secundários (Driven)
        F[FileStateRepository]
        G[MongoStateRepository]
        H[ClaudeCLIClient]
        I[GeminiCLIClient]
    end

    subgraph Ports (Interfaces)
        J[StateRepository Port]
        K[LLMClient Port]
    end

    A --> C
    B --> C
    C --> E
    D --> E
    C --> J
    C --> K

    J -- implementa --> F
    J -- implementa --> G
    K -- implementa --> H
    K -- implementa --> I
```

### Nova Estrutura de Arquivos

```
conductor/
├── pyproject.toml         # NOVO: Gerenciamento de dependências com Poetry
├── poetry.lock            # NOVO: Lockfile para dependências
├── .env.example           # NOVO: Exemplo de variáveis de ambiente
├── src/
│   ├── __init__.py
│   ├── cli/                 # Adapter Primário: Interface de Linha de Comando
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   └── agent.py
│   ├── core/                # Lógica de Negócio e Entidades
│   │   ├── __init__.py
│   │   ├── agent_logic.py     # Lógica de orquestração (antes em GenesisAgent)
│   │   └── domain.py          # Modelos Pydantic e exceções do domínio
│   ├── infrastructure/      # Adapters Secundários: Implementações Concretas
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   └── cli_client.py  # Implementações ClaudeCLIClient, GeminiCLIClient
│   │   └── persistence/
│   │       └── state_repository.py # Implementações File/MongoStateRepository
│   ├── ports/                 # Interfaces (Contratos Abstratos)
│   │   ├── __init__.py
│   │   ├── llm_client.py
│   │   └── state_repository.py
│   ├── config.py            # NOVO: Configuração centralizada com Pydantic
│   └── container.py         # NOVO: Container de Injeção de Dependência
└── tools/
    └── ... (scripts de suporte)
```

## 3. Plano de Execução Detalhado

### Fase 1: Fundação e Gerenciamento de Dependências

1.  **Inicializar Poetry:**
    *   Execute `poetry init` para criar o `pyproject.toml`.
    *   Adicione as dependências de produção: `pyyaml`, `pydantic`, `pydantic-settings`.
    *   Adicione as dependências de desenvolvimento: `pytest`, `pymongo` (para testes).

2.  **Criar Estrutura de Diretórios:**
    *   Crie a estrutura de diretórios `src/` completa, incluindo os subdiretórios `cli`, `core`, `infrastructure`, `ports` e os arquivos `__init__.py` em cada um.

### Fase 2: Definir os "Ports" (Interfaces)

1.  **StateRepository Port:**
    *   Crie o arquivo `src/ports/state_repository.py`.
    *   Defina a classe abstrata `StateRepository(ABC)` com os métodos `load_state` e `save_state`, exatamente como no plano da SAGA-008.

2.  **LLMClient Port:**
    *   Crie o arquivo `src/ports/llm_client.py`.
    *   Defina a classe abstrata `LLMClient(ABC)` com os métodos `invoke(prompt: str) -> str` e `set_persona(persona: str)`. Isso abstrai a chamada à IA.

### Fase 3: Implementar os "Adapters" (Implementações Concretas)

1.  **StateRepository Adapters:**
    *   Mova as classes `FileStateRepository` e `MongoStateRepository` do antigo `scripts/core/state_repository.py` para `src/infrastructure/persistence/state_repository.py`.
    *   Garanta que ambas as classes implementem a interface `StateRepository` do `src/ports/`.

2.  **LLMClient Adapters:**
    *   Crie o arquivo `src/infrastructure/llm/cli_client.py`.
    *   Mova as classes `ClaudeCLIClient` e `GeminiCLIClient` do antigo `agent_common.py` para este novo arquivo.
    *   Refatore-as para que implementem a interface `LLMClient` do `src/ports/`.

3.  **Configuração e Logging:**
    *   Crie `src/config.py` com uma classe `Settings(BaseSettings)` para carregar configurações do ambiente (ex: `MONGO_URI`).
    *   Crie um módulo `src/core/observability.py` e implemente a classe `JSONFormatter` e a função `configure_logging`, copiando o padrão do projeto de referência.

### Fase 4: Refatorar o Core da Aplicação

1.  **Refatorar `GenesisAgent` para `AgentLogic`:**
    *   O conteúdo da classe `GenesisAgent` será a base para a nova lógica de negócio.
    *   Crie `src/core/agent_logic.py`.
    *   A nova classe `AgentLogic` **não deve mais lidar com I/O ou configuração diretamente**. Seu construtor deve receber, via injeção de dependência, as implementações dos *ports* (`StateRepository` e `LLMClient`).
    *   Toda a lógica de carregar persona, gerenciar histórico de conversa, resolver caminhos e chamar a IA deve residir aqui.

### Fase 5: Injeção de Dependência e CLI

1.  **Criar o Container de DI:**
    *   Crie o arquivo `src/container.py`.
    *   Este módulo será responsável por ler a configuração (`Settings`), instanciar os adapters concretos (`FileStateRepository`, `ClaudeCLIClient`, etc.) e a lógica do core (`AgentLogic`), conectando todas as dependências.

2.  **Refatorar os CLIs (`admin.py`, `agent.py`):**
    *   Mova os arquivos para `src/cli/`.
    *   Eles devem se tornar "finos". Sua única responsabilidade é:
        a. Parsear os argumentos da linha de comando.
        b. Chamar o `container` para obter uma instância pronta do `AgentLogic`.
        c. Chamar os métodos do `AgentLogic` (ex: `agent_logic.embody_and_run_repl(...)`).
        d. Chamar `configure_logging()` no início da execução.

### Fase 6: Validação e Testes

1.  **Atualizar Testes:**
    *   Mova os testes existentes para um novo diretório `tests/` que espelhe a estrutura de `src/` (ex: `tests/core`, `tests/cli`).
    *   Refatore os testes para não dependerem mais de arquivos no disco, mas sim para injetar *mocks* dos `StateRepository` and `LLMClient` no `AgentLogic`.

2.  **Executar Validação:**
    *   Execute `poetry install` para criar o ambiente e instalar as dependências.
    *   Execute `poetry run pytest` para garantir que todos os testes, novos e antigos, passem.
    *   Execute os CLIs: `poetry run python src/cli/admin.py --help`.

### Fase 7: Limpeza

1.  **Remover Artefatos Antigos:**
    *   Delete o diretório `scripts/` inteiro.

### Fase 8: Containerização da Aplicação

Finalmente, para garantir portabilidade e consistência, a aplicação será containerizada usando Docker.

1.  **Criar `.dockerignore`:**
    *   Crie um arquivo `.dockerignore` na raiz do projeto para excluir arquivos desnecessários da imagem Docker.
    *   **Conteúdo:**
        ```
        # Docker
        .dockerignore
        Dockerfile
        docker-compose.yml

        # Ambiente
        .venv/
        .env

        # Python
        __pycache__/
        *.pyc
        .pytest_cache/
        ```

2.  **Criar `Dockerfile` Multi-Stage:**
    *   Crie um `Dockerfile` na raiz do projeto, seguindo o padrão de alta qualidade do projeto de referência.
    *   **Conteúdo:**
        ```Dockerfile
        # --- Estágio de Build ---
        FROM python:3.11-slim as builder

        WORKDIR /app

        RUN pip install poetry
        RUN poetry config virtualenvs.in-project true

        COPY pyproject.toml poetry.lock ./

        # Instala apenas dependências de produção para a imagem final
        RUN poetry install --only main --no-interaction --no-ansi --no-root

        # --- Estágio Final ---
        FROM python:3.11-slim

        WORKDIR /app

        # Copia o ambiente virtual com as dependências do estágio de build
        COPY --from=builder /app/.venv ./.venv

        # Define o PATH para que os executáveis do .venv sejam encontrados
        ENV PATH="/app/.venv/bin:$PATH"

        # Copia o código fonte da aplicação
        COPY src/ ./src

        # Define o ponto de entrada padrão (pode ser sobrescrito)
        ENTRYPOINT ["python", "-m", "src.cli.admin"]
        ```

3.  **Criar `docker-compose.yml` para Desenvolvimento:**
    *   Crie um arquivo `docker-compose.yml` para facilitar o desenvolvimento e a execução.
    *   **Conteúdo:**
        ```yaml
        version: '3.8'

        services:
          conductor:
            build: .
            # Monta o código fonte para desenvolvimento com hot-reload (se aplicável)
            volumes:
              - ./src:/app/src
            # Passa variáveis de ambiente para o container
            env_file:
              - .env
        ```

## 5. Critérios de Sucesso (Para Avaliação do Arquiteto)

A refatoração será considerada um sucesso se:

-   [ ] O projeto utilizar `pyproject.toml` e `poetry.lock`.
-   [ ] A estrutura de diretórios corresponder exatamente à arquitetura proposta em `src/`.
-   [ ] A lógica de negócio (`AgentLogic`) depender apenas de interfaces (`ports`), não de implementações concretas.
-   [ ] Os CLIs (`admin.py`, `agent.py`) forem apenas pontos de entrada que delegam para o core.
-   [ ] O logging da aplicação for estruturado em JSON.
-   [ ] A imagem Docker for construída com sucesso via `docker compose build`.
-   [ ] O container executar corretamente: `docker compose run --rm conductor --help` deve funcionar.
-   [ ] Todos os testes em `tests/` passarem com sucesso via `poetry run pytest`.
-   [ ] O diretório `scripts/` original for completamente removido.