# --- Estágio de Build ---
FROM python:3.11-slim as builder

WORKDIR /app

# Instala Poetry
RUN pip install poetry

# Configura Poetry para criar venv no projeto
RUN poetry config virtualenvs.in-project true

# Copia arquivos de configuração do Poetry
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

# Instala dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    curl \
    git \
    procps \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Instala o Gemini CLI globalmente
RUN npm install -g @google/gemini-cli

# Copia o código fonte da aplicação
COPY src/ ./src
COPY config/ ./config

# Cria diretório de logs
RUN mkdir -p logs

# Define o ponto de entrada padrão (pode ser sobrescrito)
ENTRYPOINT ["python", "-m", "src.cli.admin"]