FROM python:3.9-slim

WORKDIR /app

# Install git and other necessary system dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Diagnostic step to verify git installation
RUN ls -l /usr/bin/git

# Configure git to trust the mounted monorepo directory
RUN git config --global --add safe.directory /monorepo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# The directory of the monorepo will be mounted as a volume in /monorepo
VOLUME /monorepo

# The entry command will execute the agent
ENTRYPOINT ["python", "-m", "src"]