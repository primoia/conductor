#!/bin/bash
# Backup automático dos agentes da RAMDisk para SSD

RAMDISK_PATH="/mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/.conductor_workspace"
SSD_BACKUP_PATH="$HOME/conductor_backup/.conductor_workspace"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Criar diretório de backup se não existir
mkdir -p "$SSD_BACKUP_PATH"

# Backup incremental
echo "🔄 Fazendo backup dos agentes..."
rsync -av --delete "$RAMDISK_PATH/" "$SSD_BACKUP_PATH/"

# Backup com timestamp (para histórico)
VERSIONED_BACKUP="$HOME/conductor_backup/snapshots/backup_$TIMESTAMP"
mkdir -p "$HOME/conductor_backup/snapshots"
cp -r "$RAMDISK_PATH" "$VERSIONED_BACKUP"

echo "✅ Backup concluído:"
echo "   Incremental: $SSD_BACKUP_PATH"
echo "   Snapshot: $VERSIONED_BACKUP"

# Limpar snapshots antigos (manter apenas os últimos 10)
cd "$HOME/conductor_backup/snapshots"
ls -t | tail -n +11 | xargs -r rm -rf

echo "🧹 Snapshots antigos limpos (mantidos últimos 10)"