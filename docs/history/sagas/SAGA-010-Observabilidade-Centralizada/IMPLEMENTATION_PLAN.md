**Para:** Agente Implementador (Claude)
**De:** Arquiteto de Software (Gemini)
**Assunto:** Plano de Implementação da Stack de Observabilidade Centralizada

## 1. Visão Geral

Este documento detalha os passos para implementar uma stack de logging centralizado usando Promtail, Loki e Grafana (Stack PLG). O objetivo é coletar os logs JSON estruturados da aplicação `conductor` e permitir sua visualização e filtragem em uma interface web. Este plano assume que a refatoração da SAGA-009 foi concluída.

## 2. Decisão Arquitetural: Localização da Stack

Para garantir a escalabilidade do monorepo, a stack de observabilidade não residirá dentro do projeto `conductor`. Ela será criada em um novo diretório de alto nível chamado `observability/`, paralelo ao diretório `projects/`. Isso permite que, no futuro, outros projetos do monorepo também enviem seus logs para esta mesma instância centralizada.

**Estrutura Alvo no Monorepo:**
```
primoia-monorepo/
├── observability/          # NOVO: Stack de monitoramento
│   ├── docker-compose.yml
│   ├── loki/
│   │   └── config.yml
│   ├── promtail/
│   │   └── config.yml
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   └── dashboards/
│       └── grafana.ini
└── projects/
    └── conductor/
        ├── src/
        └── ...
```

## 3. Fase 1: Aprimoramento dos Logs da Aplicação

O formato de log JSON atual é bom, mas falta um campo crucial para a filtragem: o `agent_id`. Vamos adicioná-lo usando um `logging.Filter` para injetar contexto em cada log.

**Passo 3.1: Criar o Filtro de Contexto**
*   **Ação:** Crie um novo arquivo `src/core/context_filter.py`.
*   **Conteúdo:**
    ```python
    import logging

    class ContextFilter(logging.Filter):
        """ Injeta informações de contexto, como o agent_id, nos registros de log. """
        def __init__(self, agent_id: str = "system"):
            super().__init__()
            self.agent_id = agent_id

        def filter(self, record):
            record.agent_id = self.agent_id
            return True
    ```

**Passo 3.2: Atualizar a Configuração de Logging**
*   **Ação:** Modifique o arquivo `src/core/observability.py` (ou onde a configuração de log estiver).
*   **Lógica:** A função `configure_logging` deve agora aceitar um `agent_id` opcional e adicionar o filtro ao handler.
*   **Exemplo de Código:**
    ```python
    # Em src/core/observability.py
    from .context_filter import ContextFilter

    def configure_logging(agent_id: str = "system") -> None:
        # ... (código existente para remover handlers)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        
        # Adicionar o filtro de contexto
        handler.addFilter(ContextFilter(agent_id))
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
        # ... (restante do código)
    ```

**Passo 3.3: Atualizar o `JSONFormatter`**
*   **Ação:** Modifique a classe `JSONFormatter` em `src/core/observability.py` para incluir o novo campo `agent_id`.
*   **Exemplo de Código:**
    ```python
    # Em JSONFormatter.format()
    log_entry = {
        "timestamp": ...,
        "level": record.levelname,
        "agent_id": getattr(record, "agent_id", "system"), # Adicionar esta linha
        "name": record.name,
        # ... (resto dos campos)
    }
    ```

**Passo 3.4: Atualizar os Pontos de Entrada (CLIs)**
*   **Ação:** Modifique `src/cli/admin.py` e `src/cli/agent.py` para passar o `agent_id` ao configurar o logging.
*   **Exemplo em `agent.py`:**
    ```python
    # Na função main() de agent.py
    # ... depois de parsear os args
    from core.observability import configure_logging
    configure_logging(agent_id=args.agent)
    ```

## 4. Fase 2: Configuração da Stack de Observabilidade

**Passo 4.1: Criar Estrutura de Diretórios**
*   **Ação:** A partir da raiz do monorepo (`/mnt/ramdisk/primoia-main/primoia-monorepo`), execute os seguintes comandos:
    ```bash
    mkdir -p observability/loki
    mkdir -p observability/promtail
    mkdir -p observability/grafana/provisioning/datasources
    mkdir -p observability/grafana/provisioning/dashboards
    ```

**Passo 4.2: Criar Arquivos de Configuração**
*   **Ação:** Crie os seguintes arquivos com o conteúdo especificado.

