# Conductor Examples

This directory contains practical examples and proof-of-concept implementations demonstrating the core Conductor patterns.

## 🧪 Proof of Concept Files

### Core Implementation Examples

- **`simple-agent-demo.py`** - Simplified demonstration of the core Conductor pattern
  - Shows filesystem reading + local processing + LLM backup
  - Multiple task types: gradle_version, dependency_check, test_status
  - Easy to understand and extend

- **`agent-template.py`** - Complete agent implementation template
  - Production-ready base classes and patterns
  - `ConductorAgentBase` with stats, error handling, LLM integration
  - Specialized agents: `GradleVersionAgent`, `TestExecutorAgent`
  - Hybrid local/LLM processing with confidence scoring

### Analysis and Testing

- **`ollama-analysis.py`** - Detailed analysis of Ollama API usage with a local LLM
  - Shows exact request/response patterns
  - Performance metrics and optimization strategies
  - Different API endpoints (`generate` vs `chat`)

- **`test-conditional-activation.sh`** - Demonstrates conditional agent activation
  - Dependency graph-based activation (only relevant agents run)
  - Cost reduction through smart agent selection
  - Simulates real-world change scenarios

- **`test-hybrid-architecture.sh`** - Multi-tier routing simulation
  - Local LLM → Cheap API → Premium API escalation
  - Complexity-based task routing
  - Cost optimization demonstration

## 🚀 Key Concepts Demonstrated

### 1. **Filesystem + LLM Pattern**
```python
# Core workflow proven in examples:
1. 📁 Read files from filesystem (build.gradle, test files, etc.)
2. 🔍 Process locally when possible (regex, parsing) 
3. 🤖 Use LLM for complex analysis/extraction
4. ✅ Return structured results with confidence scores
```

### 2. **Hybrid Processing Strategy**
- **Local first**: Fast regex/parsing for deterministic tasks
- **LLM backup**: When local processing has low confidence
- **Cost optimization**: $0.00 for local LLM, escalate only when needed

### 3. **Agent Specialization**
- Each agent has a specific, narrow responsibility
- Standardized input/output formats
- Built-in statistics and performance monitoring
- Easy to extend and customize

## 🛠️ How to Run

### Prerequisites
- Ensure you have an LLM configured in `config/ai_providers.yaml` (e.g., a local Ollama instance or a cloud provider like Google Gemini or Anthropic Claude).

### Run Examples
```bash
# Simple demo
poetry run python examples/simple-agent-demo.py

# Full agent template demo  
poetry run python examples/agent-template.py

# Test conditional activation
bash examples/test-conditional-activation.sh

# Test hybrid architecture
bash examples/test-hybrid-architecture.sh
```

## 🎯 Next Steps

These examples prove the core concepts work. For production implementation:

1. **Integrate with real CI/CD** (GitHub Actions, Jenkins)
2. **Add more specialized agents** (security, performance, documentation)
3. **Implement orchestrator** with dependency graphs
4. **Scale to multiple projects** with shared agent pool

The foundation is solid - now it's time to build the full system! 🚀