# Meli Challenge - Item Details API

API developed as part of Mercado Livre's backend technical challenge.

This project creates a containerized API to serve product details, following best practices in software architecture, testing, and automation.

**Tech Stack:**
*   Python 3.11+
*   FastAPI
*   Poetry
*   Pytest
*   Docker & Docker Compose

## How to Run

This project is fully containerized. The only prerequisite is having **Docker** and **Docker Compose** installed.

For detailed instructions on how to build the image, start the application, stop the application, and run the tests, please refer to the document:

➡️ **[./run.md](./run.md)**

## Architecture Diagram

The application follows a layered architecture (Ports and Adapters) that clearly separates responsibilities:

```mermaid
graph TD
    A[Client/HTTP Requests] --> B[FastAPI - API Layer]
    B --> C[Service Layer]
    C --> D[Repository Layer] 
    D --> E[Data Layer - JSON File]
    
    subgraph "API Layer"
        B1[GET /api/v1/items/{id}]
        B2[POST /api/v1/items]  
        B3[PUT /api/v1/items/{id}]
        B4[DELETE /api/v1/items/{id}]
    end
    
    subgraph "Service Layer"
        C1[ItemService]
        C2[Business Logic]
        C3[ItemNotFoundException]
    end
    
    subgraph "Repository Layer"  
        D1[ItemRepository]
        D2[find_by_id]
        D3[save]
        D4[delete]
    end
    
    subgraph "Data Layer"
        E1[items.json]
        E2[Configuration via .env]
    end
    
    subgraph "Cross-Cutting Concerns"
        F1[JSON Structured Logging]
        F2[Pydantic Validation]
        F3[Exception Handling]
    end
    
    B --> B1
    B --> B2  
    B --> B3
    B --> B4
    
    C --> C1
    C --> C2
    C --> C3
    
    D --> D1
    D --> D2
    D --> D3  
    D --> D4
    
    E --> E1
    E --> E2
    
    C -.-> F1
    B -.-> F2
    B -.-> F3
```

**Architecture Benefits:**
- **Separation of Responsibilities:** Each layer has a specific function
- **Testability:** Isolated layers allow effective unit testing
- **Maintainability:** Changes in one layer do not affect others
- **Scalability:** Easy component replacement (e.g., JSON → Database)

## Logging and Observability Strategy

This project implements a structured logging strategy that facilitates integration with any modern observability platform.

### Logging Approach

**Structured JSON Format:** All logs are emitted in structured JSON format to `stdout`, facilitating:
- Automatic parsing by log aggregation systems
- Efficient filtering and searching by specific fields
- Native integration with stacks like ELK, Splunk, Datadog, etc.

**Example log output:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "name": "app.services.item_service",
  "message": "Item found: iPhone 14 Pro Max (ID: MLB123456789)",
  "module": "item_service",
  "function": "get_item_by_id",
  "line": 56
}
```

### Integration with Observability Platforms

The `stdout` logging pattern allows seamless integration with any system:

**Example - Papertrail via Syslog Driver:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logs.papertrailapp.com:XXXXX"
        tag: "desafio-meli-api"
```

**Other supported integrations:**
- AWS CloudWatch Logs (`awslogs` driver)
- Google Cloud Logging (`gcplogs` driver)
- Fluentd (`fluentd` driver)
- Splunk (`splunk` driver)

## Project Structure

### Saga 01 - Foundation
The project architecture establishes the foundation for development:

-   `app/main.py`: FastAPI application entry point and "Hello World" endpoint.
-   `tests/test_api.py`: Integration test for the "Hello World" endpoint.
-   `Dockerfile`: Recipe for building the application image.
-   `docker-compose.yml`: Orchestrates container execution.
-   `pyproject.toml` / `poetry.lock`: Dependency management.
-   `docs/sagas/`: Incremental documentation of architecture and project decisions.

## Key Architectural Decisions

This project was built with several intentional architectural decisions to ensure robustness, maintainability, and alignment with modern software engineering practices:

1.  **Layered Architecture (Ports and Adapters):** The application is divided into distinct layers (API, Services, Repository) to separate responsibilities. This ensures that business logic (`services`) does not depend on implementation details, such as the web framework (`api`) or the persistence method (`repository`).

