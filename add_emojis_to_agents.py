#!/usr/bin/env python3
"""
Adiciona emojis relevantes aos 30 agentes que não têm emoji definido.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/?authSource=admin')
DB_NAME = 'conductor_state'

# Mapeamento de emojis por agent_id
EMOJI_MAPPING = {
    # Database & Backend
    'MongoDBTest_Agent': '🍃',
    'DatabaseExpert_Agent': '🗄️',
    'MongoKotlinExpert_Agent': '🍃',
    'MongoTest_Agent': '🔬',

    # API & Architecture
    'APIArchitect_Agent': '🏗️',

    # Frontend
    'AngularExpert_Agent': '🅰️',
    'ReactExpert_Agent': '⚛️',

    # Code Quality & Review
    'CodeReviewer_Agent': '👁️',
    'PerformanceOptimizer_Agent': '⚡',
    'SecuritySpecialist_Agent': '🔒',
    'TestingSpecialist_Agent': '🧪',

    # DevOps & Tools
    'CommitMessage_Agent': '📝',
    'Executor_Agent': '⚙️',
    'LogAnalyzer_Agent': '📊',

    # Documentation
    'DocWriter_Agent': '📚',
    'DocumentationExpert_Agent': '📖',
    'ReadmeResume_Agent': '📋',

    # Content & Marketing
    'GitLinkedInPromotion_Agent': '📢',
    'LinkedInContent_Agent': '💼',
    'StrategicComment_Agent': '💬',

    # Creative & Storytelling
    'ScreenplayNarrativeDeveloper_Agent': '🎬',
    'SequenceDiagramGenerator_Agent': '📐',

    # Business & Strategy
    'BusinessStrategy_Agent': '💡',

    # Web & Scraping
    'WebScraper_Agent': '🕸️',

    # Meta & System
    'AgentCreator_Agent': '🔧',
    'Maestro_Agent': '🎼',
    'SystemGuide_Meta_Agent': '🧭',

    # Test Agents
    'TestAgent': '🧪',
    'TestDirectCall_Agent': '🔬',
    'TestQuickValidation_Agent': '✅',
}

def main():
    print("=" * 80)
    print("Adicionando Emojis aos Agentes")
    print("=" * 80)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db['agents']

    updated_count = 0
    not_found_count = 0

    print(f"\n🔄 Processando {len(EMOJI_MAPPING)} agentes...\n")

    for agent_id, emoji in EMOJI_MAPPING.items():
        result = collection.update_one(
            {'agent_id': agent_id},
            {'$set': {'definition.emoji': emoji}}
        )

        if result.matched_count > 0:
            if result.modified_count > 0:
                # Buscar nome do agente
                agent = collection.find_one({'agent_id': agent_id})
                name = agent.get('definition', {}).get('name', agent_id)
                print(f"✅ {emoji} {name}")
                updated_count += 1
            else:
                print(f"⏭️  {emoji} {agent_id} (já tinha emoji)")
        else:
            print(f"❌ {agent_id} - Não encontrado no banco")
            not_found_count += 1

    print("\n" + "=" * 80)
    print("📊 Resumo")
    print("=" * 80)
    print(f"✅ Atualizados: {updated_count}")
    print(f"⏭️  Já tinham: {len(EMOJI_MAPPING) - updated_count - not_found_count}")
    print(f"❌ Não encontrados: {not_found_count}")

    # Verificar estado final
    total_com_emoji = collection.count_documents({'definition.emoji': {'$exists': True}})
    total_sem_emoji = collection.count_documents({'definition.emoji': {'$exists': False}})

    print("\n" + "=" * 80)
    print("🔍 Estado Final do Banco")
    print("=" * 80)
    print(f"✅ Agentes COM emoji: {total_com_emoji}")
    print(f"❌ Agentes SEM emoji: {total_sem_emoji}")

    if total_sem_emoji > 0:
        print(f"\n⚠️  Ainda existem {total_sem_emoji} agentes sem emoji:")
        sem_emoji = collection.find({'definition.emoji': {'$exists': False}}, {'agent_id': 1})
        for agent in sem_emoji:
            print(f"   - {agent.get('agent_id')}")

    client.close()
    print("\n✅ Concluído!")

if __name__ == '__main__':
    main()
