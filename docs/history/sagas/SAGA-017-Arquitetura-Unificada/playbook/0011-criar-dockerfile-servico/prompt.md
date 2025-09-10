# Especificação Técnica e Plano de Execução: 0011-criar-dockerfile-servico

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa estabelece a capacidade de empacotar o `ConductorService` como uma unidade de implantação portátil e reprodutível. O uso de um Dockerfile multi-stage garante uma imagem final otimizada e segura, que é a base para qualquer estratégia de DevOps moderna, desde o desenvolvimento local até a produção.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O novo Dockerfile **DEVE** ser nomeado `Dockerfile.service` e localizado na raiz do projeto.
- **Otimização:** A implementação **DEVE** usar "multi-stage builds" para separar o ambiente de build do ambiente de execução, resultando em uma imagem final menor.
- **Segurança:** A imagem final **DEVE** rodar com um usuário não-root.
- **Dependências:** As dependências **DEVEM** ser instaladas usando Poetry.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `Dockerfile.service`**
```dockerfile
# Stage 1: Builder
FROM python:3.10-slim-bullseye AS builder

# Instalar poetry
RUN pip install poetry

# Configurar o ambiente
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copiar arquivos de dependência e instalar
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev && mv .venv /opt/venv

# Copiar código-fonte
COPY src ./src

# ---

# Stage 2: Final Image
FROM python:3.10-slim-bullseye

# Criar usuário não-root
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser/app

# Copiar ambiente virtual e código-fonte do builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src ./src

# Ativar o ambiente virtual
ENV PATH="/opt/venv/bin:$PATH"

# Placeholder para o comando de inicialização do serviço
# Será atualizado quando o serviço tiver um ponto de entrada executável
CMD ["python", "-c", "print('Conductor Service - Ponto de Entrada a ser implementado')"]
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `Dockerfile.service` for criado na raiz do projeto exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
