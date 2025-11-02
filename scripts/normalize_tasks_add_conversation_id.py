#!/usr/bin/env python3
"""
Script de Normalização: Adicionar conversation_id na collection tasks

Este script:
1. Varre todas as tasks na collection
2. Para cada instance_id único, gera um conversation_id (UUID)
3. Atualiza todas as tasks com o mesmo instance_id para ter o mesmo conversation_id
4. Tasks sem instance_id recebem conversation_id = instance_id vazio (cada uma é uma conversa isolada)

Autor: Claude Code Assistant
Data: 2025-11-01
Ref: PLANO_REFATORACAO_CONVERSATION_ID.md
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
    """Cria backup da collection tasks antes da modificação."""
    backup_name = f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"📦 Criando backup: {backup_name}")

    # Copiar todos os documentos
    tasks = list(db.tasks.find())
    if tasks:
        db[backup_name].insert_many(tasks)
        logger.info(f"✅ Backup criado com {len(tasks)} documentos")
    else:
        logger.warning("⚠️ Nenhuma task encontrada para backup")

    return backup_name


def normalize_tasks(db, dry_run=True):
    """
    Adiciona conversation_id às tasks baseado no instance_id.

    Args:
        db: Database MongoDB
        dry_run: Se True, apenas simula sem modificar dados
    """
    tasks_collection = db.tasks

    # 1. Mapear instance_id → conversation_id
    logger.info("🔍 Analisando tasks existentes...")

    # Pegar todos os instance_ids únicos
    pipeline = [
        {"$group": {"_id": "$instance_id", "count": {"$sum": 1}}}
    ]

    instance_groups = list(tasks_collection.aggregate(pipeline))
    logger.info(f"📊 Encontrados {len(instance_groups)} instance_ids únicos")

    # Criar mapeamento instance_id → conversation_id
    instance_to_conversation = {}

    for group in instance_groups:
        instance_id = group['_id']
        count = group['count']

        if instance_id is None or instance_id == "":
            # Tasks sem instance_id não recebem conversation_id fixo
            # (cada uma será uma conversa isolada)
            logger.info(f"   - instance_id=None: {count} tasks (cada uma receberá conversation_id único)")
            continue
        else:
            # Gerar conversation_id único para este instance_id
            conversation_id = str(uuid.uuid4())
            instance_to_conversation[instance_id] = conversation_id
            logger.info(f"   - instance_id={instance_id[:8]}...: {count} tasks → conversation_id={conversation_id[:8]}...")

    # 2. Atualizar tasks
    logger.info(f"\n{'🔍 [DRY RUN]' if dry_run else '✍️'} Atualizando tasks...")

    total_updated = 0
    total_with_instance = 0
    total_without_instance = 0

    # Atualizar tasks com instance_id
    for instance_id, conversation_id in instance_to_conversation.items():
        if dry_run:
            count = tasks_collection.count_documents({"instance_id": instance_id})
            logger.info(f"   [DRY RUN] Atualizaria {count} tasks: instance_id={instance_id[:8]}... → conversation_id={conversation_id[:8]}...")
            total_with_instance += count
        else:
            result = tasks_collection.update_many(
                {"instance_id": instance_id},
                {"$set": {"conversation_id": conversation_id}}
            )
            logger.info(f"   ✅ Atualizadas {result.modified_count} tasks: instance_id={instance_id[:8]}... → conversation_id={conversation_id[:8]}...")
            total_updated += result.modified_count
            total_with_instance += result.modified_count

    # Atualizar tasks SEM instance_id (cada uma recebe seu próprio conversation_id)
    tasks_without_instance = tasks_collection.find({"$or": [{"instance_id": None}, {"instance_id": ""}]})

    for task in tasks_without_instance:
        task_id = task['_id']
        conversation_id = str(uuid.uuid4())

        if dry_run:
            logger.info(f"   [DRY RUN] Atualizaria task {task_id} sem instance_id → conversation_id={conversation_id[:8]}...")
            total_without_instance += 1
        else:
            tasks_collection.update_one(
                {"_id": task_id},
                {"$set": {"conversation_id": conversation_id}}
            )
            total_without_instance += 1

    # 3. Relatório final
    logger.info(f"\n📊 Resumo da normalização:")
    logger.info(f"   - Tasks com instance_id: {total_with_instance}")
    logger.info(f"   - Tasks sem instance_id: {total_without_instance}")
    logger.info(f"   - Total: {total_with_instance + total_without_instance}")

    if not dry_run:
        logger.info(f"   - Total atualizado: {total_updated + total_without_instance}")

        # Criar índice para conversation_id
        logger.info(f"\n🔧 Criando índice para conversation_id...")
        tasks_collection.create_index("conversation_id")
        logger.info(f"✅ Índice criado")

    return {
        "total_with_instance": total_with_instance,
        "total_without_instance": total_without_instance,
        "total": total_with_instance + total_without_instance,
        "updated": total_updated + total_without_instance if not dry_run else 0
    }


def verify_normalization(db):
    """Verifica se a normalização foi bem-sucedida."""
    tasks_collection = db.tasks

    logger.info("\n🔍 Verificando normalização...")

    # 1. Verificar se todas as tasks têm conversation_id
    total_tasks = tasks_collection.count_documents({})
    tasks_with_conv_id = tasks_collection.count_documents({"conversation_id": {"$exists": True}})
    tasks_without_conv_id = total_tasks - tasks_with_conv_id

    logger.info(f"   - Total de tasks: {total_tasks}")
    logger.info(f"   - Tasks com conversation_id: {tasks_with_conv_id}")
    logger.info(f"   - Tasks sem conversation_id: {tasks_without_conv_id}")

    if tasks_without_conv_id > 0:
        logger.warning(f"⚠️ Ainda existem {tasks_without_conv_id} tasks sem conversation_id!")
        return False

    # 2. Verificar consistência: instance_id → conversation_id
    pipeline = [
        {"$match": {"instance_id": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": "$instance_id",
            "conversation_ids": {"$addToSet": "$conversation_id"}
        }}
    ]

    inconsistent = []
    for group in tasks_collection.aggregate(pipeline):
        instance_id = group['_id']
        conversation_ids = group['conversation_ids']

        if len(conversation_ids) > 1:
            inconsistent.append((instance_id, conversation_ids))

    if inconsistent:
        logger.error(f"❌ Inconsistências encontradas:")
        for instance_id, conv_ids in inconsistent:
            logger.error(f"   instance_id={instance_id} tem múltiplos conversation_ids: {conv_ids}")
        return False

    logger.info("✅ Normalização verificada com sucesso!")
    return True


def main():
    """Função principal do script."""
    import argparse

    parser = argparse.ArgumentParser(description='Normalizar tasks adicionando conversation_id')
    parser.add_argument('--dry-run', action='store_true', help='Simular sem modificar dados')
    parser.add_argument('--skip-backup', action='store_true', help='Pular criação de backup')
    parser.add_argument('--verify-only', action='store_true', help='Apenas verificar normalização')

    args = parser.parse_args()

    try:
        # Conectar ao MongoDB
        db = connect_to_mongodb()

        if args.verify_only:
            verify_normalization(db)
            return

        # Criar backup (a menos que skip-backup seja passado)
        if not args.skip_backup and not args.dry_run:
            backup_name = create_backup(db)
            logger.info(f"💾 Backup salvo como: {backup_name}")

        # Normalizar tasks
        result = normalize_tasks(db, dry_run=args.dry_run)

        if args.dry_run:
            logger.info(f"\n🔍 [DRY RUN] Nenhuma modificação foi feita")
            logger.info(f"Execute sem --dry-run para aplicar as mudanças")
        else:
            logger.info(f"\n✅ Normalização concluída com sucesso!")

            # Verificar resultado
            verify_normalization(db)

    except Exception as e:
        logger.error(f"❌ Erro durante normalização: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
