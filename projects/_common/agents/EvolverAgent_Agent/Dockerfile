FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# The directory of the monorepo will be mounted as a volume in /monorepo
VOLUME /monorepo

# The entry command will execute the agent
ENTRYPOINT ["python", "-m", "src"]