#!/usr/bin/env python3
"""
Exemplo de Avaliação de Agentes Conductor

Este script demonstra como usar o sistema de avaliação de agentes
de forma programática, sem usar o script shell.

Autor: Conductor Team
Versão: 1.0
Data: 2025-01-16
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório do script ao path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from agent_evaluator import AgentEvaluator, TestCase

def main():
    """Função principal do exemplo"""
    print("🤖 Sistema de Avaliação de Agentes Conductor")
    print("=" * 50)
    
    # Configurar caminho do Conductor
    conductor_root = script_dir.parent
    print(f"📁 Diretório do Conductor: {conductor_root}")
    
    # Criar avaliador
    evaluator = AgentEvaluator(str(conductor_root))
    
    # Mostrar agentes disponíveis
    print("\n📋 Agentes disponíveis para avaliação:")
    for agent_id in evaluator.test_cases.keys():
        print(f"  - {agent_id}")
    
    # Executar avaliação de exemplo
    print("\n🚀 Executando avaliação de exemplo...")
    
    # Avaliar AgentCreator_Agent
    print("\n1️⃣ Avaliando AgentCreator_Agent...")
    agent_creator_results = []
    for test_case in evaluator.test_cases["AgentCreator_Agent"]:
        print(f"   Teste: {test_case.name}")
        evaluation = evaluator.evaluate_agent("AgentCreator_Agent", test_case)
        agent_creator_results.append(evaluation)
        print(f"   Score: {evaluation.total_score:.2f}/10")
    
    # Avaliar OnboardingGuide_Agent
    print("\n2️⃣ Avaliando OnboardingGuide_Agent...")
    onboarding_results = []
    for test_case in evaluator.test_cases["OnboardingGuide_Agent"]:
        print(f"   Teste: {test_case.name}")
        evaluation = evaluator.evaluate_agent("OnboardingGuide_Agent", test_case)
        onboarding_results.append(evaluation)
        print(f"   Score: {evaluation.total_score:.2f}/10")
    
    # Avaliar KotlinEntityCreator_Agent
    print("\n3️⃣ Avaliando KotlinEntityCreator_Agent...")
    entity_creator_results = []
    for test_case in evaluator.test_cases["KotlinEntityCreator_Agent"]:
        print(f"   Teste: {test_case.name}")
        evaluation = evaluator.evaluate_agent("KotlinEntityCreator_Agent", test_case)
        entity_creator_results.append(evaluation)
        print(f"   Score: {evaluation.total_score:.2f}/10")
    
    # Calcular estatísticas
    print("\n📊 Estatísticas da Avaliação:")
    print("-" * 30)
    
    all_results = {
        "AgentCreator_Agent": agent_creator_results,
        "OnboardingGuide_Agent": onboarding_results,
        "KotlinEntityCreator_Agent": entity_creator_results
    }
    
    for agent_id, results in all_results.items():
        if results:
            scores = [r.total_score for r in results]
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            print(f"\n{agent_id}:")
            print(f"  Score médio: {avg_score:.2f}/10")
            print(f"  Range: {min_score:.2f} - {max_score:.2f}")
            print(f"  Total de testes: {len(results)}")
    
    # Gerar recomendações
    print("\n💡 Recomendações:")
    print("-" * 20)
    
    for agent_id, results in all_results.items():
        if results:
            avg_score = sum(r.total_score for r in results) / len(results)
            
            if avg_score >= 8.0:
                status = "🟢 Excelente"
                recommendation = "Manter padrões atuais"
            elif avg_score >= 7.0:
                status = "🟡 Bom"
                recommendation = "Melhorias moderadas recomendadas"
            elif avg_score >= 6.0:
                status = "🟠 Regular"
                recommendation = "Melhorias necessárias"
            else:
                status = "🔴 Crítico"
                recommendation = "Melhoria urgente necessária"
            
            print(f"\n{agent_id}: {status}")
            print(f"  Recomendação: {recommendation}")
    
    # Salvar resultados
    print("\n💾 Salvando resultados...")
    evaluator._save_comprehensive_report(all_results)
    
    print(f"\n✅ Avaliação concluída!")
    print(f"📁 Resultados salvos em: {evaluator.results_dir}")
    
    # Mostrar próximos passos
    print("\n🎯 Próximos Passos:")
    print("1. Revisar resultados detalhados nos arquivos JSON")
    print("2. Implementar melhorias baseadas nas recomendações")
    print("3. Executar nova avaliação para medir progresso")
    print("4. Estabelecer processo contínuo de monitoramento")
    
    print("\n🔧 Para usar o sistema completo:")
    print(f"   cd {conductor_root}")
    print("   ./scripts/run_agent_evaluation.sh --full --report")

if __name__ == "__main__":
    main()