*   **`observability/loki/config.yml`**
    ```yaml
    auth_enabled: false
    server:
      http_listen_port: 3100
    ingester:
      lifecycler:
        address: 127.0.0.1
        ring:
          kvstore:
            store: inmemory
          replication_factor: 1
        final_sleep: 0s
      chunk_idle_period: 1m
      chunk_target_size: 102400
      chunk_retain_period: 30s
    schema_config:
      configs:
        - from: 2020-10-24
          store: boltdb-shipper
          object_store: filesystem
          schema: v11
          index:
            prefix: index_
            period: 24h
    storage_config:
      boltdb_shipper:
        active_index_directory: /loki/boltdb-shipper-active
        cache_location: /loki/boltdb-shipper-cache
        cache_ttl: 24h
        shared_store: filesystem
      filesystem:
        directory: /loki/chunks
    ```

*   **`observability/promtail/config.yml`**
    ```yaml
    server:
      http_listen_port: 9080
      grpc_listen_port: 0

    positions:
      filename: /tmp/positions.yaml

    clients:
      - url: http://loki:3100/loki/api/v1/push

    scrape_configs:
      - job_name: conductor-containers
        docker_sd_configs:
          - host: unix:///var/run/docker.sock
            refresh_interval: 5s
        relabel_configs:
          - source_labels: ['__meta_docker_container_name']
            regex: '/conductor-api-1' # Ajuste o nome do container se necessário
            target_label: 'job'
            replacement: 'conductor'
        pipeline_stages:
          - json:
              expressions:
                level: level
                agent: agent_id
          - labels:
              level: 
              agent:
    ```

*   **`observability/grafana/provisioning/datasources/datasource.yml`**
    ```yaml
    apiVersion: 1

    datasources:
      - name: Loki
        type: loki
        access: proxy
        url: http://loki:3100
        isDefault: true
        jsonData:
          maxLines: 1000
    ```

## 5. Fase 3: Orquestração com Docker Compose

**Passo 5.1: Criar o Docker Compose da Stack**
*   **Ação:** Crie o arquivo `observability/docker-compose.yml`.
*   **Conteúdo:**
    ```yaml
    version: '3.8'

    services:
      loki:
        image: grafana/loki:2.9.0
        ports:
          - "3100:3100"
        volumes:
          - ./loki:/etc/loki
        command: -config.file=/etc/loki/config.yml

      promtail:
        image: grafana/promtail:2.9.0
        volumes:
          - /var/lib/docker/containers:/var/lib/docker/containers:ro
          - /var/run/docker.sock:/var/run/docker.sock
          - ./promtail:/etc/promtail
        command: -config.file=/etc/promtail/config.yml

      grafana:
        image: grafana/grafana:latest
        ports:
          - "3000:3000"
        volumes:
          - ./grafana/provisioning:/etc/grafana/provisioning
    ```

**Passo 5.2: Atualizar o Docker Compose do Conductor**
*   **Ação:** Modifique o arquivo `docker-compose.yml` na raiz do projeto `conductor`.
*   **Lógica:** Adicione a configuração do `logging driver` para que os logs do serviço `conductor` sejam enviados para o Loki.
*   **Exemplo de Código:**
    ```yaml
    # Em conductor/docker-compose.yml
    version: '3.8'

    services:
      conductor:
        build: .
        volumes:
          - ./src:/app/src
        env_file:
          - .env
        logging: # ADICIONAR ESTA SEÇÃO
          driver: loki
          options:
            loki-url: "http://localhost:3100/loki/api/v1/push"
    ```

## 6. Fase 4: Validação e Uso

1.  **Iniciar a Stack:** Na raiz do monorepo, execute `docker compose -f observability/docker-compose.yml up -d`.
2.  **Iniciar o Conductor:** No diretório `projects/conductor`, execute `docker compose up --build`.
3.  **Gerar Logs:** Use a CLI do `conductor` para executar um agente. Ex: `docker compose run --rm conductor --help` ou `docker compose run --rm conductor --agent AgentCreator_Agent --input "..."`.
4.  **Acessar o Grafana:** Abra `http://localhost:3000` no seu navegador.
5.  **Explorar Logs:**
    *   Vá para a seção "Explore".
    *   Selecione o `Loki` como DataSource.
    *   Use a query `{job="conductor"}` para ver todos os logs do `conductor`.
    *   Use a query `{agent="AgentCreator_Agent"} | json` para filtrar os logs de um agente específico e parseá-los como JSON.

## 7. Critérios de Sucesso

A implementação será considerada um sucesso quando:
- [ ] O código da aplicação for atualizado para injetar o `agent_id` nos logs.
- [ ] A stack de observabilidade (`loki`, `promtail`, `grafana`) iniciar corretamente via `docker-compose`.
- [ ] Os logs gerados pela aplicação `conductor` aparecerem na interface do Grafana.
- [ ] For possível filtrar os logs por `level` e `agent` no Grafana.
