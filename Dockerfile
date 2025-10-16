# projects/conductor/Dockerfile

# --- Estágio 1: Builder ---
# Instala dependências em um ambiente virtual isolado
FROM python:3.11-slim as builder

WORKDIR /app

# Instala o Poetry
RUN pip install poetry

# Configura Poetry para criar venv no projeto
RUN poetry config virtualenvs.in-project true

# Copia os arquivos de definição de dependências
# O contexto do build é ./projects/conductor, então os caminhos são relativos a essa pasta
COPY ./poetry.lock ./pyproject.toml /app/

# Instala as dependências, sem as de desenvolvimento, em um venv
RUN poetry install --only main --no-root

# --- Estágio 2: Final ---
# Cria a imagem final, menor e mais limpa
FROM python:3.11-slim

WORKDIR /app

# Expõe a porta que a API vai usar
EXPOSE 8000

# Copia o ambiente virtual com as dependências do estágio builder
COPY --from=builder /app/.venv /.venv

# Define o PATH para usar o python do venv
ENV PATH="/.venv/bin:$PATH"
ENV PYTHONPATH=/app

# Copia o código fonte da aplicação
COPY ./src ./src
COPY ./config.yaml .

# Cria o diretório .conductor_workspace se não existir
RUN mkdir -p ./.conductor_workspace
COPY ./.conductor_workspace ./.conductor_workspace

# Comando para iniciar o servidor FastAPI quando o contêiner rodar
CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]