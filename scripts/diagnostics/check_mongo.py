#!/usr/bin/env python3
"""
Script de teste para verificar configuração MongoDB
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from core.state_repository import MongoStateRepository

def test_mongo_connection():
    """Testa a conexão e operações básicas com MongoDB."""
    
    print("🔍 Verificando configuração MongoDB...")
    
    # Verificar variável de ambiente
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI não configurada!")
        print("   Configure com: export MONGO_URI='mongodb://localhost:27017'")
        return False
    
    print(f"📝 MONGO_URI: {mongo_uri}")
    
    try:
        # Criar repositório (testa conexão)
        print("🔌 Testando conexão...")
        repo = MongoStateRepository()
        print("✅ Conexão estabelecida com sucesso!")
        
        # Dados de teste
        agent_home_path = "/test/mongo"
        state_file_name = "test_state.json"
        test_data = {
            "conversation_history": [
                {"role": "user", "message": "Teste MongoDB"},
                {"role": "assistant", "message": "MongoDB funcionando!"}
            ],
            "agent_id": "TestAgent",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        print("💾 Testando salvamento...")
        save_result = repo.save_state(agent_home_path, state_file_name, test_data)
        if save_result:
            print("✅ Dados salvos com sucesso!")
        else:
            print("❌ Falha ao salvar dados!")
            return False
        
        print("📖 Testando carregamento...")
        loaded_data = repo.load_state(agent_home_path, state_file_name)
        
        # Verificar se os dados foram carregados corretamente
        if loaded_data.get("agent_id") == test_data["agent_id"]:
            print("✅ Dados carregados com sucesso!")
            print(f"   Agent ID: {loaded_data['agent_id']}")
            print(f"   Mensagens: {len(loaded_data['conversation_history'])}")
            print(f"   Repository type: {loaded_data.get('repository_type', 'N/A')}")
        else:
            print("❌ Dados carregados incorretamente!")
            return False
        
        # Fechar conexão
        repo.close()
        print("🔚 Conexão fechada.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("   Instale pymongo: pip install pymongo")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def show_mongo_examples():
    """Mostra exemplos de configuração MongoDB."""
    
    print("\n📋 Exemplos de configuração MONGO_URI:")
    print("=" * 50)
    
    print("\n1. MongoDB local (sem autenticação):")
    print("   export MONGO_URI='mongodb://localhost:27017'")
    
    print("\n2. MongoDB local (com autenticação):")
    print("   export MONGO_URI='mongodb://user:pass@localhost:27017/conductor_db'")
    
    print("\n3. MongoDB Docker:")
    print("   docker run -d --name mongodb -p 27017:27017 mongo:latest")
    print("   export MONGO_URI='mongodb://localhost:27017'")
    
    print("\n4. MongoDB Atlas (cloud):")
    print("   export MONGO_URI='mongodb+srv://user:pass@cluster.mongodb.net/conductor_db'")
    
    print("\n📊 Estrutura de dados no MongoDB:")
    print("   Database: conductor_state (padrão)")
    print("   Collection: agent_states (padrão)")
    print("   Document ID: {agent_home_path}_{state_file_name}")
    
    print("\n🔧 Comandos úteis:")
    print("   # Ver dados salvos via mongo shell")
    print("   mongo")
    print("   use conductor_state")
    print("   db.agent_states.find().pretty()")

if __name__ == "__main__":
    print("🧪 Teste de Configuração MongoDB")
    print("=" * 40)
    
    if test_mongo_connection():
        print("\n🎉 MongoDB configurado e funcionando!")
    else:
        print("\n💡 Configuração necessária:")
        show_mongo_examples()