#!/usr/bin/env python3
"""
Motor de Sincronização Inteligente - SAGA-019
Implementa migração bidirecional entre backends filesystem e mongodb
com suporte especial para workflows RAMDisk.
"""

import os
import sys
import argparse
import yaml
import time
from typing import Optional, Tuple
from pathlib import Path

# Adicionar src ao path para imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.container import container
from src.core.services.configuration_service import ConfigurationService
from src.core.services.storage_service import StorageService
from src.ports.state_repository import IStateRepository
from src.config import Settings


class SyncEngine:
    """Motor de sincronização bidirecional entre backends de storage."""
    
    def __init__(self):
        """Inicializar motor com configuração do container DI."""
        self.settings = Settings()
        self.config_service = ConfigurationService()
        self.start_time = time.time()
        
    def check_mongodb_availability(self) -> bool:
        """Verificar se MongoDB está configurado e acessível."""
        if not self.settings.mongo_uri:
            print("⚠️  MongoDB não configurado!")
            print("📖 Configure MONGO_URI no seu arquivo .env")
            print("🔗 Documentação: https://docs.conductor.dev/mongodb-setup")
            return False
        
        try:
            # Testar conectividade básica
            from pymongo import MongoClient
            client = MongoClient(self.settings.mongo_uri, serverSelectionTimeoutMS=5000)
            client.server_info()  # Força conexão
            print(f"✅ MongoDB conectado: {self.settings.mongo_uri}")
            return True
        except Exception as e:
            print(f"❌ MongoDB não acessível: {e}")
            print("🔧 Verifique se o MongoDB está rodando")
            return False
    
    def get_repositories(self, source_type: str, dest_type: str, custom_path: Optional[str] = None) -> Tuple[IStateRepository, IStateRepository]:
        """Obter instâncias de IStateRepository para origem e destino."""
        
        def create_repo(backend_type: str, path: Optional[str] = None) -> IStateRepository:
            if backend_type == "filesystem":
                from src.infrastructure.storage.filesystem_repository import FileSystemStateRepository
                fs_path = path or self.config_service.get_storage_config().path
                return FileSystemStateRepository(base_path=fs_path)
            elif backend_type == "mongodb":
                from src.infrastructure.storage.mongo_repository import MongoStateRepository
                return MongoStateRepository(
                    connection_string=self.settings.mongo_uri,
                    db_name=self.settings.mongo_database
                )
            else:
                raise ValueError(f"Tipo de backend desconhecido: {backend_type}")
        
        # Aplicar custom_path apenas ao destino se for filesystem
        source_path = None
        dest_path = custom_path if dest_type == "filesystem" else None
        
        source_repo = create_repo(source_type, source_path)
        dest_repo = create_repo(dest_type, dest_path)
        
        return source_repo, dest_repo
    
    def migrate_agents(self, source_repo: IStateRepository, dest_repo: IStateRepository) -> dict:
        """Transferir agentes entre repositórios com logs detalhados."""
        print("🔄 Iniciando migração de agentes...")
        
        # Descobrir agentes
        print("📊 Descobrindo agentes...")
        try:
            agent_ids = source_repo.list_agents()
            if not agent_ids:
                print("   ⚠️  Nenhum agente encontrado no backend de origem")
                return {"success": True, "agents_migrated": 0, "files_transferred": 0}
            
            print(f"   ✓ Encontrados {len(agent_ids)} agentes: {agent_ids}")
        except Exception as e:
            print(f"   ❌ Erro ao listar agentes: {e}")
            return {"success": False, "error": str(e)}
        
        # Transferir dados
        print("\n📦 Transferindo dados:")
        total_files = 0
        migrated_agents = 0
        
        for agent_id in agent_ids:
            print(f"   🤖 {agent_id}")
            agent_files = 0
            
            try:
                # Transferir definition.yaml
                definition = source_repo.load_definition(agent_id)
                if definition:
                    dest_repo.save_definition(agent_id, definition)
                    size = len(str(definition).encode('utf-8'))
                    print(f"      ✓ definition.yaml ({size:,}B) → destino")
                    agent_files += 1
                
                # Transferir persona.md
                persona = source_repo.load_persona(agent_id)
                if persona:
                    dest_repo.save_persona(agent_id, persona)
                    size = len(persona.encode('utf-8'))
                    print(f"      ✓ persona.md ({size:,}B) → destino")
                    agent_files += 1
                else:
                    print("      ⚠️  persona.md não encontrado, pulando...")
                
                # Transferir session.json
                session = source_repo.load_session(agent_id)
                if session:
                    dest_repo.save_session(agent_id, session)
                    size = len(str(session).encode('utf-8'))
                    print(f"      ✓ session.json ({size:,}B) → destino")
                    agent_files += 1
                
                # Transferir knowledge.json (se existir)
                try:
                    knowledge = source_repo.load_knowledge(agent_id)
                    if knowledge:
                        dest_repo.save_knowledge(agent_id, knowledge)
                        size = len(str(knowledge).encode('utf-8'))
                        print(f"      ✓ knowledge.json ({size:,}B) → destino")
                        agent_files += 1
                except AttributeError:
                    # Método pode não existir em todas as implementações
                    pass
                
                total_files += agent_files
                migrated_agents += 1
                
            except Exception as e:
                print(f"      ❌ Erro ao migrar {agent_id}: {e}")
                continue
        
        duration = time.time() - self.start_time
        
        print(f"\n✅ Migração concluída!")
        print(f"   📈 {migrated_agents} agentes, {total_files} arquivos transferidos")
        print(f"   ⏱️  Tempo total: {duration:.1f}s")
        
        return {
            "success": True,
            "agents_migrated": migrated_agents,
            "files_transferred": total_files,
            "duration": duration
        }
    
    def update_config_if_needed(self, new_backend: str, no_config_update: bool) -> bool:
        """Atualizar config.yaml condicionalmente."""
        if no_config_update:
            print("🔒 Configuração preservada (--no-config-update)")
            return True
        
        print("\n⚙️  Atualizando configuração...")
        
        try:
            config_path = "config.yaml"
            
            # Backup do config atual
            backup_path = f"config.yaml.backup.{int(time.time())}"
            if os.path.exists(config_path):
                import shutil
                shutil.copy2(config_path, backup_path)
                print(f"   💾 Backup salvo: {backup_path}")
            
            # Carregar e modificar config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'storage' not in config:
                config['storage'] = {}
            
            old_type = config['storage'].get('type', 'filesystem')
            config['storage']['type'] = new_backend
            
            # Configurações específicas do backend
            if new_backend == 'mongodb':
                # Manter path do filesystem como backup
                if 'path' in config['storage']:
                    config['storage']['backup_path'] = config['storage']['path']
                # Remover path para mongodb
                config['storage'].pop('path', None)
            elif new_backend == 'filesystem':
                # Restaurar path se existir backup
                if 'backup_path' in config['storage']:
                    config['storage']['path'] = config['storage']['backup_path']
                    config['storage'].pop('backup_path', None)
                elif 'path' not in config['storage']:
                    config['storage']['path'] = '.conductor_workspace'
            
            # Salvar config atualizado
            with open(config_path, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"   ✓ config.yaml atualizado: storage.type = {new_backend}")
            print(f"   📝 Anterior: {old_type} → Novo: {new_backend}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erro ao atualizar config.yaml: {e}")
            return False
    
    def run_migration(self, source: str, destination: str, path: Optional[str] = None, no_config_update: bool = False) -> bool:
        """Executar migração completa."""
        print("="*60)
        print(f"🔄 Iniciando migração: {source} → {destination}")
        print("="*60)
        
        # Validações de pré-requisitos
        if destination == "mongodb" and not self.check_mongodb_availability():
            return False
        
        if source == "mongodb" and not self.check_mongodb_availability():
            return False
        
        # Obter repositórios
        try:
            source_repo, dest_repo = self.get_repositories(source, destination, path)
        except Exception as e:
            print(f"❌ Erro ao configurar repositórios: {e}")
            return False
        
        # Executar migração
        result = self.migrate_agents(source_repo, dest_repo)
        if not result["success"]:
            return False
        
        # Atualizar configuração se necessário
        if not self.update_config_if_needed(destination, no_config_update):
            print("⚠️  Migração de dados concluída, mas config.yaml não foi atualizado")
        
        print("\n🎉 Processo concluído com sucesso!")
        return True


