#!/usr/bin/env python3
"""
Claude MongoDB Client - Cliente para testar comunicação via MongoDB
Simula como o Conductor irá se comunicar com o Claude
"""

import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from pymongo import MongoClient
    from bson import ObjectId
except ImportError:
    print("❌ PyMongo não encontrado. Instale com: pip install pymongo")
    sys.exit(1)

class ClaudeMongoClient:
    def __init__(self,
                 mongo_uri: str = "mongodb://localhost:27017",
                 database: str = "conductor",
                 collection: str = "claude_requests"):
        """
        Cliente para comunicação com Claude via MongoDB

        Args:
            mongo_uri: URI de conexão MongoDB
            database: Nome do database
            collection: Nome da collection
        """
        self.mongo_uri = mongo_uri
        self.database_name = database
        self.collection_name = collection

        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[database]
            self.collection = self.db[collection]

            # Testar conexão
            self.client.admin.command('ping')
            print(f"✅ Conectado ao MongoDB: {mongo_uri}")

        except Exception as e:
            print(f"❌ Erro ao conectar MongoDB: {e}")
            raise

    def create_request(self, command: List[str], cwd: str = ".",
                      timeout: int = 180) -> ObjectId:
        """
        Criar um novo request para o Claude

        Args:
            command: Lista de comandos (ex: ["claude", "-p", "Hello"])
            cwd: Diretório de trabalho
            timeout: Timeout em segundos

        Returns:
            ObjectId: ID do request criado
        """
        request_doc = {
            "command": command,
            "cwd": cwd,
            "timeout": timeout,
            "status": "pending",
            "created_at": datetime.now(timezone.utc)
        }

        result = self.collection.insert_one(request_doc)
        print(f"📤 Request criado: {result.inserted_id}")
        return result.inserted_id

    def get_request_status(self, request_id: ObjectId) -> Optional[Dict]:
        """Verificar status de um request"""
        return self.collection.find_one({"_id": request_id})

    def wait_for_completion(self, request_id: ObjectId,
                           timeout: int = 180, poll_interval: float = 0.5) -> Dict:
        """
        Aguardar conclusão de um request

        Args:
            request_id: ID do request
            timeout: Timeout total em segundos
            poll_interval: Intervalo entre verificações

        Returns:
            Dict: Documento do request completo
        """
        start_time = time.time()

        print(f"⏳ Aguardando conclusão do request: {request_id}")

        while True:
            # Verificar se ultrapassou timeout
            if time.time() - start_time > timeout:
                return {
                    "status": "timeout",
                    "error": f"Timeout após {timeout}s aguardando conclusão"
                }

            # Buscar status atual
            request_doc = self.get_request_status(request_id)

            if not request_doc:
                return {
                    "status": "error",
                    "error": "Request não encontrado"
                }

            status = request_doc.get("status")

            # Verificar se completou
            if status in ["completed", "error"]:
                duration = time.time() - start_time
                print(f"✅ Request concluído em {duration:.1f}s - Status: {status}")
                return request_doc

            # Aguardar próxima verificação
            time.sleep(poll_interval)

    def call_claude(self, command: List[str], cwd: str = ".",
                   timeout: int = 180) -> Dict:
        """
        Chamar Claude de forma síncrona (criar request + aguardar resposta)

        Args:
            command: Lista de comandos
            cwd: Diretório de trabalho
            timeout: Timeout em segundos

        Returns:
            Dict: Resultado da execução
        """
        # Criar request
        request_id = self.create_request(command, cwd, timeout)

        # Aguardar conclusão
        result = self.wait_for_completion(request_id, timeout)

        return result

    def list_pending_requests(self) -> List[Dict]:
        """Listar requests pendentes"""
        return list(self.collection.find(
            {"status": "pending"},
            sort=[("created_at", 1)]
        ))

    def list_recent_requests(self, limit: int = 10) -> List[Dict]:
        """Listar requests recentes"""
        return list(self.collection.find(
            {},
            sort=[("created_at", -1)],
            limit=limit
        ))

    def cleanup_old_requests(self, hours: int = 24) -> int:
        """
        Limpar requests antigos

        Args:
            hours: Idade máxima em horas

        Returns:
            int: Número de documentos removidos
        """
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        cutoff_date = datetime.fromtimestamp(cutoff_time, tz=timezone.utc)

        result = self.collection.delete_many({
            "created_at": {"$lt": cutoff_date}
        })

        print(f"🧹 Removidos {result.deleted_count} requests antigos")
        return result.deleted_count

