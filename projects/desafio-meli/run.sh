#!/bin/bash
# Script to build and start the application using Docker Compose

echo "Building and starting the application..."
docker compose up --build -d

echo "Application running at http://localhost:8000"
echo "Documentation (Swagger UI) available at http://localhost:8000/docs"