def main():
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Motor de Sincronização - SAGA-019",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Backup RAMDisk → MongoDB (sem alterar config)
  %(prog)s --source filesystem --destination mongodb --no-config-update
  
  # Restore MongoDB → RAMDisk (sem alterar config)
  %(prog)s --source mongodb --destination filesystem --no-config-update
  
  # Migração permanente para MongoDB
  %(prog)s --source filesystem --destination mongodb
  
  # Backup para path externo
  %(prog)s --source filesystem --destination filesystem --path /backup/path
        """
    )
    
    parser.add_argument("--source", required=True, choices=["filesystem", "mongodb"],
                       help="Backend de origem")
    parser.add_argument("--destination", required=True, choices=["filesystem", "mongodb"],
                       help="Backend de destino")
    parser.add_argument("--path", help="Path específico para filesystem (origem ou destino)")
    parser.add_argument("--no-config-update", action="store_true",
                       help="Não atualizar config.yaml")
    
    args = parser.parse_args()
    
    # Validação básica
    if args.source == args.destination and not args.path:
        print("❌ Origem e destino são iguais. Use --path para especificar path diferente.")
        return 1
    
    # Executar migração
    engine = SyncEngine()
    success = engine.run_migration(
        source=args.source,
        destination=args.destination,
        path=args.path,
        no_config_update=args.no_config_update
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
