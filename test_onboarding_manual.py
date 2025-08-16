#!/usr/bin/env python3
"""
Script para testar manualmente o sistema de onboarding
"""

import sys
import os
sys.path.append('scripts')

from scripts.genesis_agent import Toolbelt
import json

def test_user_profile_collection():
    """Teste da coleta de perfil do usuário"""
    print("🧪 Testando coleta de perfil de usuário...")
    print("=" * 50)
    
    toolbelt = Toolbelt('/tmp/test_onboarding')
    
    # Simular dados (você pode modificar aqui para testar diferentes cenários)
    simulated_responses = {
        'name': 'João Developer',
        'role': 'backend',
        'main_language': 'kotlin',
        'main_framework': 'spring-boot',
        'experience_level': 'mid',
        'project_type': 'new',
        'team_size': 'team'
    }
    
    print("📝 Dados simulados:")
    for key, value in simulated_responses.items():
        print(f"   {key}: {value}")
    
    return simulated_responses

def test_project_context():
    """Teste da coleta de contexto do projeto"""
    print("\n🧪 Testando coleta de contexto do projeto...")
    print("=" * 50)
    
    context = {
        'project_name': 'meu_app_kotlin',
        'project_root': '/tmp/test_project',
        'environment': 'develop',
        'is_new_project': True,
        'existing_structure_detected': False
    }
    
    print("📁 Contexto simulado:")
    for key, value in context.items():
        print(f"   {key}: {value}")
    
    return context

def test_suggestion_engine():
    """Teste do engine de sugestões"""
    print("\n🧪 Testando engine de sugestões...")
    print("=" * 50)
    
    toolbelt = Toolbelt('/tmp/test_onboarding')
    
    # Usar dados simulados
    user_profile = test_user_profile_collection()
    project_context = test_project_context()
    
    print("\n🔍 Executando sugestão baseada no perfil...")
    result = toolbelt.suggest_team_template(user_profile, project_context)
    
    if result['success']:
        print(f"✅ Sugestões geradas: {len(result['suggestions'])}")
        
        print("\n🎯 Top 3 Recomendações:")
        for i, suggestion in enumerate(result['suggestions'][:3], 1):
            print(f"{i}. {suggestion['template_name']}")
            print(f"   Score: {suggestion['score']} | Confidence: {suggestion['confidence']:.2f}")
            print(f"   Razões: {', '.join(suggestion['reasons'])}")
            print()
        
        if 'rules_version' in result:
            print(f"📋 Usando rules engine versão: {result['rules_version']}")
    else:
        print(f"❌ Falha na sugestão: {result.get('error', 'Unknown error')}")
    
    return result

def test_example_creation():
    """Teste da criação de projeto de exemplo"""
    print("\n🧪 Testando criação de projeto de exemplo...")
    print("=" * 50)
    
    toolbelt = Toolbelt('/tmp/test_onboarding')
    
    # Criar projeto de exemplo
    result = toolbelt.create_example_project(
        project_root='/tmp/test_example',
        team_template_id='kotlin-backend-basic-team',
        user_profile={'main_language': 'kotlin', 'role': 'backend'}
    )
    
    if result['success']:
        print(f"✅ Projeto de exemplo criado!")
        print(f"   Arquivos criados: {len(result['created_files'])}")
        print(f"   Tipo: {result['project_type']}")
        print(f"   Team: {result['team_name']}")
        
        print("\n📄 Arquivos gerados:")
        for file_path in result['created_files']:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"   ✅ {os.path.basename(file_path)}: {size} bytes")
            else:
                print(f"   ❌ Arquivo não encontrado: {file_path}")
    else:
        print(f"❌ Falha na criação: {result.get('error', 'Unknown error')}")
    
    return result

def main():
    """Função principal de teste"""
    print("🎼 TESTE MANUAL DO SISTEMA DE ONBOARDING")
    print("=" * 60)
    print("Este script testa os componentes do OnboardingGuide_Agent")
    print()
    
    # Executar testes sequenciais
    try:
        # 1. Testar coleta de perfil
        profile = test_user_profile_collection()
        
        # 2. Testar contexto do projeto
        context = test_project_context()
        
        # 3. Testar engine de sugestões
        suggestions = test_suggestion_engine()
        
        # 4. Testar criação de exemplo
        example = test_example_creation()
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES:")
        print(f"   ✅ Perfil de usuário: Simulado")
        print(f"   ✅ Contexto do projeto: Simulado") 
        print(f"   {'✅' if suggestions.get('success') else '❌'} Engine de sugestões: {'OK' if suggestions.get('success') else 'FALHOU'}")
        print(f"   {'✅' if example.get('success') else '❌'} Criação de exemplo: {'OK' if example.get('success') else 'FALHOU'}")
        
        print("\n🚀 PRÓXIMO PASSO:")
        print("   Para testar o chat completo, execute:")
        print("   python scripts/genesis_agent.py --embody OnboardingGuide_Agent --project-root /tmp/meu_projeto --repl")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()