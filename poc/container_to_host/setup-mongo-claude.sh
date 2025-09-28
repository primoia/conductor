#!/bin/bash

# Setup para Claude MongoDB Integration
# Este script configura tudo necessário para a comunicação via MongoDB

echo "🚀 Setup Claude MongoDB Integration"
echo "=" * 50

# Verificar se MongoDB está rodando
echo "🔍 Verificando MongoDB..."
if ! mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null; then
    echo "❌ MongoDB não está rodando. Inicie o MongoDB primeiro:"
    echo "   sudo systemctl start mongod"
    echo "   # ou"
    echo "   brew services start mongodb/brew/mongodb-community"
    exit 1
fi

echo "✅ MongoDB está rodando"

# Instalar PyMongo se necessário
echo "📦 Verificando PyMongo..."
if ! python3 -c "import pymongo" 2>/dev/null; then
    echo "📥 Instalando PyMongo..."
    pip install pymongo
    if [ $? -ne 0 ]; then
        echo "❌ Falha ao instalar PyMongo"
        exit 1
    fi
fi

echo "✅ PyMongo instalado"

# Tornar scripts executáveis
echo "🔧 Configurando permissões..."
chmod +x claude-mongo-watcher.py
chmod +x claude-mongo-client.py

# Criar database e collection
echo "🗄️  Configurando database..."
mongosh --eval "
use conductor;
db.claude_requests.createIndex({status: 1});
db.claude_requests.createIndex({created_at: 1});
db.claude_requests.createIndex({created_at: 1}, {expireAfterSeconds: 86400});
print('✅ Índices criados');
" --quiet

echo ""
echo "🎉 Setup concluído com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Inicie o watcher na sua sessão autenticada:"
echo "   ./claude-mongo-watcher.py"
echo ""
echo "2. Em outro terminal, teste o cliente:"
echo "   ./claude-mongo-client.py --demo"
echo ""
echo "3. Ou teste interativo:"
echo "   ./claude-mongo-client.py"
echo ""
echo "🔗 URLs úteis:"
echo "   MongoDB: mongodb://localhost:27017"
echo "   Database: conductor"
echo "   Collection: claude_requests"
echo ""