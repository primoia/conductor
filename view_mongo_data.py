#!/usr/bin/env python3
"""
Script para visualizar dados salvos no MongoDB
"""

import os
import sys
from datetime import datetime

try:
    import pymongo
except ImportError:
    print("❌ pymongo não instalado. Execute: pip install pymongo")
    sys.exit(1)


def view_mongo_data():
    """Visualiza dados salvos no MongoDB."""

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI não configurada!")
        return

    try:
        # Conectar ao MongoDB
        client = pymongo.MongoClient(mongo_uri)
        db = client["conductor_state"]
        collection = db["agent_states"]

        print("📊 Dados salvos no MongoDB:")
        print("=" * 50)

        # Listar todos os documentos
        documents = list(collection.find())

        if not documents:
            print("🔍 Nenhum documento encontrado.")
            return

        for i, doc in enumerate(documents, 1):
            print(f"\n📄 Documento {i}:")
            print(f"   ID: {doc['_id']}")
            print(f"   Agent: {doc.get('agent_id', 'N/A')}")
            print(f"   Path: {doc.get('agent_home_path', 'N/A')}")
            print(f"   File: {doc.get('state_file_name', 'N/A')}")
            print(f"   Updated: {doc.get('updated_at', 'N/A')}")

            # Mostrar histórico de conversas
            history = doc.get("conversation_history", [])
            print(f"   Messages: {len(history)}")

            if history:
                print("   Last messages:")
                for msg in history[-2:]:  # Últimas 2 mensagens
                    role = msg.get("role", "unknown")
                    content = str(msg.get("message", msg.get("content", "")))[:50]
                    print(f"     {role}: {content}...")

        client.close()

    except Exception as e:
        print(f"❌ Erro ao visualizar dados: {e}")


def clear_mongo_data():
    """Remove todos os dados do MongoDB (cuidado!)."""

    response = input(
        "⚠️  Tem certeza que deseja limpar TODOS os dados? (digite 'SIM'): "
    )
    if response != "SIM":
        print("❌ Operação cancelada.")
        return

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI não configurada!")
        return

    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client["conductor_state"]
        collection = db["agent_states"]

        result = collection.delete_many({})
        print(f"🗑️  {result.deleted_count} documentos removidos.")

        client.close()

    except Exception as e:
        print(f"❌ Erro ao limpar dados: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Visualizar dados MongoDB")
    parser.add_argument("--clear", action="store_true", help="Limpar todos os dados")

    args = parser.parse_args()

    if args.clear:
        clear_mongo_data()
    else:
        view_mongo_data()
