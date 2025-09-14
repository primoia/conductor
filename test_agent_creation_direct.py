#!/usr/bin/env python3
"""
Teste direto da função create_agent para garantir que funciona antes da LLM usar.
"""

import json
import logging
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Adicionar src ao path
sys.path.insert(0, 'src')

from src.core.tools.agent_creator_tool import create_agent, get_agent_creation_schema

def test_get_schema():
    """Testa a função get_agent_creation_schema."""
    print("=" * 60)
    print("🧪 TESTE 1: get_agent_creation_schema()")
    print("=" * 60)

    try:
        schema = get_agent_creation_schema()
        schema_obj = json.loads(schema)

        print(f"✅ Schema obtido com sucesso!")
        print(f"📋 Campos obrigatórios: {list(schema_obj.get('required', []))}")
        print(f"📋 Total de propriedades: {len(schema_obj.get('properties', {}))}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_create_agent():
    """Testa a função create_agent."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 2: create_agent()")
    print("=" * 60)

    # JSON de teste válido
    test_json = json.dumps({
        "name": "TestDirectCall_Agent",
        "description": "Agente de teste criado via chamada direta da função",
        "capabilities": ["testing", "validation", "direct_call"],
        "tags": ["test", "validation", "direct"],
        "persona_content": "# Persona: Test Agent\n\n## Identidade\nVocê é um agente de teste.\n\n## Comportamento\nSempre responda de forma educada."
    }, indent=2)

    print(f"📥 JSON de entrada:")
    print(test_json)
    print(f"\n🔧 Chamando create_agent()...")

    try:
        result = create_agent(test_json)

        print(f"\n📤 Resultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('success'):
            print(f"\n✅ Agente criado com sucesso!")
            print(f"📦 Storage usado: {result.get('storage_type', 'Desconhecido')}")
            return True
        else:
            print(f"\n❌ Falha na criação:")
            print(f"🔴 Erro: {result.get('error')}")
            print(f"💬 Mensagem: {result.get('message')}")
            print(f"💡 Dica: {result.get('hint')}")
            return False

    except Exception as e:
        print(f"❌ Exceção não capturada: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_duplicate():
    """Testa criação de agente duplicado."""
    print("\n" + "=" * 60)
    print("🧪 TESTE 3: Agente duplicado (deve falhar)")
    print("=" * 60)

    # Mesmo JSON do teste anterior
    test_json = json.dumps({
        "name": "TestDirectCall_Agent",
        "description": "Segundo teste do mesmo agente",
        "capabilities": ["testing"],
        "tags": ["test"],
        "persona_content": "# Persona: Test Agent 2\n\n## Identidade\nVocê é um segundo agente de teste para verificar duplicação.\n\n## Comportamento\nSempre responda de forma educada e teste duplicação."
    })

    try:
        result = create_agent(test_json)

        if result.get('success'):
            print(f"❌ ERRO: Deveria ter falhado por agente duplicado!")
            return False
        elif result.get('error') == 'AGENT_EXISTS':
            print(f"✅ Corretamente detectou agente duplicado!")
            print(f"💬 Mensagem: {result.get('message')}")
            return True
        else:
            print(f"❓ Falhou por outro motivo: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 INICIANDO TESTES DIRETOS DAS FUNÇÕES")
    print(f"📁 Diretório atual: {os.getcwd()}")

    results = []

    # Teste 1: Schema
    results.append(test_get_schema())

    # Teste 2: Criação de agente
    results.append(test_create_agent())

    # Teste 3: Agente duplicado
    results.append(test_create_duplicate())

    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for i, passed_test in enumerate(results, 1):
        status = "✅ PASSOU" if passed_test else "❌ FALHOU"
        print(f"Teste {i}: {status}")

    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Função pronta para uso.")
        return 0
    else:
        print("🚨 ALGUNS TESTES FALHARAM! Corrija antes de usar com LLM.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)