2.  **Containerization with Docker:** The entire development and production environment is containerized. This solves the "it works on my machine" problem, ensures consistency across environments, and drastically simplifies project execution for anyone. The multi-stage `Dockerfile` creates an optimized final image, containing only what is necessary for execution.

3.  **Structured Logging to `stdout`:** Following the "Twelve-Factor App" methodology, the application does not write logs to files. Instead, it emits structured logs (JSON) to standard output, delegating the responsibility of collection and storage to the execution environment (Docker). This makes the application platform-agnostic regarding observability and ready for integration with enterprise-level monitoring systems.

4.  **Dependency Management with Poetry:** We use Poetry and its `poetry.lock` file to ensure 100% reproducible builds. Anyone building the project will have the exact same set of dependencies, eliminating version conflicts.

## Technical Strategy and AI Usage

Development efficiency was enhanced through a combination of modern tools and an AI-assisted workflow.

-   **Tech Stack:** The choice of **Python/FastAPI** was deliberate to maximize development speed, leverage native data validation with Pydantic, and obtain API documentation (Swagger UI) automatically.
-   **Architect/Implementer Workflow:** We used a collaboration model where an AI (Gemini) acts as the **Software Architect**, responsible for planning, design, documentation, and review. Another AI (Claude) acts as the **Implementer**, focused on translating the architect's blueprints into clean and functional code. This process, documented in `prompts.md`, allowed a clear separation of responsibilities and accelerated the development cycle.

## Project Plan

This project was developed following an incremental methodology documented through "sagas." Each saga represents a development stage with specific objectives and well-defined acceptance criteria.

**Complete Plan Documentation:** The `docs/sagas/` folder contains detailed documentation for each phase of the project:

- **Saga 01 - Foundation:** Basic structure, containerization, and "Hello World"
- **Saga 02 - The Item:** Implementation of business logic with clean architecture
- **Saga 02a - Observability:** Structured JSON logging for monitoring
- **Saga 03 - Configuration and Modification:** External configurations and POST endpoint
- **Saga 03.1 - Complete CRUD:** Implementation of UPDATE and DELETE with E2E tests
- **Saga 04 - Final Documentation:** Architecture diagrams and packaging

## API Endpoints

The API offers complete CRUD operations for item management:

### **GET** `/api/v1/items/{item_id}`
Fetches a specific item by ID.
- **Status**: `200 OK` | `404 Not Found`
- **Response**: `Item` object with all fields

### **POST** `/api/v1/items`  
Creates a new item.
- **Status**: `201 Created` | `422 Validation Error`
- **Payload**: `ItemCreateModel` (all fields except `id`)
- **Response**: `Item` object created with automatically generated `id`

### **PUT** `/api/v1/items/{item_id}`
Updates an existing item (partial update supported).
- **Status**: `200 OK` | `404 Not Found` | `422 Validation Error`  
- **Payload**: `ItemUpdateModel` (all optional fields)
- **Response**: Updated `Item` object

### **DELETE** `/api/v1/items/{item_id}`
Removes an item.
- **Status**: `204 No Content` | `404 Not Found`
- **Response**: Empty body

### Project Structure

### Saga 01 - Foundation
Basic structure and containerization:

-   `app/main.py`: FastAPI application entry point and "Hello World" endpoint
-   `tests/test_api.py`: Comprehensive integration test suite
-   `Dockerfile`: Recipe for building the application image
-   `docker-compose.yml`: Orchestrates container execution
-   `pyproject.toml` / `poetry.lock`: Dependency management
-   `docs/sagas/`: Incremental documentation of architecture and decisions

### Saga 02-04 - Complete Implementation  
Full functionalities with clean architecture:

-   `app/models/item.py`: Pydantic models (Item, ItemCreateModel, ItemUpdateModel)
-   `app/repository/item_repository.py`: Persistence layer with CRUD operations
-   `app/services/item_service.py`: Business logic and custom exceptions  
-   `app/api/v1/items.py`: Complete REST endpoints with dependency injection
-   `app/core/config.py`: Centralized configuration with pydantic-settings
-   `app/core/logging_config.py`: Structured JSON logging for observability
-   `data/items.json`: Simulated database for development
-   `tests/`: Complete suite with unit, integration, and E2E tests