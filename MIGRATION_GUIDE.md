# 🔄 Migration Guide: Legacy CLIs to Unified Conductor CLI

## 🎯 Overview

Conductor now uses a unified CLI interface that replaces the previous subcommand-based approach with a single, more intuitive syntax.

**The legacy subcommands still work** for backward compatibility, but we recommend migrating to the unified interface for the best experience.

## 📋 Command Migration Reference

### Legacy Subcommands → New Unified Interface

| Old Subcommand | New Unified Command |
|----------------|-------------------|
| `conductor execute --agent X --input Y` | `conductor --agent X --input Y` |
| `conductor chat --agent X --input Y` | `conductor --agent X --chat --input Y` |
| `conductor repl --agent X` | `conductor --agent X --chat --interactive` |
| `conductor list-agents` | `conductor --list` |
| `conductor info --agent X` | `conductor --info X` |
| `conductor validate-config` | `conductor --validate` |
| `conductor install --category web_development` | `conductor --install web_development` |
| `conductor backup` | `conductor --backup` |
| `conductor restore` | `conductor --restore` |

## 🚀 Step-by-Step Migration

### Step 1: Verify Current Setup
```bash
# Test that the unified CLI works
conductor --help
conductor --list
conductor --validate
```

### Step 2: Migrate Common Workflows

#### Creating Agents
```bash
# OLD WAY (subcommands)
conductor repl --agent AgentCreator_Agent --mode dev

# NEW WAY (unified interface)
conductor --agent AgentCreator_Agent --chat --interactive --meta
```

#### Quick Agent Execution
```bash
# OLD WAY (subcommands)
conductor execute --agent TestAgent --environment develop --project myapp --input "Run tests"

# NEW WAY (unified interface)
conductor --agent TestAgent --environment develop --project myapp --input "Run tests"
```

#### Interactive Sessions
```bash
# OLD WAY (subcommands)
conductor repl --agent CodeAnalyst_Agent --environment dev --project app

# NEW WAY (unified interface)
conductor --agent CodeAnalyst_Agent --chat --interactive --environment dev --project app
```

### Step 3: Update Scripts and Automation

#### Bash Scripts
```bash
# OLD
#!/bin/bash
conductor execute --agent SecurityAuditor_Agent --environment prod --project ecommerce --input "Audit security"

# NEW
#!/bin/bash
conductor --agent SecurityAuditor_Agent --environment prod --project ecommerce --input "Audit security"
```

#### CI/CD Pipelines
```yaml
# OLD
- name: Generate commit message
  run: conductor execute --agent CommitMessage_Agent --input "Generate message for: ${{ github.event.head_commit.message }}"

# NEW
- name: Generate commit message
  run: conductor --agent CommitMessage_Agent --input "Generate message for: ${{ github.event.head_commit.message }}"
```

## 🆕 New Features Available

### Interactive Modes
The unified CLI offers three REPL modes:

```bash
# Basic mode (for end users)
conductor repl --agent MyAgent

# Advanced mode (with debug commands)
conductor repl --agent MyAgent --mode advanced

# Developer mode (full features)
conductor repl --agent MyAgent --mode dev
```

### Context-Aware Chat
```bash
# Chat with conversation history
conductor chat --agent MyAgent --input "Your message"

# Continue conversation (preserves context)
conductor chat --agent MyAgent --input "Continue explaining"

# Show conversation history
conductor chat --agent MyAgent --input "Thanks" --show-history
```

### Enhanced Agent Management
```bash
# List all agents with details
conductor list-agents

# Get detailed agent information
conductor info --agent MyAgent

# Install agent templates
conductor install --list
conductor install --agent ReactExpert_Agent

# System validation
conductor validate-config
```

## 🔧 Troubleshooting Migration

### Issue: Command not found
```bash
# If conductor command doesn't work, use Python directly
python src/cli/conductor.py --list

# Or make the script executable
chmod +x conductor
./conductor --list
```

### Issue: Different behavior
```bash
# Compare old vs new behavior
conductor execute --agent AgentCreator_Agent --input "test"
conductor --agent AgentCreator_Agent --input "test"

# They should produce equivalent results
```

### Issue: Missing features
```bash
# All legacy features are available in the unified CLI
# If something seems missing, check the flags:

# For meta-agent operations, use --meta flag
conductor --agent MyAgent --chat --interactive --meta

# For contextual conversations, use --chat flag
conductor --agent MyAgent --chat --input "message"
```

## 📊 Benefits of Migration

### ✅ Improved User Experience
- **Single interface** to learn instead of three
- **Consistent command syntax** across all operations
- **Better help and error messages**
- **Intuitive command names**

### ✅ Enhanced Functionality
- **Three REPL modes** (basic, advanced, dev)
- **Context-aware chat** with history preservation
- **Better agent discovery** and information
- **Integrated template management**

### ✅ Better Development Workflow
- **Unified documentation** and examples
- **Consistent behavior** across environments
- **Easier automation** and scripting
- **Future-proof** interface

## 🎯 Migration Checklist

### For Individual Users
- [ ] Test `conductor --help` works
- [ ] Replace legacy subcommands with unified interface
- [ ] Update personal scripts and aliases
- [ ] Learn new execution modes (stateless, contextual, interactive)

### For Teams
- [ ] Update team documentation
- [ ] Migrate CI/CD pipelines
- [ ] Update onboarding materials
- [ ] Train team members on new interface
- [ ] Update project README files

### For Projects
- [ ] Update build scripts
- [ ] Migrate automation workflows
- [ ] Update deployment scripts
- [ ] Test all automated processes
- [ ] Update project documentation

## 🔄 Gradual Migration Strategy

### Phase 1: Learn (Week 1)
- Use unified CLI alongside legacy CLIs
- Test equivalent commands
- Learn new features (REPL modes, chat)

### Phase 2: Migrate Scripts (Week 2)
- Update personal scripts and aliases
- Migrate development workflows
- Update documentation

### Phase 3: Team Migration (Week 3-4)
- Migrate team processes
- Update CI/CD pipelines
- Train team members

### Phase 4: Full Adoption (Week 4+)
- Use only unified CLI for all work
- Legacy subcommands only for compatibility
- Enjoy improved productivity!

## 💡 Pro Tips

### 1. Use Aliases for Smooth Transition
```bash
# Add to your .bashrc or .zshrc
alias admin-repl='conductor repl --mode dev'
alias agent-exec='conductor execute'
alias agent-repl='conductor repl'
```

### 2. Leverage New Features
```bash
# Use contextual chat for iterative conversations
conductor --agent MyAgent --chat --input "Start analysis"
conductor --agent MyAgent --chat --input "Continue with details"

# Use different execution modes as needed
conductor --agent MyAgent --input "task"                    # Stateless (fast)
conductor --agent MyAgent --chat --input "task"            # Contextual
conductor --agent MyAgent --chat --interactive             # Interactive
```

### 3. Explore Agent Templates
```bash
# Discover new agents
conductor --install list

# Install useful agents
conductor --install web_development
conductor --install SecuritySpecialist_Agent
```

## 🎉 Welcome to the Unified Conductor Experience!

The unified CLI represents a significant improvement in usability while maintaining all the power and flexibility you're used to. Take your time with the migration, and don't hesitate to use both interfaces during the transition period.

**Happy coding with Conductor!** 🚀