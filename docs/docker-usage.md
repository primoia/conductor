# Docker Usage Guide - Conductor Framework

Este guia documenta como usar o Conductor Framework com Docker, incluindo configurações específicas para integração com Google Cloud e Vertex AI.

## Construção da Imagem

```bash
# Construir a imagem (com cache)
docker compose build

# Forçar reconstrução da imagem (sem cache)
docker compose build --no-cache
```

## Execução Básica

### Admin CLI

# Help do Admin CLI
docker compose run --rm --entrypoint="" conductor-api python -m src.cli.admin --help

# Executar meta-agent (ex: AgentCreator_Agent) em modo REPL
# O Admin CLI opera em meta-agentes do framework, não em projetos externos.
docker compose run --rm \
  --entrypoint="python -m src.cli.admin" \
  conductor-api \
  --agent AgentCreator_Agent --ai-provider gemini --repl --timeout 300

# Executar meta-agent com input direto (não interativo)
docker compose run --rm \
  --entrypoint="python -m src.cli.admin" \
  conductor-api \
  --agent AgentCreator_Agent --ai-provider gemini --input "Crie um novo agente chamado TesteAgent." --timeout 300

# Executar meta-agent em modo simulação (sem chamar o provedor de IA real)
docker compose run --rm \
  --entrypoint="python -m src.cli.admin" \
  conductor-api \
  --agent AgentCreator_Agent --ai-provider gemini --simulate-chat --repl --timeout 300



### Agent CLI

```bash
# Help do Agent CLI  
docker compose run --rm --entrypoint="" conductor-api python -m src.cli.agent --help

# Executar agente de projeto (ex: ProblemRefiner_Agent) em modo REPL com projeto alvo montado
# O projeto alvo é montado em /app/projects/src para acesso pelos scripts do agente.
docker compose run --rm \
  --entrypoint="python -m src.cli.agent" \
  -v "/mnt/ramdisk/develop/nex-web-backend:/app/projects/src" \
  conductor-api \
  --environment develop \
  --project nex-web-backend \
  --agent ProblemRefiner_Agent \
  --ai-provider gemini \
  --repl --timeout 300

```

## Integração com Google Cloud Vertex AI

Para usar o Gemini CLI com Vertex AI dentro do container, você pode executar comandos diretamente:

### Configuração com Service Account

```bash
docker run --rm \
  -v "/path/to/your/project:/app" \
  -v "/path/to/service-account-key.json:/gcp_key.json" \
  -e "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json" \
  -e "GOOGLE_GENAI_USE_VERTEXAI=true" \
  -e "GOOGLE_CLOUD_PROJECT=your-project-id" \
  -e "GOOGLE_CLOUD_LOCATION=us-central1" \
  conductor-api \
  npx https://github.com/google-gemini/gemini-cli -p "Seu prompt aqui file: /app/arquivo.md"
```

### Exemplo Prático

```bash
# Exemplo real de uso com o projeto fake_project
docker run --rm \
  -v "/mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/tests/fake_project:/app" \
  -v "/home/cezar/.gcp/keys/conductor-key.json:/gcp_key.json" \
  -e "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json" \
  -e "GOOGLE_GENAI_USE_VERTEXAI=true" \
  -e "GOOGLE_CLOUD_PROJECT=gen-lang-client-0338424173" \
  -e "GOOGLE_CLOUD_LOCATION=us-central1" \
  conductor-api \
  npx https://github.com/google-gemini/gemini-cli -p "Crie uma persona com dois parágrafos file: /app/README.md"
```

## Variáveis de Ambiente Importantes

### Configuração do Conductor

```bash
# Arquivo .env para desenvolvimento
LOG_LEVEL=INFO
JSON_LOGGING=true
ENVIRONMENT=develop
DEBUG_MODE=false
DEFAULT_TIMEOUT=120

# Para MongoDB (opcional)
MONGO_URI=mongodb://mongodb:27017/conductor_state
```

### Configuração do Google Cloud

```bash
# Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# API Key (alternativa ao service account)
GOOGLE_API_KEY=your-api-key
```

## Volumes e Montagens

### Estrutura de Volumes Recomendada

