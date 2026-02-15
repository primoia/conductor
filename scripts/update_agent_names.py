#!/usr/bin/env python3
"""
Script para atualizar definition.name com nomes definidos manualmente.

Uso:
    python scripts/update_agent_names.py [--dry-run]
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/?authSource=admin')
DB_NAME = os.getenv('MONGO_DB', 'conductor_state')

# Mapeamento manual: agent_id → display_name
AGENT_NAMES = {
    'AIBusinessProposal_Agent': 'AI Business Proposal',
    'APIArchitect_Agent': 'API Architect',
    'AgentCreator_Agent': 'Agent Creator',
    'AgentEvaluator_Agent': 'Agent Evaluator',
    'AngularExpert_Agent': 'Angular Expert',
    'AngularRefactorAnalyst_Agent': 'Angular Refactor Analyst',
    'BusinessStrategy_Agent': 'Business Strategy',
    'CRMAnalytics_Agent': 'CRM Analytics',
    'CareerArchitect_Agent': 'Career Architect',
    'CodeReviewer_Agent': 'Code Reviewer',
    'CommitMessage_Agent': 'Commit Message',
    'ConversationToFeature_Agent': 'Conversation to Feature',
    'Counselor_Agent': 'Counselor',
    'DatabaseExpert_Agent': 'Database Expert',
    'DealPredictor_CRM_Agent': 'Deal Predictor CRM',
    'DevOpsEngineer_Agent': 'DevOps Engineer',
    'DocWriter_Agent': 'Doc Writer',
    'DockerSecurityArchitect_Agent': 'Docker Security Architect',
    'DocumentationExpert_Agent': 'Documentation Expert',
    'EmailAssistant_CRM_Agent': 'Email Assistant CRM',
    'ExecutionPlanValidator_Agent': 'Execution Plan Validator',
    'Executor_Agent': 'Executor',
    'GitLinkedInPromotion_Agent': 'Git LinkedIn Promotion',
    'Hunter_Agent': 'Hunter',
    'IdeaCompanion_Agent': 'Idea Companion',
    'LeadQualifier_CRM_Agent': 'Lead Qualifier CRM',
    'LinkedInContent_Agent': 'LinkedIn Content',
    'LogAnalyzer_Agent': 'Log Analyzer',
    'MCPToolsTester_Agent': 'MCP Tools Tester',
    'Maestro_Agent': 'Maestro',
    'MongoDBTest_Agent': 'MongoDB Test',
    'MongoKotlinExpert_Agent': 'MongoDB Kotlin Expert',
    'MongoTest_Agent': 'MongoDB Test',
    'MonorepoCommitOrchestrator_Agent': 'Monorepo Commit Orchestrator',
    'NormalizedTest12345_Agent': 'Normalized Test',
    'PerformanceOptimizer_Agent': 'Performance Optimizer',
    'PrimoiaCRM_Agent': 'Primoia CRM',
    'PrimoiaGitOrchestrator_Agent': 'Primoia Git Orchestrator',
    'ProgrammingLanguages_Agent': 'Programming Languages',
    'PythonMicroservicesArchitect_Agent': 'Python Microservices Architect',
    'ReactExpert_Agent': 'React Expert',
    'RequirementsEngineer_Agent': 'Requirements Engineer',
    'SagaPlanner_Agent': 'Saga Planner',
    'ScreenplayAssistant_Agent': 'Screenplay Assistant',
    'ScreenplayNarrativeDeveloper_Agent': 'Screenplay Narrative Developer',
    'SecuritySpecialist_Agent': 'Security Specialist',
    'SeniorCodeExecutor_Agent': 'Senior Code Executor',
    'SequenceDiagramGenerator_Agent': 'Sequence Diagram Generator',
    'StrategicComment_Agent': 'Strategic Comment',
    'SystemGuide_Meta_Agent': 'System Guide',
    'TestAgent': 'Test Agent',
    'TestDirectCall_Agent': 'Test Direct Call',
    'TestNormalizedV2_Agent': 'Test Normalized V2',
    'TestNormalized_Agent': 'Test Normalized',
    'TestQuickValidation_Agent': 'Test Quick Validation',
    'TestingSpecialist_Agent': 'Testing Specialist',
    'Visionary_Agent': 'Visionary',
    'WebScraper_Agent': 'Web Scraper',
    'linkedin_creator_Agent': 'LinkedIn Creator',
    'resume_formatter_Agent': 'Resume Formatter',
}


def update_agent_names(dry_run: bool = False):
    print("=" * 70)
    print("ATUALIZAÇÃO DE NOMES DE AGENTES")
    print("=" * 70)
    print(f"Modo: {'DRY-RUN' if dry_run else 'EXECUÇÃO REAL'}")
    print("=" * 70)

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Conectado ao MongoDB\n")
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

    db = client[DB_NAME]
    agents_collection = db["agents"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    updated = 0
    skipped = 0

    for agent_id, new_name in sorted(AGENT_NAMES.items()):
        doc = agents_collection.find_one({'agent_id': agent_id})
        if not doc:
            print(f"⚠️  {agent_id}: não encontrado")
            continue

        current_name = doc.get('definition', {}).get('name', '')

        if current_name == new_name:
            print(f"⏭️  {agent_id}: já é '{new_name}'")
            skipped += 1
            continue

        print(f"📝 {agent_id}: '{current_name}' → '{new_name}'")

        if not dry_run:
            agents_collection.update_one(
                {'agent_id': agent_id},
                {'$set': {'definition.name': new_name, 'updated_at': now}}
            )
            updated += 1
        else:
            updated += 1

    print("\n" + "=" * 70)
    if dry_run:
        print(f"🔍 Seriam atualizados: {updated}")
        print(f"⏭️  Já corretos: {skipped}")
        print("\n⚠️ Execute sem --dry-run para aplicar")
    else:
        print(f"✅ Atualizados: {updated}")
        print(f"⏭️  Ignorados: {skipped}")

    client.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    update_agent_names(dry_run=dry_run)
