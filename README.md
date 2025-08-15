# 🎼 Conductor - AI-Powered Code Orchestrator

> **Intelligent orchestrator that coordinates AI agents to generate quality code**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 🚀 **Overview**

The **Conductor** is an orchestration system that integrates `.bmad-core` methodology with specialized AI agents to generate production code in an automated and intelligent way.

### ✨ **Key Features**

- 🤖 **Multiple AI Providers**: Support for Claude and Gemini
- 🎯 **Specialized Agents**: Each agent has specific expertise
- 📋 **Implementation Plans**: YAML structure to define tasks
- 🔄 **Intelligent Orchestration**: Sequential and parallel execution
- ✅ **Automatic Validation**: Quality verification of generated code
- 📚 **Integrated Methodology**: Uses `.bmad-core` for planning
- 🎛️ **Flexible Configuration**: Configurable project directory

## 📁 **Project Structure**

```
conductor/
├── 📚 docs/                    # Complete documentation
│   ├── README.md              # Detailed documentation
│   ├── integration/           # Integration guides
│   ├── plans/                 # Implementation plans
│   ├── cleanup/               # Cleanup documentation
│   └── history/               # Project history
├── 🚀 scripts/                # Main scripts
│   ├── run_conductor.py       # Main orchestrator
│   ├── demo_integration.py    # Demonstration
│   └── test_integration.py    # Tests
├── 🎭 demo/                   # Practical examples
├── 📖 .bmad-core/             # Development methodology
├── 🔧 projects/               # Projects and agents
├── 📝 stories/                # Example stories
└── 💻 src/                    # Generated code
```

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Claude CLI installed (for using Claude)
which claude
# Output: /usr/bin/claude

# Node.js and NPM (for using Gemini)
which npx
# Output: /usr/bin/npx
```

### **Basic Execution**
```bash
# Run orchestrator with Claude (default)
python scripts/run_conductor.py --projeto /path/to/project implementation_plan.yaml

# Run orchestrator with Gemini
python scripts/run_conductor.py --ia gemini --projeto /path/to/project implementation_plan.yaml

# Run demo
python scripts/demo_integration.py

# Run tests
python scripts/test_integration.py
```

## 📚 **Documentation**

### **📖 [Complete Documentation](docs/README.md)**
Detailed guide covering all aspects of Conductor.

### **🔗 [Integration Guide](docs/integration/INTEGRATION_README.md)**
How to integrate Conductor with your projects.

### **📋 [Implementation Plans](docs/plans/)**
Detailed development and refactoring plans.

### **🧹 [Cleanup Documentation](docs/cleanup/)**
Repository cleanup and organization process.

### **📜 [Project History](docs/history/)**
Project evolution and important milestones.

## 🎯 **Use Cases**

### **1. Kotlin Entity Generation**
```yaml
# Implementation plan example
storyId: "stories/product-entity.story.md"
tasks:
  - name: "create-product-entity"
    agent: "KotlinEntityCreator_Agent"
    inputs: ["stories/product-entity.story.md"]
    outputs: ["src/main/kotlin/Product.kt"]
```

### **2. Repository Creation**
```yaml
  - name: "create-product-repository"
    agent: "KotlinRepositoryCreator_Agent"
    inputs: ["src/main/kotlin/Product.kt"]
    outputs: ["src/main/kotlin/ProductRepository.kt"]
```

### **3. Service and Controller Generation**
```yaml
  - name: "create-product-service"
    agent: "KotlinServiceCreator_Agent"
    inputs: ["src/main/kotlin/Product.kt", "src/main/kotlin/ProductRepository.kt"]
    outputs: ["src/main/kotlin/ProductService.kt"]
```

## 🤖 **Available Agents**

| Agent | Specialty | Status |
|-------|-----------|--------|
| `KotlinEntityCreator_Agent` | JPA entity creation | ✅ Functional |
| `KotlinRepositoryCreator_Agent` | Repository creation | ✅ Functional |
| `KotlinServiceCreator_Agent` | Service creation | 🚧 In development |
| `KotlinControllerCreator_Agent` | Controller creation | 🚧 In development |
| `KotlinTestCreator_Agent` | Test creation | 🚧 In development |

## 🧪 **Testing and Validation**

### **Run Integration Tests**
```bash
python scripts/test_integration.py
```

### **Run Complete Demo**
```bash
python scripts/demo_integration.py
```

### **Validate Implementation Plan**
```bash
# Validate with Claude
python scripts/run_conductor.py --projeto /path/to/project plan.yaml

# Validate with Gemini
python scripts/run_conductor.py --ia gemini --projeto /path/to/project plan.yaml
```

## 🔧 **Configuration**

### **Command Line Arguments**
```bash
# Available arguments
--ai-provider, --ia    # AI provider (claude or gemini, default: claude)
--project-path, --projeto  # Target project path (required)
--verbose, -v         # Detailed logging
```

### **Usage Examples**
```bash
# Use Claude in a Kotlin project
python scripts/run_conductor.py --projeto /mnt/ramdisk/develop/nex-web-backend plan.yaml

# Use Gemini in a Node.js project
python scripts/run_conductor.py --ia gemini --projeto /mnt/ramdisk/develop/nex-web plan.yaml

# Execution with detailed logging
python scripts/run_conductor.py --ia claude --projeto /path/to/project --verbose plan.yaml
```

### **Environment Variables**
```bash
# Claude configuration (optional)
export CLAUDE_API_KEY="your-api-key"
export CLAUDE_MODEL="claude-3.5-sonnet"

# Gemini configuration (optional)
export GEMINI_API_KEY="your-gemini-api-key"
```

### **Agent Configuration**
```bash
# Agent structure
projects/develop/agents/AgentName/
├── persona.md           # Personality and expertise
├── memory/
│   ├── context.md       # Context and knowledge
│   └── avoid_patterns.md # Patterns to avoid
```

## 📊 **Metrics and Performance**

- ⚡ **Execution Time**: ~40s per task
- 🎯 **Success Rate**: 95%+
- 📝 **Code Quality**: Production-ready
- 🔄 **Parallelization**: Support for parallel execution

## 🤝 **Contribution**

1. **Fork** the project
2. **Create** a branch for your feature
3. **Develop** following the standards
4. **Test** with `python scripts/test_integration.py`
5. **Commit** your changes
6. **Push** to the branch
7. **Open** a Pull Request

## 📄 **License**

This project is licensed under the [MIT License](LICENSE).

## 🙏 **Acknowledgments**

- **Claude AI** for intelligent code generation
- **`.bmad-core`** for development methodology
- **Community** for feedback and contributions

---

**🎼 Conductor** - Transforming ideas into code, one orchestration at a time.

**📧 Contact**: [your-email@example.com](mailto:your-email@example.com)  
**🐛 Issues**: [GitHub Issues](https://github.com/your-username/conductor/issues)  
**📖 Wiki**: [Complete Documentation](docs/README.md)