```bash
# Para desenvolvimento: montar o diretório raiz do projeto 'conductor' em /app
# Isso permite hot-reload e acesso a todos os arquivos do projeto.
docker run --rm \
  -v "$(pwd):/app" \
  -v "/path/to/gcp-key.json:/gcp_key.json" \
  conductor-api
```

### Montagens Específicas

- **Projeto Conductor**: `-v "$(pwd):/app"` para hot-reload durante desenvolvimento e acesso completo ao código.
- **Logs**: `-v "$(pwd)/logs:/app/logs"` para persistir logs.
- **Projeto alvo**: `-v "/path/to/target/project:/app/projects/src"` para trabalhar em projetos externos (o agente espera o código-fonte do projeto alvo em `/app/projects/src`).
- **Chaves GCP**: `-v "/path/to/key.json:/gcp_key.json"` para autenticação.

## Docker Compose com Serviços

```yaml
# docker-compose.yml configurado
version: '3.8'

services:
  conductor:
    build: .
    volumes:
      - .:/app  # Monta o diretório raiz do projeto 'conductor' em /app
      - ./logs:/app/logs
      - /path/to/gcp-key.json:/gcp_key.json
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json
      - GOOGLE_GENAI_USE_VERTEXAI=true
      - GOOGLE_CLOUD_PROJECT=your-project-id
      - GOOGLE_CLOUD_LOCATION=us-central1
    env_file:
      - .env
    
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_DATABASE: conductor_state
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

## Integração Futura com GeminiCLIClient

Para integrar o comando documentado na infraestrutura do Conductor, será necessário:

### 1. Adaptação do GeminiCLIClient

```python
# src/infrastructure/llm/cli_client.py
class GeminiCLIClient(BaseCLIClient):
    def invoke(self, prompt: str) -> str:
        # Usar npx gemini-cli com configuração Vertex AI
        cmd = [
            "npx", 
            "https://github.com/google-gemini/gemini-cli",
            "-p", 
            self._build_full_prompt_with_persona(prompt)
        ]
        
        # Adicionar configuração do ambiente se disponível
        env = os.environ.copy()
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            env['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if os.getenv('GOOGLE_GENAI_USE_VERTEXAI'):
            env['GOOGLE_GENAI_USE_VERTEXAI'] = 'true'
        
        # Executar comando...
```

### 2. Configuração no Container

```python
# src/config.py - adicionar configurações GCP
class Settings(BaseSettings):
    # ... configurações existentes
    
    # Google Cloud Configuration
    google_application_credentials: Optional[str] = None
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us-central1"
    google_genai_use_vertexai: bool = False
```

## Comandos Úteis

```bash
# Executar bash interativo no container (via docker compose)
docker compose run --rm --entrypoint="" conductor-api bash

# Verificar instalações
docker run --rm conductor-api node --version
docker run --rm conductor npm list -g

# Executar testes no container
docker run --rm -v "$(pwd):/app" conductor-api poetry run pytest

# Logs do container
docker compose logs conductor

# Limpar recursos
docker compose down -v
docker system prune
```

## Troubleshooting

### Problemas Comuns

1. **Erro de permissão GCP**: Verificar se o service account tem as permissões necessárias
2. **Arquivo não encontrado**: Verificar se os volumes estão montados corretamente
3. **Timeout**: Ajustar variável `DEFAULT_TIMEOUT` para operações longas
4. **Memória**: Para projetos grandes, pode ser necessário aumentar memória do Docker
5. **ModuleNotFoundError (Dependências Python)**:
   - Se um módulo Python não for encontrado, verifique se a dependência está listada corretamente no `pyproject.toml`.
   - Execute `poetry update` localmente para atualizar o `poetry.lock`.
   - Reconstrua a imagem Docker com `docker compose build --no-cache` para garantir que a dependência seja instalada no contêiner.

### Debug

```bash
# Executar com debug habilitado
docker run --rm -e DEBUG_MODE=true conductor-api python -m src.cli.admin --debug --agent TestAgent

# Verificar variáveis de ambiente
docker run --rm conductor-api env | grep GOOGLE

# Testar conectividade com Vertex AI
docker run --rm \
  -v "/path/to/key.json:/gcp_key.json" \
  -e "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json" \
  conductor-api \
  gcloud auth application-default print-access-token
```

---

**Nota**: Este documento será atualizado conforme a integração com Vertex AI for implementada na infraestrutura do Conductor.
