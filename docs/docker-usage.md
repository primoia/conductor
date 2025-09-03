# Docker Usage Guide - Conductor Framework

This guide documents how to use the Conductor Framework with Docker, including specific configurations for integration with Google Cloud and Vertex AI.

## Building the Image

```bash
# Build the image (with cache)
docker compose build

# Force rebuild the image (without cache)
docker compose build --no-cache
```

## Basic Execution

### Admin CLI

```bash
# Admin CLI Help (Docker Compose)
docker compose run --rm --entrypoint="" conductor-api python -m src.cli.admin --help

# Admin CLI Help (Python directly)
poetry run python -m src.cli.admin --help

# Execute meta-agent (e.g., AgentCreator_Agent) in REPL mode (Docker Compose)
# The Admin CLI operates on framework meta-agents, not external projects.
docker compose run --rm \
  --entrypoint="python -m src.cli.admin" \
  conductor-api \
  --agent AgentCreator_Agent --ai-provider gemini --repl --timeout 300

# Execute meta-agent (e.g., AgentCreator_Agent) in REPL mode (Python directly)
poetry run python -m src.cli.admin \
  --agent AgentCreator_Agent --ai-provider gemini --repl --timeout 300

# Execute meta-agent with direct input (non-interactive) (Docker Compose)
docker compose run --rm \
  --entrypoint="python -m src.cli.admin" \
  conductor-api \
  --agent AgentCreator_Agent --ai-provider gemini --input "Create a new agent called TestAgent." --timeout 300

# Execute meta-agent with direct input (non-interactive) (Python directly)
poetry run python -m src.cli.admin \
  --agent AgentCreator_Agent --ai-provider gemini --input "Create a new agent called TestAgent." --timeout 300

# Execute meta-agent in simulation mode (without calling the real AI provider) (Docker Compose)
docker compose run --rm \
  --entrypoint="python -m src.cli.admin" \
  conductor-api \
  --agent AgentCreator_Agent --ai-provider gemini --simulate-chat --repl --timeout 300

# Execute meta-agent in simulation mode (without calling the real AI provider) (Python directly)
poetry run python -m src.cli.admin \
  --agent AgentCreator_Agent --ai-provider gemini --simulate-chat --repl --timeout 300
```

### Agent CLI

```bash
# Agent CLI Help (Docker Compose)
docker compose run --rm --entrypoint="" conductor-api python -m src.cli.agent --help

# Agent CLI Help (Python directly)
poetry run python -m src.cli.agent --help

# Execute project agent (e.g., ProblemRefiner_Agent) in REPL mode with target project mounted (Docker Compose)
# The target project is mounted to /app/projects/src for access by agent scripts.
docker compose run --rm \
  --entrypoint="python -m src.cli.agent" \
  -v "/mnt/ramdisk/develop/nex-web-backend:/app/projects/src" \
  conductor-api \
  --environment develop \
  --project nex-web-backend \
  --agent ProblemRefiner_Agent \
  --ai-provider gemini \
  --repl --timeout 300

# Execute project agent (e.g., ProblemRefiner_Agent) in REPL mode (Python directly)
# Ensure your current working directory is the root of the target project.
# Or, adjust the --project-root parameter if the agent needs to access files outside the current directory.
poetry run python -m src.cli.agent \
  --environment develop \
  --project nex-web-backend \
  --agent ProblemRefiner_Agent \
  --ai-provider gemini \
  --repl --timeout 300
```

## Integration with Google Cloud Vertex AI

To use Gemini with Vertex AI within the container, you can configure the environment variables. The Conductor framework will automatically use Vertex AI if these variables are set and `GOOGLE_GENAI_USE_VERTEXAI` is true.

### Configuration with Service Account

```bash
docker run --rm \
  -v "/path/to/your/project:/app" \
  -v "/path/to/service-account-key.json:/gcp_key.json" \
  -e "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json" \
  -e "GOOGLE_GENAI_USE_VERTEXAI=true" \
  -e "GOOGLE_CLOUD_PROJECT=your-project-id" \
  -e "GOOGLE_CLOUD_LOCATION=us-central1" \
  conductor-api \
  # Your Conductor command here, e.g., python -m src.cli.agent ...
```

## Important Environment Variables

### Conductor Configuration

```bash
# .env file for development
LOG_LEVEL=INFO
JSON_LOGGING=true
ENVIRONMENT=develop
DEBUG_MODE=false
DEFAULT_TIMEOUT=120

# For MongoDB (optional)
MONGO_URI=mongodb://mongodb:27017/conductor_state
```

### Google Cloud Configuration

```bash
# Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# API Key (alternative to service account)
GOOGLE_API_KEY=your-api-key
```

## Volumes and Mounts

### Recommended Volume Structure

```bash
# For development: mount the 'conductor' project root directory to /app
# This allows hot-reload and access to all project files.
docker run --rm \
  -v "$(pwd):/app" \
  -v "/path/to/gcp-key.json:/gcp_key.json" \
  conductor-api
```

### Specific Mounts

- **Conductor Project**: `-v "$(pwd):/app"` for hot-reload during development and full code access.
- **Logs**: `-v "$(pwd)/logs:/app/logs"` to persist logs.
- **Target Project**: `-v "/path/to/target/project:/app/projects/src"` to work on external projects (the agent expects the target project's source code in `/app/projects/src`).
- **GCP Keys**: `-v "/path/to/key.json:/gcp_key.json"` for authentication.

## Docker Compose with Services

```yaml
# docker-compose.yml configured
version: '3.8'

services:
  conductor:
    build: .
    volumes:
      - .:/app  # Mounts the 'conductor' project root directory to /app
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

## Useful Commands

```bash
# Execute interactive bash in the container (via docker compose)
docker compose run --rm --entrypoint="" conductor-api bash

# Verify installations
docker run --rm conductor-api node --version
docker run --rm conductor-api npm list -g

# Execute tests in the container
docker run --rm -v "$(pwd):/app" conductor-api poetry run pytest

# Container logs
docker compose logs conductor

# Clean up resources
docker compose down -v
docker system prune
```

## Troubleshooting

### Common Issues

1. **GCP permission error**: Verify if the service account has the necessary permissions
2. **File not found**: Verify if volumes are mounted correctly
3. **Timeout**: Adjust `DEFAULT_TIMEOUT` variable for long operations
4. **Memory**: For large projects, you might need to increase Docker memory
5. **ModuleNotFoundError (Python Dependencies)**:
   - If a Python module is not found, verify that the dependency is correctly listed in `pyproject.toml`.
   - Run `poetry update` locally to update the `poetry.lock`.
   - Rebuild the Docker image with `docker compose build --no-cache` to ensure the dependency is installed in the container.

### Debugging

```bash
# Execute with debug enabled
docker run --rm -e DEBUG_MODE=true conductor-api python -m src.cli.admin --debug --agent TestAgent

# Check environment variables
docker run --rm conductor-api env | grep GOOGLE

# Test connectivity with Vertex AI
docker run --rm \
  -v "/path/to/key.json:/gcp_key.json" \
  -e "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json" \
  conductor-api \
  gcloud auth application-default print-access-token
```

---

**Note**: This document will be updated as Vertex AI integration is implemented in the Conductor infrastructure.