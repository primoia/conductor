# 🗨️ Conversation Management

## Overview

Conductor's Conversation Management system provides a robust framework for tracking and managing multi-agent conversations with persistent history and collaborative context. This feature enables seamless interaction between multiple agents working on complex tasks while maintaining a coherent conversation thread.

## Key Features

### 📝 Persistent History
- **Complete Context:** Every conversation is stored with full message history
- **Automatic Tracking:** Conversations are tracked automatically when using MongoDB storage
- **State Preservation:** All agent interactions and their outcomes are preserved

### 👥 Multi-Agent Collaboration
- **Shared Conversations:** Multiple agents can participate in a single conversation thread
- **Agent Handoffs:** Seamlessly transfer context between different specialized agents
- **Collaborative Problem-Solving:** Agents can build upon each other's work

### 🔍 Conversation Retrieval
- **By ID:** Access any conversation using its unique `conversation_id`
- **Full History:** Retrieve complete conversation history with all interactions
- **Context Continuity:** Pick up where you left off with preserved context

### ✏️ Metadata Management
- **Title Editing:** Update conversation titles for better organization
- **Context Updates:** Modify conversation context and metadata
- **Soft Delete:** Archive conversations without permanent deletion

## How It Works

### Storage Configuration

Conversation management is automatically enabled when using MongoDB storage:

```yaml
# config.yaml
storage:
  type: mongodb
  connection_string: mongodb://localhost:27017
  database: conductor_state
```

### API Endpoints

The conversation management system provides RESTful API endpoints:

```
POST   /conversations              # Create new conversation
GET    /conversations/{id}         # Get conversation by ID
PATCH  /conversations/{id}/title   # Update conversation title
PATCH  /conversations/{id}/context # Update conversation context
GET    /conversations/{id}/history # Get conversation history
DELETE /conversations/{id}         # Soft delete conversation
```

### CLI Usage

```bash
# Start a new conversation
conductor --agent MyAgent --chat --input "Let's start a new project"

# Continue an existing conversation
conductor --agent MyAgent --chat --conversation-id <id> --input "Continue analysis"

# Different agent joining the same conversation
conductor --agent AnalysisAgent --chat --conversation-id <id> --input "Review the previous work"
```

## Use Cases

### Complex Multi-Step Tasks

When working on complex projects that require multiple agents:

```bash
# Step 1: Architecture planning
conductor --agent ArchitectAgent --chat --input "Design a microservices architecture"
# conversation_id: abc123

# Step 2: Code generation (same conversation)
conductor --agent CodeGenAgent --chat --conversation-id abc123 --input "Implement the design"

# Step 3: Testing (same conversation)
conductor --agent TestAgent --chat --conversation-id abc123 --input "Create comprehensive tests"
```

### Long-Running Projects

For projects that span multiple sessions:

```bash
# Day 1: Start project
conductor --agent ProjectAgent --chat --input "Initialize new web application"
# Note the conversation_id

# Day 2: Continue project
conductor --agent ProjectAgent --chat --conversation-id <id> --input "Add authentication"

# Day 3: Refine
conductor --agent ProjectAgent --chat --conversation-id <id> --input "Optimize performance"
```

### Team Collaboration

Multiple agents collaborating on the same task:

```bash
# Agent 1: Requirements gathering
conductor --agent RequirementsAgent --chat --input "Gather feature requirements"

# Agent 2: Design (using same conversation)
conductor --agent DesignAgent --chat --conversation-id <id> --input "Create design based on requirements"

# Agent 3: Implementation (using same conversation)
conductor --agent DevAgent --chat --conversation-id <id> --input "Implement the designed solution"
```

## Technical Details

### Data Model

Conversations are stored in MongoDB with the following structure:

```json
{
  "conversation_id": "unique-uuid",
  "title": "Project initialization",
  "created_at": "2025-11-07T10:30:00Z",
  "updated_at": "2025-11-07T14:45:00Z",
  "active_agent": {
    "agent_id": "agent-123",
    "instance_id": "instance-456",
    "name": "ProjectAgent",
    "emoji": "🏗️"
  },
  "participating_agents": [...],
  "is_deleted": false
}
```

### History Management

Task history is linked to conversations via `conversation_id`:

```json
{
  "task_id": "task-789",
  "conversation_id": "conversation-abc123",
  "agent_id": "agent-123",
  "timestamp": "2025-11-07T10:30:00Z",
  "input": "User message",
  "output": "Agent response",
  "context": {...}
}
```

## Best Practices

### 1. Use Descriptive Titles
Update conversation titles to reflect their purpose:
```bash
# Via API
PATCH /conversations/{id}/title
{"title": "User Authentication Feature - Sprint 12"}
```

### 2. Archive Completed Work
Soft delete conversations when work is complete:
```bash
DELETE /conversations/{id}
```

### 3. Leverage Context
Pass conversation IDs when continuing related work:
```bash
conductor --agent DevAgent --chat --conversation-id <id> --input "Continue implementation"
```

### 4. Multi-Agent Coordination
Use the same conversation ID when multiple agents need shared context:
```bash
# Agent 1: Analysis
conductor --agent AnalysisAgent --chat --input "Analyze codebase"
# Note conversation_id

# Agent 2: Refactoring (same conversation)
conductor --agent RefactorAgent --chat --conversation-id <id> --input "Apply suggestions"
```

## Migration

For existing Conductor installations, migration scripts are provided:

```bash
# Migrate histories to conversations
python scripts/migrate_histories_to_conversations.py

# Normalize tasks with conversation IDs
python scripts/normalize_tasks_add_conversation_id.py
```

## Configuration

Default timeout for conversation operations:

```yaml
# config.yaml
timeout: 600  # 10 minutes - allows for long-running agent operations
```

## Related Features

- **[Interactive Sessions](interactive-sessions.md):** Real-time agent interaction
- **[Multi-Provider AI](multi-provider-ai.md):** Using different AI models in conversations
- **[MongoDB Storage](../guides/storage-migration.md):** Setting up MongoDB for conversation persistence

## API Reference

For detailed API documentation, see the FastAPI interactive docs:
```bash
# Start the server
python src/server.py

# Access API docs
http://localhost:8000/docs
```

## Troubleshooting

### Conversation Not Found
**Issue:** `conversation_id` returns 404

**Solution:** Verify the ID is correct and the conversation hasn't been deleted:
```bash
GET /conversations/{id}
```

### Multiple Agents Not Sharing Context
**Issue:** Agents don't see each other's messages

**Solution:** Ensure you're using the same `conversation_id`:
```bash
conductor --agent Agent2 --chat --conversation-id <same-id> --input "message"
```

### MongoDB Connection Issues
**Issue:** Conversations not persisting

**Solution:** Verify MongoDB configuration:
```yaml
storage:
  type: mongodb
  connection_string: mongodb://localhost:27017
```

## Version History

- **v1.1.0** (2025-11-07): Initial conversation management implementation
- **v1.0.0** (2025-01-09): Basic agent interaction (no conversation tracking)

---

**Status:** ✅ Production Ready
**Since:** v1.1.0
**Dependencies:** MongoDB Storage
