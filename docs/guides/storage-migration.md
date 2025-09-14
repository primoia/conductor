# 🔄 Storage Migration Guide

This guide covers migrating agent data between filesystem and MongoDB backends in Conductor.

## Overview

Conductor supports bidirectional migration between storage backends:
- **Filesystem**: Local `.conductor_workspace` directory (default)
- **MongoDB**: Centralized database for team collaboration

## Quick Start

### 1. MongoDB Setup (First Time)

Add to your `.env` file:
```bash
MONGO_URI=mongodb://username:password@localhost:27017/conductor_state?authSource=admin
MONGO_DATABASE=conductor_state
MONGO_COLLECTION=agent_states
```

### 2. Basic Migration Commands

```bash
# Backup to MongoDB (safe, preserves filesystem config)
conductor --migrate-to mongodb --no-config-update

# Restore from MongoDB (safe, preserves filesystem config)
conductor --migrate-from mongodb --migrate-to filesystem --no-config-update

# Permanent migration to MongoDB (updates config.yaml)
conductor --migrate-to mongodb

# External backup to private Git repository
conductor --migrate-to filesystem --path /path/to/backup
```

## Use Cases

### RAMDisk Workflow (Recommended)

Perfect for volatile storage with MongoDB backup:

```bash
# Daily backup routine
conductor --migrate-to mongodb --no-config-update

# Emergency restore after RAMDisk loss
conductor --migrate-from mongodb --migrate-to filesystem --no-config-update
```

**Benefits:**
- ✅ Keep filesystem as default (simple for new developers)
- ✅ MongoDB as secure backup (no data loss)
- ✅ No configuration complexity
- ✅ Fast development cycle

### Team Scaling

Migrate permanently when team grows:

```bash
# One-time migration to shared MongoDB
conductor --migrate-to mongodb

# All team members now use MongoDB
# config.yaml automatically updated to: storage.type = mongodb
```

**Benefits:**
- ✅ Shared agent state across team
- ✅ Centralized knowledge base
- ✅ Consistent development environment
- ✅ Easy onboarding for new team members

### Private Git Backup

Backup agents to private repositories:

```bash
# Backup to private Git repo
conductor --migrate-to filesystem --path /path/to/private-repo/.conductor_workspace

# Commit and push
cd /path/to/private-repo
git add .conductor_workspace
git commit -m "Backup agents $(date)"
git push origin main
```

**Benefits:**
- ✅ Version-controlled agent backups
- ✅ Private repository security
- ✅ Team access via Git permissions
- ✅ Historical backup tracking

## Advanced Usage

### Selective Migration

The migration system transfers all agent data:
- `definition.yaml` - Agent configuration
- `persona.md` - Agent personality and instructions
- `session.json` - Current session state
- `knowledge.json` - Accumulated knowledge
- `history.log` - Task execution history

### Configuration Management

#### Preserve Configuration (Recommended)
```bash
# Use --no-config-update to keep current config.yaml
conductor --migrate-to mongodb --no-config-update
```

#### Update Configuration
```bash
# Updates config.yaml automatically
conductor --migrate-to mongodb

# Creates backup: config.yaml.backup.TIMESTAMP
# Updates: storage.type = mongodb
```

### Hybrid Workflows

You can use both storage systems simultaneously:

```bash
# Regular development (filesystem)
conductor --agent MyAgent "develop feature"

# Periodic backup (mongodb)
conductor --migrate-to mongodb --no-config-update

# Traditional SSD backup (still works)
conductor --backup
```

## Performance & Reliability

### Speed
- **19 agents**: ~0.1 seconds
- **Bulk operations**: Optimized for large datasets
- **Network**: Depends on MongoDB connection speed

### Safety Features
- ✅ **Automatic config backup** before changes
- ✅ **Validation** of MongoDB connectivity
- ✅ **Rollback support** via config.yaml.backup files
- ✅ **Error handling** with detailed messages
- ✅ **Dry-run validation** before actual migration

### Monitoring
```bash
# View detailed logs during migration
conductor --migrate-to mongodb --no-config-update

# Example output:
# 🔄 Initiating migration: filesystem → mongodb
# ✅ MongoDB connected: mongodb://localhost:27017/...
# 📊 Discovering agents...
#    ✓ Found 19 agents: [Agent1, Agent2, ...]
# 📦 Transferring data:
#    🤖 Agent1
#       ✓ definition.yaml (569B) → destination
#       ✓ persona.md (1,866B) → destination
# ✅ Migration completed! 19 agents, 58 files transferred
```

## Troubleshooting

### Common Issues

#### MongoDB Not Configured
```
❌ MongoDB not configured!
📖 Configure MONGO_URI in your .env file
```
**Solution**: Add `MONGO_URI=mongodb://...` to `.env`

#### Connection Failed
```
❌ MongoDB not accessible: ServerSelectionTimeoutError
```
**Solutions**:
- Check if MongoDB is running: `docker ps` or `systemctl status mongod`
- Verify connection string format
- Test firewall/network connectivity

#### Permission Denied
```
❌ Error: Permission denied writing to /path/to/backup
```
**Solution**: Ensure write permissions: `chmod 755 /path/to/backup`

### Validation Commands

```bash
# Test MongoDB connectivity
python3 -c "from pymongo import MongoClient; MongoClient('mongodb://...').server_info()"

# Validate current configuration
conductor --validate

# Check agent count
conductor --list
```

## Migration Checklist

### Before Migration
- [ ] Backup current agents: `conductor --backup`
- [ ] Configure MongoDB connection in `.env`
- [ ] Test MongoDB connectivity
- [ ] Ensure sufficient disk space/database storage

### During Migration
- [ ] Use `--no-config-update` for safe testing
- [ ] Monitor logs for errors
- [ ] Verify agent count matches source

### After Migration
- [ ] Test agent functionality: `conductor --list`
- [ ] Verify configuration: `conductor --validate`
- [ ] Keep config.yaml.backup files for rollback

## Integration with Existing Workflows

### SSD Backup Compatibility
The new migration system works alongside existing backup:

```bash
# Traditional SSD backup (still works)
conductor --backup

# New MongoDB backup
conductor --migrate-to mongodb --no-config-update
```

Both can run simultaneously without conflicts.

### CI/CD Integration
```bash
# In your CI/CD pipeline
- name: Backup agents to MongoDB
  run: conductor --migrate-to mongodb --no-config-update

- name: Backup to private repo
  run: |
    conductor --migrate-to filesystem --path ./agent-backup
    git -C ./agent-backup add .
    git -C ./agent-backup commit -m "CI backup $(date)"
    git -C ./agent-backup push
```

## Best Practices

1. **Start with `--no-config-update`** to test safely
2. **Regular backups** for RAMDisk workflows  
3. **Monitor logs** during first migrations
4. **Keep config backups** for easy rollback
5. **Test connectivity** before production migrations
6. **Document team workflows** when scaling to MongoDB

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Validate configuration: `conductor --validate`
3. Review logs during migration
4. Test with small agent sets first

---

*This migration system was implemented in SAGA-019 and provides enterprise-grade reliability for agent data management.*
