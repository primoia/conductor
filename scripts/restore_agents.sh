#!/bin/bash
# Restore dos agentes do SSD para RAMDisk

RAMDISK_PATH="/mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/.conductor_workspace"
SSD_BACKUP_PATH="$HOME/conductor_backup/.conductor_workspace"

if [ ! -d "$SSD_BACKUP_PATH" ]; then
    echo "❌ Backup não encontrado em: $SSD_BACKUP_PATH"
    exit 1
fi

echo "🔄 Restaurando agentes do backup..."
mkdir -p "$RAMDISK_PATH"
rsync -av "$SSD_BACKUP_PATH/" "$RAMDISK_PATH/"

echo "✅ Restore concluído!"
echo "   De: $SSD_BACKUP_PATH"
echo "   Para: $RAMDISK_PATH"

# Verificar agentes restaurados
echo "📊 Agentes restaurados:"
ls -1 "$RAMDISK_PATH/agents/" 2>/dev/null || echo "   Nenhum agente encontrado"