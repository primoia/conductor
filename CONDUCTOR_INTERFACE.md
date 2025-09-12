# 🎯 Conductor Interface (Unified CLI)

## Quick Reference

| Flag | Purpose | Example |
|------|---------|---------|
| `--list` | List agents | `conductor --list` |
| `--agent --input` | Stateless execution | `conductor --agent X --input "task"` |
| `--chat --input` | Contextual execution | `conductor --agent X --chat --input "task"` |
| `--chat --interactive` | Interactive REPL | `conductor --agent X --chat --interactive` |
| `--info` | Agent info | `conductor --info X` |
| `--validate` | Validate system | `conductor --validate` |
| `--install` | Install templates | `conductor --install web_development` |
| `--backup` | Backup agents | `conductor --backup` |
| `--restore` | Restore agents | `conductor --restore` |
| `--output json` | JSON output | `conductor --agent X --input "task" --output json` |
| `--new-agent-id` | New agent ID (meta mode) | `conductor --agent AgentCreator_Agent --meta --chat --input "create" --new-agent-id MyAgent` |

> Note: `--new-agent` remains as a legacy alias; prefer `--new-agent-id`.

## When to Use Each Mode
- Stateless: automation and CI/CD
- Contextual: iterative work and follow-ups
- Interactive: development, debugging, experimentation

## Legacy Note
Older entry points (`src/cli/admin.py`, `src/cli/agent.py`) remain for compatibility but the recommended interface is the unified `conductor` CLI. Update scripts to use the unified flags.