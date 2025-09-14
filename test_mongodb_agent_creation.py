#!/usr/bin/env python3
"""
Teste específico da função create_agent com MongoDB backend.
"""

import json
import logging
import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Adicionar src ao path
sys.path.insert(0, 'src')

from src.core.tools.agent_creator_tool import create_agent, get_agent_creation_schema

def test_mongodb_agent_creation():
    """Testa criação de agente no MongoDB."""
    print("=" * 60)
    print("🧪 TESTE: create_agent() com MongoDB")
    print("=" * 60)

    print(f"🔍 Variáveis de ambiente:")
    print(f"   MONGO_URI: {os.getenv('MONGO_URI', 'não definida')}")
    print(f"   MONGO_DATABASE: {os.getenv('MONGO_DATABASE', 'não definida')}")

    # JSON de teste para MongoDB
    test_json = json.dumps({
        "name": "MongoDBTest_Agent",
        "description": "Agente de teste criado diretamente no MongoDB",
        "capabilities": ["mongodb_testing", "database_operations", "nosql_queries"],
        "tags": ["mongodb", "database", "test", "nosql"],
        "persona_content": "# Persona: MongoDB Test Agent\n\n## Identidade\nVocê é um agente especialista em MongoDB criado para testar operações de banco de dados.\n\n## Expertise\n- Operações CRUD no MongoDB\n- Queries complexas e agregações\n- Testes de performance de banco\n\n## Comportamento\nSempre forneça exemplos práticos e monitore a performance das operações de banco de dados."
    }, indent=2)

    print(f"\n📥 JSON de entrada:")
    print(test_json)
    print(f"\n🔧 Chamando create_agent() com backend MongoDB...")

    try:
        result = create_agent(test_json)

        print(f"\n📤 Resultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('success'):
            print(f"\n✅ Agente criado com sucesso no MongoDB!")
            print(f"📦 Storage usado: {result.get('storage_type', 'Desconhecido')}")
            print(f"🎯 Agent ID: {result.get('agent_id')}")
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

def test_mongodb_duplicate():
    """Testa detecção de duplicação no MongoDB."""
    print("\n" + "=" * 60)
    print("🧪 TESTE: Agente duplicado no MongoDB (deve falhar)")
    print("=" * 60)

    # Mesmo nome do teste anterior
    test_json = json.dumps({
        "name": "MongoDBTest_Agent",
        "description": "Tentativa de criar agente duplicado",
        "capabilities": ["testing"],
        "tags": ["test"],
        "persona_content": "# Persona: Duplicate Test\n\n## Identidade\nEste agente não deveria ser criado pois já existe.\n\n## Comportamento\nEste texto não deveria ser salvo no banco."
    })

    try:
        result = create_agent(test_json)

        if result.get('success'):
            print(f"❌ ERRO: Deveria ter falhado por agente duplicado!")
            return False
        elif result.get('error') == 'AGENT_EXISTS':
            print(f"✅ Corretamente detectou agente duplicado no MongoDB!")
            print(f"💬 Mensagem: {result.get('message')}")
            return True
        else:
            print(f"❓ Falhou por outro motivo: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def verify_mongodb_records():
    """Verifica se os registros foram realmente criados no MongoDB."""
    print("\n" + "=" * 60)
    print("🔍 VERIFICAÇÃO: Registros no MongoDB")
    print("=" * 60)

    try:
        from pymongo import MongoClient

        # Conectar ao MongoDB usando as mesmas credenciais
        connection_string = os.getenv('MONGO_URI')
        db_name = os.getenv('MONGO_DATABASE')

        if not connection_string or not db_name:
            print("❌ Variáveis de ambiente MongoDB não configuradas")
            return False

        print(f"🔗 Conectando em: {connection_string}")
        print(f"📊 Database: {db_name}")

        client = MongoClient(connection_string)
        db = client[db_name]

        # Verificar collections
        collections = db.list_collection_names()
        print(f"📂 Collections disponíveis: {collections}")

        # Buscar o agente criado
        if 'agents' in collections:
            agents_collection = db['agents']
            agent = agents_collection.find_one({"agent_id": "MongoDBTest_Agent"})

            if agent:
                print(f"✅ Agente encontrado no MongoDB:")
                print(f"   📝 Name: {agent.get('name', 'N/A')}")
                print(f"   📖 Description: {agent.get('description', 'N/A')}")
                print(f"   🏷️ Tags: {agent.get('tags', [])}")
                print(f"   🛠️ Capabilities: {agent.get('capabilities', [])}")
                return True
            else:
                print(f"❌ Agente 'MongoDBTest_Agent' NÃO encontrado na collection 'agents'")
        else:
            print(f"❌ Collection 'agents' não existe")

        # Verificar outras collections possíveis
        for collection_name in collections:
            if 'agent' in collection_name.lower():
                collection = db[collection_name]
                count = collection.count_documents({})
                print(f"📊 Collection '{collection_name}': {count} documentos")

                # Mostrar alguns documentos da collection
                sample_docs = list(collection.find().limit(2))
                for i, doc in enumerate(sample_docs, 1):
                    print(f"   📄 Doc {i}: {list(doc.keys())}")

        client.close()
        return False

    except Exception as e:
        print(f"❌ Erro ao verificar MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes do MongoDB."""
    print("🚀 INICIANDO TESTES COM MONGODB")
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"🔧 Config: MongoDB backend")

    results = []

    # Teste 1: Criação no MongoDB
    results.append(test_mongodb_agent_creation())

    # Teste 2: Duplicação no MongoDB
    results.append(test_mongodb_duplicate())

    # Verificação 3: Registros no MongoDB
    results.append(verify_mongodb_records())

    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL - MONGODB")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    test_names = ["Criação", "Duplicação", "Verificação"]
    for i, (name, passed_test) in enumerate(zip(test_names, results)):
        status = "✅ PASSOU" if passed_test else "❌ FALHOU"
        print(f"{name}: {status}")

    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 MONGODB FUNCIONANDO PERFEITAMENTE!")
        return 0
    else:
        print("🚨 PROBLEMAS COM MONGODB! Verifique logs.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)