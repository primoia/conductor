#!/usr/bin/env python3
"""
Normaliza nomes dos agentes para formato legível.
Ex: MongoDBTest_Agent → MongoDB Test Agent
"""

import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:czrimr@localhost:27017/?authSource=admin')
DB_NAME = 'conductor_state'

def normalize_name(agent_id: str) -> str:
    """
    Converte agent_id para nome legível.
    Ex: MongoDBTest_Agent → MongoDB Test
        resume_formatter_Agent → Resume Formatter
    """
    # Remove sufixo _Agent
    name = agent_id.replace('_Agent', '')

    # Casos especiais
    special_cases = {
        'MongoDBTest': 'MongoDB Test',
        'MongoDB': 'MongoDB',
        'APIArchitect': 'API Architect',
        'AngularExpert': 'Angular Expert',
        'BusinessStrategy': 'Business Strategy',
        'DatabaseExpert': 'Database Expert',
        'DocWriter': 'Documentation Writer',
        'LogAnalyzer': 'Log Analyzer',
        'MongoKotlinExpert': 'MongoDB Kotlin Expert',
        'PerformanceOptimizer': 'Performance Optimizer',
        'ReactExpert': 'React Expert',
        'SecuritySpecialist': 'Security Specialist',
        'TestDirectCall': 'Test Direct Call',
        'TestQuickValidation': 'Test Quick Validation',
        'TestingSpecialist': 'Testing Specialist',
        'WebScraper': 'Web Scraper',
        'MongoTest': 'MongoDB Test',
        'GitLinkedInPromotion': 'Git LinkedIn Promotion',
        'DocumentationExpert': 'Documentation Expert',
        'StrategicComment': 'Strategic Comment',
        'LinkedInContent': 'LinkedIn Content',
        'ReadmeResume': 'README Resume',
        'SequenceDiagramGenerator': 'Sequence Diagram Generator',
        'ScreenplayNarrativeDeveloper': 'Screenplay Narrative Developer',
    }

    if name in special_cases:
        return special_cases[name]

    # Se tem underscore (ex: resume_formatter)
    if '_' in name:
        return ' '.join(word.capitalize() for word in name.split('_'))

    # Separar por CamelCase
    # Ex: CamelCase → Camel Case
    name = re.sub('([a-z])([A-Z])', r'\1 \2', name)

    return name

def main():
    print("=" * 80)
    print("Normalizando Nomes dos Agentes")
    print("=" * 80)

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db['agents']

    # Buscar todos os agentes
    agents = list(collection.find({}, {'agent_id': 1, 'definition.name': 1}))

    print(f"\n🔄 Processando {len(agents)} agentes...\n")

    updated_count = 0
    already_ok = 0

    for agent in agents:
        agent_id = agent.get('agent_id')
        current_name = agent.get('definition', {}).get('name', '')

        # Pular agentes que já têm nomes legíveis (não terminam com _Agent e não são iguais ao agent_id)
        if current_name and not current_name.endswith('_Agent') and current_name != agent_id:
            print(f"✓ {agent_id} → Já OK: {current_name}")
            already_ok += 1
            continue

        # Normalizar
        new_name = normalize_name(agent_id)

        result = collection.update_one(
            {'agent_id': agent_id},
            {'$set': {'definition.name': new_name}}
        )

        if result.modified_count > 0:
            print(f"✅ {agent_id}")
            print(f"   De: {current_name}")
            print(f"   Para: {new_name}")
            updated_count += 1
        else:
            print(f"⚠️  {agent_id} - Nenhuma alteração necessária")

    print("\n" + "=" * 80)
    print("📊 Resumo")
    print("=" * 80)
    print(f"✅ Atualizados: {updated_count}")
    print(f"✓ Já estavam OK: {already_ok}")

    # Listar estado final
    print("\n" + "=" * 80)
    print("🔍 Estado Final")
    print("=" * 80 + "\n")

    agents_final = collection.find({}, {'agent_id': 1, 'definition.name': 1, 'definition.emoji': 1}).sort('definition.name', 1)

    for agent in agents_final:
        emoji = agent.get('definition', {}).get('emoji', '🤖')
        name = agent.get('definition', {}).get('name', agent.get('agent_id'))
        print(f"{emoji} {name}")

    client.close()
    print("\n✅ Concluído!")

if __name__ == '__main__':
    main()
