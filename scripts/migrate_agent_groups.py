#!/usr/bin/env python3
"""
Script para adicionar tags de grupo aos agentes.

Adiciona tags no formato 'group:categoria' para facilitar filtragem na UI.

Uso:
    python scripts/migrate_agent_groups.py [--dry-run]

Opções:
    --dry-run   Mostra o que seria feito sem executar as alterações
"""

import os
import sys
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient

# Configuração padrão
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/?authSource=admin')
DB_NAME = os.getenv('MONGO_DB', 'conductor_state')

# Mapeamento de agentes para grupos
# Baseado na categorização do Counselor_Agent
AGENT_GROUPS = {
    # 🔧 Desenvolvimento & Arquitetura (group:development)
    'APIArchitect_Agent': 'development',
    'AngularExpert_Agent': 'development',
    'AngularRefactorAnalyst_Agent': 'development',
    'ReactExpert_Agent': 'development',
    'DatabaseExpert_Agent': 'development',
    'MongoKotlinExpert_Agent': 'development',
    'PythonMicroservicesArchitect_Agent': 'development',
    'CodeReviewer_Agent': 'development',
    'ProgrammingLanguages_Agent': 'development',
    'SequenceDiagramGenerator_Agent': 'development',

    # 📊 CRM & Vendas (group:crm)
    'PrimoiaCRM_Agent': 'crm',
    'CRMAnalytics_Agent': 'crm',
    'DealPredictor_CRM_Agent': 'crm',
    'LeadQualifier_CRM_Agent': 'crm',
    'EmailAssistant_CRM_Agent': 'crm',
    'Hunter_Agent': 'crm',
    'AIBusinessProposal_Agent': 'crm',

    # 📝 Documentação & Conteúdo (group:documentation)
    'DocWriter_Agent': 'documentation',
    'DocumentationExpert_Agent': 'documentation',
    'LinkedInContent_Agent': 'documentation',
    'linkedin_creator_Agent': 'documentation',
    'GitLinkedInPromotion_Agent': 'documentation',
    'StrategicComment_Agent': 'documentation',
    'ScreenplayAssistant_Agent': 'documentation',
    'ScreenplayNarrativeDeveloper_Agent': 'documentation',
    'ConversationToFeature_Agent': 'documentation',

    # 🛡️ DevOps & Segurança (group:devops)
    'DevOpsEngineer_Agent': 'devops',
    'DockerSecurityArchitect_Agent': 'devops',
    'SecuritySpecialist_Agent': 'devops',
    'PerformanceOptimizer_Agent': 'devops',
    'LogAnalyzer_Agent': 'devops',
    'WebScraper_Agent': 'devops',

    # 🎼 Orquestração & Meta-Agentes (group:orchestration)
    'Maestro_Agent': 'orchestration',
    'AgentCreator_Agent': 'orchestration',
    'AgentEvaluator_Agent': 'orchestration',
    'IdeaCompanion_Agent': 'orchestration',
    'Visionary_Agent': 'orchestration',
    'Counselor_Agent': 'orchestration',
    'SystemGuide_Meta_Agent': 'orchestration',
    'SagaPlanner_Agent': 'orchestration',
    'SeniorCodeExecutor_Agent': 'orchestration',
    'Executor_Agent': 'orchestration',
    'RequirementsEngineer_Agent': 'orchestration',
    'BusinessStrategy_Agent': 'orchestration',
    'MonorepoCommitOrchestrator_Agent': 'orchestration',
    'PrimoiaGitOrchestrator_Agent': 'orchestration',
    'CommitMessage_Agent': 'orchestration',

    # 🧪 Testes & Qualidade (group:testing)
    'TestingSpecialist_Agent': 'testing',
    'MCPToolsTester_Agent': 'testing',
    'ExecutionPlanValidator_Agent': 'testing',
    'MongoTest_Agent': 'testing',
    'MongoDBTest_Agent': 'testing',
    'TestAgent': 'testing',
    'TestDirectCall_Agent': 'testing',
    'TestNormalized_Agent': 'testing',
    'TestNormalizedV2_Agent': 'testing',
    'NormalizedTest12345_Agent': 'testing',
    'TestQuickValidation_Agent': 'testing',

    # 💼 Carreira & Profissional (group:career)
    'CareerArchitect_Agent': 'career',
    'resume_formatter_Agent': 'career',
}

# Labels para exibição na UI
GROUP_LABELS = {
    'development': '🔧 Desenvolvimento',
    'crm': '📊 CRM & Vendas',
    'documentation': '📝 Documentação',
    'devops': '🛡️ DevOps & Segurança',
    'orchestration': '🎼 Orquestração',
    'testing': '🧪 Testes',
    'career': '💼 Carreira',
    'other': '📦 Outros',
}


def migrate_groups(dry_run: bool = False):
    """
    Adiciona tags de grupo aos agentes.
    """
    print("=" * 70)
    print("MIGRAÇÃO DE GRUPOS DE AGENTES")
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
    agents = list(agents_collection.find({}, {'_id': 1, 'agent_id': 1, 'definition': 1}))
    print(f"\n📊 Total de agentes: {len(agents)}")

    # Estatísticas
    stats = {group: 0 for group in GROUP_LABELS.keys()}
    updates_count = 0
    errors_count = 0
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    print("\n" + "-" * 70)
    print("GRUPOS A SEREM ATRIBUÍDOS:")
    print("-" * 70)

    for agent in agents:
        agent_id = agent.get('agent_id', 'N/A')
        oid = agent.get('_id')
        definition = agent.get('definition', {})
        current_tags = definition.get('tags', [])

        # Determinar grupo
        group = AGENT_GROUPS.get(agent_id, 'other')
        group_tag = f'group:{group}'
        stats[group] += 1

        # Verificar se já tem a tag de grupo
        existing_group_tags = [t for t in current_tags if t.startswith('group:')]

        if group_tag in current_tags:
            print(f"⏭️  {agent_id}: já tem '{group_tag}'")
            continue

        # Remover tags de grupo antigas (se houver) e adicionar nova
        new_tags = [t for t in current_tags if not t.startswith('group:')]
        new_tags.append(group_tag)

        print(f"\n📝 {agent_id}")
        print(f"   Grupo: {GROUP_LABELS.get(group, group)}")
        if existing_group_tags:
            print(f"   Tags de grupo antigas: {existing_group_tags} → removidas")
        print(f"   Nova tag: '{group_tag}'")

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
                    print(f"   ✅ Atualizado!")
                    updates_count += 1
                else:
                    print(f"   ⚠️ Nenhuma modificação")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                errors_count += 1
        else:
            print(f"   🔍 [DRY-RUN] Seria atualizado")
            updates_count += 1

    # Resumo por grupo
    print("\n" + "=" * 70)
    print("DISTRIBUIÇÃO POR GRUPO")
    print("=" * 70)
    for group, label in GROUP_LABELS.items():
        count = stats.get(group, 0)
        if count > 0:
            print(f"  {label}: {count} agentes")

    print("\n" + "=" * 70)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 70)
    if dry_run:
        print(f"🔍 Agentes que SERIAM atualizados: {updates_count}")
        print("\n⚠️ Execute sem --dry-run para aplicar as alterações")
    else:
        print(f"✅ Agentes atualizados: {updates_count}")
        print(f"❌ Erros: {errors_count}")

    client.close()
    print("\n✅ Conexão fechada")

    # Retornar labels para uso no frontend
    return GROUP_LABELS


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    migrate_groups(dry_run=dry_run)


if __name__ == "__main__":
    main()
