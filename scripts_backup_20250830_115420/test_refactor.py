#!/usr/bin/env python3
"""
Script de teste para validar a refatoração do run_conductor.py
"""

import os
import sys
import subprocess
import tempfile
import yaml
from pathlib import Path

def create_test_plan():
    """Criar um plano de teste temporário"""
    test_plan = {
        'storyId': 'TEST-REFACTOR-001',
        'description': 'Teste da refatoração do Conductor',
        'tasks': [
            {
                'name': 'teste_claude',
                'description': 'Teste com Claude',
                'agent': 'KotlinEntityCreator_Agent',
                'inputs': [],
                'outputs': ['test_claude_output.txt'],
                'depends_on': None
            }
        ],
        'validationCriteria': [
            'Arquivo de saída deve ser criado',
            'Arquivo não deve estar vazio'
        ]
    }
    
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(test_plan, temp_file)
    temp_file.close()
    
    return temp_file.name

def test_claude_provider():
    """Test Claude provider"""
    print("🧪 Testing Claude provider...")
    
    test_plan = create_test_plan()
    project_path = os.getcwd()
    
    try:
        # Executar com Claude
        cmd = [
            sys.executable, 'run_conductor.py',
            '--ai-provider', 'claude',
            '--project-path', project_path,
            test_plan
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ Teste Claude: SUCESSO")
            return True
        else:
            print(f"❌ Teste Claude: FALHOU")
            print(f"Erro: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Teste Claude: EXCEÇÃO - {e}")
        return False
    finally:
        # Limpar arquivo temporário
        os.unlink(test_plan)

def test_gemini_provider():
    """Test Gemini provider"""
    print("🧪 Testing Gemini provider...")
    
    test_plan = create_test_plan()
    project_path = os.getcwd()
    
    try:
        # Executar com Gemini
        cmd = [
            sys.executable, 'run_conductor.py',
            '--ai-provider', 'gemini',
            '--project-path', project_path,
            test_plan
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ Teste Gemini: SUCESSO")
            return True
        else:
            print(f"❌ Teste Gemini: FALHOU")
            print(f"Erro: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Teste Gemini: EXCEÇÃO - {e}")
        return False
    finally:
        # Limpar arquivo temporário
        os.unlink(test_plan)

def test_argument_parsing():
    """Test argument parsing"""
    print("🧪 Testing argument parsing...")
    
    try:
        # Testar ajuda
        cmd = [sys.executable, 'run_conductor.py', '--help']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0 and '--ai-provider' in result.stdout:
            print("✅ Teste argumentos: SUCESSO")
            return True
        else:
            print("❌ Teste argumentos: FALHOU")
            return False
            
    except Exception as e:
        print(f"❌ Teste argumentos: EXCEÇÃO - {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Conductor refactoring tests")
    print("=" * 50)
    
    # Check if we're in the correct directory
    if not os.path.exists('run_conductor.py'):
        print("❌ ERROR: Run this script in the conductor/scripts/ directory")
        sys.exit(1)
    
    tests = [
        test_argument_parsing,
        test_claude_provider,
        test_gemini_provider
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()