def demo():
    """Demonstração do cliente"""
    print("🤖 Claude MongoDB Client - Demo")
    print("=" * 50)

    try:
        client = ClaudeMongoClient()

        # Teste 1: Help command
        print("\n📋 Teste 1: Claude Help")
        result = client.call_claude(
            command=["claude", "--help"],
            cwd="/tmp"
        )

        print(f"Status: {result.get('status')}")
        if result.get('status') == 'completed':
            output = result.get('result', '')
            lines = output.split('\n')[:5]
            print("Resultado (primeiras linhas):")
            for line in lines:
                print(f"  {line}")
            print(f"  ... (total: {len(output)} caracteres)")
        else:
            print(f"Erro: {result.get('result', 'Erro desconhecido')}")

        # Teste 2: Prompt simples
        print("\n💬 Teste 2: Claude com prompt")
        result = client.call_claude(
            command=["claude", "-p", "Diga olá em português em 5 palavras"],
            cwd="/tmp"
        )

        print(f"Status: {result.get('status')}")
        print(f"Resultado: {result.get('result', 'Sem resultado')}")

        # Teste 3: README específico
        print("\n📁 Teste 3: Resumir README.md")
        result = client.call_claude(
            command=["claude", "-p", "Resuma o arquivo README.md em 3 frases"],
            cwd="/mnt/ramdisk/develop/nex-web-backend"
        )

        print(f"Status: {result.get('status')}")
        output = result.get('result', 'Sem resultado')
        if len(output) > 200:
            print(f"Resultado: {output[:200]}...")
        else:
            print(f"Resultado: {output}")

        # Mostrar estatísticas
        print("\n📊 Estatísticas:")
        pending = client.list_pending_requests()
        recent = client.list_recent_requests(5)

        print(f"Requests pendentes: {len(pending)}")
        print(f"Últimos 5 requests:")
        for req in recent:
            created = req.get('created_at', 'N/A')
            status = req.get('status', 'N/A')
            cmd = ' '.join(req.get('command', []))[:30]
            print(f"  {created} - {status} - {cmd}...")

    except Exception as e:
        print(f"❌ Erro na demo: {e}")

def main():
    """Função principal para testes interativos"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude MongoDB Client")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017",
                       help="URI de conexão MongoDB")
    parser.add_argument("--database", default="conductor",
                       help="Nome do database")
    parser.add_argument("--collection", default="claude_requests",
                       help="Nome da collection")
    parser.add_argument("--demo", action="store_true",
                       help="Executar demonstração")

    args = parser.parse_args()

    if args.demo:
        demo()
    else:
        # Modo interativo simples
        client = ClaudeMongoClient(
            mongo_uri=args.mongo_uri,
            database=args.database,
            collection=args.collection
        )

        print("Digite comandos Claude (ou 'quit' para sair):")
        while True:
            try:
                prompt = input("\n> ")
                if prompt.lower() in ['quit', 'exit', 'q']:
                    break

                if prompt.strip():
                    result = client.call_claude(
                        command=["claude", "-p", prompt],
                        cwd="."
                    )
                    print(f"\nStatus: {result.get('status')}")
                    print(f"Resultado: {result.get('result', 'Sem resultado')}")

            except KeyboardInterrupt:
                print("\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()