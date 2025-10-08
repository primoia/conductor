#!/usr/bin/env python3
"""
Adiciona campos emoji e model aos agentes SAGA-003 migrados.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:czrimr@localhost:27017/?authSource=admin')
DB_NAME = 'conductor_state'

# Mapeamento de agentes SAGA-003
SAGA_003_AGENTS = {
    'resume_formatter_Agent': {
        'emoji': '📄',
        'model': 'claude-sonnet-4'
    },
    'linkedin_creator_Agent': {
        'emoji': '💼',
        'model': 'claude-sonnet-4'
    }
}

def main():
    print("=" * 80)
    print("SAGA-003: Adicionar Campos emoji e model")
    print("=" * 80)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db['agents']

    for agent_id, fields in SAGA_003_AGENTS.items():
        result = collection.update_one(
            {'agent_id': agent_id},
            {'$set': {
                'definition.emoji': fields['emoji'],
                'definition.model': fields['model']
            }}
        )

        if result.modified_count > 0:
            print(f"✅ Atualizado: {agent_id} → {fields['emoji']} {fields['model']}")
        else:
            print(f"⚠️  Não encontrado ou já atualizado: {agent_id}")

    # Verificar
    print("\n" + "=" * 80)
    print("🔍 Verificando...")
    print("=" * 80 + "\n")

    for agent_id in SAGA_003_AGENTS.keys():
        agent = collection.find_one({'agent_id': agent_id})
        if agent:
            emoji = agent.get('definition', {}).get('emoji', '❌')
            model = agent.get('definition', {}).get('model', '❌')
            print(f"{emoji} {agent.get('definition', {}).get('name', agent_id)} - Model: {model}")

    client.close()
    print("\n✅ Concluído!")

if __name__ == '__main__':
    main()
