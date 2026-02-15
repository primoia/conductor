#!/usr/bin/env python3
"""
Script para migrar tags group:* para o campo group na raiz do documento.

Move a informação de grupo das tags (definition.tags) para um campo
dedicado na raiz do documento MongoDB, e remove a tag group:* redundante.

Uso:
    python scripts/migrate_group_to_root.py [--dry-run]

Opções:
    --dry-run   Mostra o que seria feito sem executar as alterações
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient

# Configuração padrão
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/?authSource=admin')
DB_NAME = os.getenv('MONGO_DB', 'conductor_state')

VALID_GROUPS = ['development', 'crm', 'documentation', 'devops', 'orchestration', 'testing', 'career', 'other']


def migrate_group_to_root(dry_run: bool = False):
    """
    Migra tags group:* para o campo group na raiz do documento.
    """
    print("=" * 70)
    print("MIGRAÇÃO DE GROUP PARA RAIZ DO DOCUMENTO")
    print("=" * 70)
    print(f"MongoDB URI: {MONGO_URI[:30]}...")
    print(f"Database: {DB_NAME}")
    print(f"Modo: {'DRY-RUN (simulação)' if dry_run else 'EXECUÇÃO REAL'}")
    print("=" * 70)
    print()

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Conectado ao MongoDB")
    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB: {e}")
        sys.exit(1)

    db = client[DB_NAME]
    agents_collection = db["agents"]

    # Buscar todos os agentes
    agents = list(agents_collection.find({}, {'_id': 1, 'agent_id': 1, 'definition': 1, 'group': 1}))
    print(f"\n📊 Total de agentes: {len(agents)}")

    # Estatísticas
    already_migrated = 0
    migrated = 0
    errors = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    print("\n" + "-" * 70)
    print("MIGRAÇÕES:")
    print("-" * 70)

    for agent in agents:
        agent_id = agent.get('agent_id', 'N/A')
        oid = agent.get('_id')
        definition = agent.get('definition', {})
        current_tags = definition.get('tags', [])
        existing_group = agent.get('group')

        # Extrair grupo das tags
        group_tag = None
        group_value = None
        for tag in current_tags:
            if tag.startswith('group:'):
                group_tag = tag
                group_value = tag.replace('group:', '')
                break

        # Se já tem group na raiz e não tem tag group:*, pular
        if existing_group and not group_tag:
            print(f"⏭️  {agent_id}: já migrado (group={existing_group})")
            already_migrated += 1
            continue

        # Se já tem group na raiz E tem tag group:*, apenas remover a tag
        if existing_group and group_tag:
            new_tags = [t for t in current_tags if not t.startswith('group:')]
            print(f"\n📝 {agent_id}")
            print(f"   Group existente: {existing_group}")
            print(f"   Removendo tag redundante: '{group_tag}'")

            if not dry_run:
                try:
                    result = agents_collection.update_one(
                        {"_id": oid},
                        {
                            "$set": {
                                "definition.tags": new_tags,
                                "updated_at": now
                            }
                        }
                    )
                    if result.modified_count > 0:
                        print(f"   ✅ Tag removida!")
                        migrated += 1
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    errors += 1
            else:
                print(f"   🔍 [DRY-RUN] Seria atualizado")
                migrated += 1
            continue

        # Se não tem group na raiz
        if not existing_group:
            # Se tem tag group:*, usar ela
            if group_value:
                new_group = group_value if group_value in VALID_GROUPS else 'other'
            else:
                # Sem tag group:*, definir como 'other'
                new_group = 'other'

            # Remover tag group:* das tags
            new_tags = [t for t in current_tags if not t.startswith('group:')]

            print(f"\n📝 {agent_id}")
            print(f"   Grupo extraído: {group_value or '(nenhum)'} → {new_group}")
            if group_tag:
                print(f"   Removendo tag: '{group_tag}'")

            if not dry_run:
                try:
                    result = agents_collection.update_one(
                        {"_id": oid},
                        {
                            "$set": {
                                "group": new_group,
                                "definition.tags": new_tags,
                                "updated_at": now
                            }
                        }
                    )
                    if result.modified_count > 0:
                        print(f"   ✅ Migrado!")
                        migrated += 1
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    errors += 1
            else:
                print(f"   🔍 [DRY-RUN] Seria migrado")
                migrated += 1

    print("\n" + "=" * 70)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 70)
    print(f"📊 Já migrados (ignorados): {already_migrated}")
    if dry_run:
        print(f"🔍 Agentes que SERIAM atualizados: {migrated}")
        print("\n⚠️ Execute sem --dry-run para aplicar as alterações")
    else:
        print(f"✅ Agentes atualizados: {migrated}")
        print(f"❌ Erros: {errors}")

    client.close()
    print("\n✅ Conexão fechada")


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    migrate_group_to_root(dry_run=dry_run)


if __name__ == "__main__":
    main()
