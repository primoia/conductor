#!/usr/bin/env python3
"""
Script para migrar campos created_at e updated_at nos documentos de agentes.

Usa o timestamp embutido no ObjectId do MongoDB para definir created_at
para agentes que não possuem esse campo.

Uso:
    python scripts/migrate_agent_timestamps.py [--dry-run]

Opções:
    --dry-run   Mostra o que seria feito sem executar as alterações
"""

import os
import sys
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient

# Configuração padrão
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:czrimr@localhost:27017/?authSource=admin')
DB_NAME = os.getenv('MONGO_DB', 'conductor_state')


def get_timestamp_from_objectid(oid) -> datetime:
    """
    Extrai o timestamp de um ObjectId do MongoDB.
    Os primeiros 4 bytes do ObjectId contêm um timestamp Unix.
    """
    if isinstance(oid, str):
        oid = ObjectId(oid)
    return oid.generation_time.replace(tzinfo=None)


def migrate_timestamps(dry_run: bool = False):
    """
    Migra os campos created_at e updated_at para agentes existentes.
    """
    print("=" * 60)
    print("MIGRAÇÃO DE TIMESTAMPS DE AGENTES")
    print("=" * 60)
    print(f"MongoDB URI: {MONGO_URI[:30]}...")
    print(f"Database: {DB_NAME}")
    print(f"Modo: {'DRY-RUN (simulação)' if dry_run else 'EXECUÇÃO REAL'}")
    print("=" * 60)
    print()

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Testar conexão
        client.admin.command('ping')
        print("✅ Conectado ao MongoDB")
    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB: {e}")
        sys.exit(1)

    db = client[DB_NAME]
    agents_collection = db["agents"]

    # Buscar todos os agentes
    total_agents = agents_collection.count_documents({})
    print(f"\n📊 Total de agentes na collection: {total_agents}")

    # Buscar agentes sem created_at
    agents_without_created_at = list(agents_collection.find(
        {"created_at": {"$exists": False}},
        {"_id": 1, "agent_id": 1}
    ))
    print(f"📊 Agentes sem created_at: {len(agents_without_created_at)}")

    # Buscar agentes sem updated_at
    agents_without_updated_at = agents_collection.count_documents(
        {"updated_at": {"$exists": False}}
    )
    print(f"📊 Agentes sem updated_at: {agents_without_updated_at}")

    if not agents_without_created_at:
        print("\n✅ Todos os agentes já possuem created_at!")
        return

    print("\n" + "-" * 60)
    print("ATUALIZAÇÕES A SEREM REALIZADAS:")
    print("-" * 60)

    updates_count = 0
    errors_count = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC sem timezone para MongoDB

    for agent in agents_without_created_at:
        agent_id = agent.get("agent_id", "N/A")
        oid = agent.get("_id")

        if oid:
            created_at = get_timestamp_from_objectid(oid)
            print(f"\n📝 Agente: {agent_id}")
            print(f"   _id: {oid}")
            print(f"   created_at (extraído do _id): {created_at.isoformat()}")
            print(f"   updated_at (agora): {now.isoformat()}")

            if not dry_run:
                try:
                    result = agents_collection.update_one(
                        {"_id": oid},
                        {
                            "$set": {
                                "created_at": created_at,
                                "updated_at": now
                            }
                        }
                    )
                    if result.modified_count > 0:
                        print(f"   ✅ Atualizado com sucesso!")
                        updates_count += 1
                    else:
                        print(f"   ⚠️ Nenhuma modificação (documento pode já ter sido atualizado)")
                except Exception as e:
                    print(f"   ❌ Erro ao atualizar: {e}")
                    errors_count += 1
            else:
                print(f"   🔍 [DRY-RUN] Seria atualizado")
                updates_count += 1

    # Atualizar updated_at para agentes que já têm created_at mas não têm updated_at
    if not dry_run:
        result = agents_collection.update_many(
            {
                "created_at": {"$exists": True},
                "updated_at": {"$exists": False}
            },
            {"$set": {"updated_at": now}}
        )
        if result.modified_count > 0:
            print(f"\n✅ Adicionado updated_at a {result.modified_count} agentes que já tinham created_at")

    print("\n" + "=" * 60)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 60)
    if dry_run:
        print(f"🔍 Agentes que SERIAM atualizados: {updates_count}")
        print("\n⚠️ Execute sem --dry-run para aplicar as alterações")
    else:
        print(f"✅ Agentes atualizados: {updates_count}")
        print(f"❌ Erros: {errors_count}")

    client.close()
    print("\n✅ Conexão fechada")


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    migrate_timestamps(dry_run=dry_run)


if __name__ == "__main__":
    main()
