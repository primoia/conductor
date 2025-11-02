#!/usr/bin/env python3
"""
Script de Migração: De agent_conversations para conversations

Este script migra dados da collection agent_conversations (modelo antigo baseado em instance_id)
para a nova collection conversations (modelo global baseado em conversation_id).

Lógica de Migração:
1. Cada instance_id único se torna uma conversa (conversation)
2. Mensagens são convertidas do formato {role, content} para {type, content, agent}
3. Metadados do agente são extraídos e adicionados

Autor: Claude Code Assistant
Data: 2025-11-01
Ref: PLANO_REFATORACAO_CONVERSATION_ID.md - Fase 3
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()


def connect_to_mongodb():
    """Conecta ao MongoDB usando MONGO_URI do ambiente."""
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        raise ValueError("MONGO_URI não definida no ambiente")

    client = MongoClient(mongo_uri)
    db = client.conductor_state
    logger.info(f"✅ Conectado ao MongoDB: conductor_state")
    return db


def create_backup(db):
    """Cria backup da collection agent_conversations antes da migração."""
    backup_name = f"agent_conversations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"📦 Criando backup: {backup_name}")

    # Copiar todos os documentos
    conversations = list(db.agent_conversations.find())
    if conversations:
        db[backup_name].insert_many(conversations)
        logger.info(f"✅ Backup criado com {len(conversations)} documentos")
    else:
        logger.warning("⚠️ Nenhuma conversa encontrada para backup")

    return backup_name


def migrate_conversation(old_conv: dict, agent_id_map: dict = None) -> dict:
    """
    Converte um documento agent_conversations para o novo formato conversations.

    Args:
        old_conv: Documento antigo
        agent_id_map: Mapeamento instance_id → agent_id (se disponível)

    Returns:
        Documento no novo formato
    """
    instance_id = old_conv['instance_id']
    agent_name = old_conv.get('agent_name', 'Unknown Agent')
    metadata = old_conv.get('metadata', {})
    old_history = old_conv.get('conversation_history', [])

    # Gerar conversation_id único
    conversation_id = str(uuid.uuid4())

    # Tentar obter agent_id do mapa ou usar agent_name como fallback
    agent_id = None
    if agent_id_map:
        agent_id = agent_id_map.get(instance_id)

    if not agent_id:
        # Fallback: usar agent_name como agent_id
        agent_id = agent_name.replace(' ', '_')

    # Criar AgentInfo para o agente
    agent_info = {
        "agent_id": agent_id,
        "instance_id": instance_id,
        "name": agent_name,
        "emoji": "🤖"  # Emoji padrão, pode ser customizado depois
    }

    # Converter mensagens do formato antigo para o novo
    new_messages = []

    for old_msg in old_history:
        role = old_msg.get('role')
        content = old_msg.get('content', '')
        timestamp = old_msg.get('timestamp', datetime.utcnow().isoformat())

        if role == 'user':
            new_messages.append({
                "id": str(uuid.uuid4()),
                "type": "user",
                "content": content,
                "timestamp": timestamp
            })
        elif role == 'assistant':
            new_messages.append({
                "id": str(uuid.uuid4()),
                "type": "bot",
                "content": content,
                "timestamp": timestamp,
                "agent": agent_info
            })

    # Criar documento novo
    new_conv = {
        "conversation_id": conversation_id,
        "title": f"Conversa com {agent_name}",  # Título gerado
        "created_at": metadata.get('created_at', datetime.utcnow().isoformat()),
        "updated_at": metadata.get('last_interaction', datetime.utcnow().isoformat()),
        "active_agent": agent_info,
        "participants": [agent_info],
        "messages": new_messages,
        # Metadados de migração
        "_migration": {
            "migrated_from": "agent_conversations",
            "original_instance_id": instance_id,
            "migrated_at": datetime.utcnow().isoformat()
        }
    }

    return new_conv


def build_agent_id_map(db):
    """
    Tenta construir um mapa instance_id → agent_id usando a collection tasks.

    Returns:
        Dict[instance_id, agent_id]
    """
    logger.info("🔍 Construindo mapa instance_id → agent_id...")

    agent_map = {}

    # Usar pipeline de agregação para agrupar
    pipeline = [
        {"$match": {"instance_id": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": "$instance_id",
            "agent_id": {"$first": "$agent_id"}  # Pega o primeiro agent_id encontrado
        }}
    ]

    for result in db.tasks.aggregate(pipeline):
        instance_id = result['_id']
        agent_id = result['agent_id']
        agent_map[instance_id] = agent_id

    logger.info(f"✅ Mapa construído com {len(agent_map)} entradas")
    return agent_map


def migrate_all_conversations(db, dry_run=True):
    """
    Migra todas as conversas de agent_conversations para conversations.

    Args:
        db: Database MongoDB
        dry_run: Se True, apenas simula sem modificar dados
    """
    agent_conversations = db.agent_conversations
    conversations = db.conversations

    # Construir mapa de instance_id → agent_id
    agent_id_map = build_agent_id_map(db)

    # Obter todos os documentos de agent_conversations
    logger.info("🔍 Lendo conversas antigas...")
    old_conversations = list(agent_conversations.find())
    logger.info(f"📊 Encontradas {len(old_conversations)} conversas para migrar")

    if len(old_conversations) == 0:
        logger.warning("⚠️ Nenhuma conversa para migrar")
        return {"total": 0, "migrated": 0}

    migrated_count = 0

    for old_conv in old_conversations:
        instance_id = old_conv.get('instance_id')

        if not instance_id:
            logger.warning(f"⚠️ Conversa sem instance_id, pulando: {old_conv.get('_id')}")
            continue

        # Converter para novo formato
        new_conv = migrate_conversation(old_conv, agent_id_map)

        if dry_run:
            logger.info(f"[DRY RUN] Migraria conversa:")
            logger.info(f"   instance_id: {instance_id}")
            logger.info(f"   conversation_id: {new_conv['conversation_id']}")
            logger.info(f"   title: {new_conv['title']}")
            logger.info(f"   messages: {len(new_conv['messages'])}")
        else:
            # Inserir na nova collection
            try:
                conversations.insert_one(new_conv)
                logger.info(f"✅ Migrada: {instance_id} → {new_conv['conversation_id']} ({len(new_conv['messages'])} mensagens)")
                migrated_count += 1
            except Exception as e:
                logger.error(f"❌ Erro ao migrar conversa {instance_id}: {e}")

    if dry_run:
        logger.info(f"\n🔍 [DRY RUN] {len(old_conversations)} conversas seriam migradas")
    else:
        logger.info(f"\n✅ Migração concluída: {migrated_count}/{len(old_conversations)} conversas migradas")

    return {"total": len(old_conversations), "migrated": migrated_count if not dry_run else 0}


def verify_migration(db):
    """Verifica se a migração foi bem-sucedida."""
    logger.info("\n🔍 Verificando migração...")

    old_count = db.agent_conversations.count_documents({})
    new_count = db.conversations.count_documents({"_migration.migrated_from": "agent_conversations"})

    logger.info(f"   - Conversas antigas (agent_conversations): {old_count}")
    logger.info(f"   - Conversas migradas (conversations): {new_count}")

    if new_count == old_count:
        logger.info("✅ Migração completa! Todas as conversas foram migradas.")
        return True
    elif new_count < old_count:
        logger.warning(f"⚠️ Migração incompleta: {old_count - new_count} conversas faltando")
        return False
    else:
        logger.info("ℹ️ Há mais conversas migradas do que antigas (possível re-execução)")
        return True


def main():
    """Função principal do script."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrar agent_conversations para conversations')
    parser.add_argument('--dry-run', action='store_true', help='Simular sem modificar dados')
    parser.add_argument('--skip-backup', action='store_true', help='Pular criação de backup')
    parser.add_argument('--verify-only', action='store_true', help='Apenas verificar migração')

    args = parser.parse_args()

    try:
        # Conectar ao MongoDB
        db = connect_to_mongodb()

        if args.verify_only:
            verify_migration(db)
            return

        # Criar backup (a menos que skip-backup seja passado)
        if not args.skip_backup and not args.dry_run:
            backup_name = create_backup(db)
            logger.info(f"💾 Backup salvo como: {backup_name}")

        # Migrar conversas
        result = migrate_all_conversations(db, dry_run=args.dry_run)

        if args.dry_run:
            logger.info(f"\n🔍 [DRY RUN] Nenhuma modificação foi feita")
            logger.info(f"Execute sem --dry-run para aplicar as mudanças")
        else:
            logger.info(f"\n✅ Migração concluída com sucesso!")

            # Verificar resultado
            verify_migration(db)

    except Exception as e:
        logger.error(f"❌ Erro durante migração: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
