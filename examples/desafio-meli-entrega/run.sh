#!/bin/bash
# Script para construir e iniciar a aplicação usando Docker Compose

echo "Construindo e iniciando a aplicação..."
docker compose up --build -d

echo "Aplicação rodando em http://localhost:8000"
echo "Documentação (Swagger UI) disponível em http://localhost:8000/docs"
