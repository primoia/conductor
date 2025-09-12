#!/bin/bash
# Configurar backup automático via cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_agents.sh"

echo "🔧 Configurando backup automático..."

# Adicionar ao crontab (backup a cada 30 minutos)
(crontab -l 2>/dev/null; echo "*/30 * * * * $BACKUP_SCRIPT >> /tmp/conductor_backup.log 2>&1") | crontab -

echo "✅ Backup automático configurado!"
echo "   Frequência: A cada 30 minutos"
echo "   Script: $BACKUP_SCRIPT"
echo "   Log: /tmp/conductor_backup.log"
echo ""
echo "Para verificar: crontab -l"
echo "Para remover: crontab -e (e deletar a linha)"