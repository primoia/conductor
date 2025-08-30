#!/usr/bin/env python3
"""
Script de Migração de Agentes v1.x para v2.0
Migra agentes da estrutura legada para a nova arquitetura orientada a ambientes.

Uso:
    python scripts/migrate_agents_v2.py [--dry-run]
"""

import os
import sys
import shutil
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional

# Adiciona o diretório raiz do projeto ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

class AgentMigrator:
    def __init__(self, dry_run: bool = False, auto_confirm: bool = False):
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm
        self.conductor_root = Path(__file__).parent.parent
        self.legacy_agents_path = self.conductor_root / "projects" / "develop" / "agents"
        self.backup_path = self.conductor_root / "backups" / "agents_v1_backup"
        
        # Configurações específicas por agente
        self.agent_configs = {
            "AgentCreator_Agent": {
                "environment": "develop",
                "project_key": None,  # Meta-agente, não tem projeto alvo
                "output_scope": None,  # Permissões especiais
                "execution_mode": "meta_agent"
            },
            "KotlinEntityCreator_Agent": {
                "environment": "develop", 
                "project_key": "nex-web-backend",
                "output_scope": "src/main/kotlin/br/com/nextar/entity/*.kt",
                "execution_mode": "project_resident"
            },
            "KotlinRepositoryCreator_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend", 
                "output_scope": "src/main/kotlin/br/com/nextar/repository/*.kt",
                "execution_mode": "project_resident"
            },
            "KotlinServiceCreator_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend",
                "output_scope": "src/main/kotlin/br/com/nextar/service/*.kt", 
                "execution_mode": "project_resident"
            },
            "KotlinTestCreator_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend",
                "output_scope": "src/test/kotlin/br/com/nextar/**/*Test.kt",
                "execution_mode": "project_resident"
            },
            "OnboardingGuide_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend",
                "output_scope": "docs/onboarding/*.md",
                "execution_mode": "project_resident"
            },
            "PlanCreator_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend", 
                "output_scope": "workspace/plans/*.yaml",
                "execution_mode": "project_resident"
            },
            "ProblemRefiner_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend",
                "output_scope": "workspace/analysis/*.md",
                "execution_mode": "project_resident"
            },
            "PythonDocumenter_Agent": {
                "environment": "develop",
                "project_key": "nex-web-backend",
                "output_scope": "docs/api/*.md",
                "execution_mode": "project_resident"
            }
        }
    
    def create_backup(self):
        """Cria backup dos agentes originais antes da migração."""
        if self.backup_path.exists():
            print(f"❌ Backup já existe em {self.backup_path}")
            if not self.auto_confirm:
                response = input("Sobrescrever backup existente? (y/N): ")
                if response.lower() != 'y':
                    print("Migração cancelada.")
                    sys.exit(1)
            shutil.rmtree(self.backup_path)
        
        print(f"📦 Criando backup em {self.backup_path}")
        if not self.dry_run:
            self.backup_path.parent.mkdir(exist_ok=True)
            shutil.copytree(self.legacy_agents_path, self.backup_path)
        print("✅ Backup criado com sucesso!")
    
    def get_new_agent_path(self, agent_id: str) -> Path:
        """Calcula o novo caminho para um agente na estrutura v2.0."""
        config = self.agent_configs[agent_id]
        
        if config["project_key"] is None:
            # Meta-agente (AgentCreator_Agent) - vai para _common
            return self.conductor_root / "projects" / "_common" / "agents" / agent_id
        else:
            # Agente de projeto - vai para projects/<env>/<proj>/agents/<id>
            return (self.conductor_root / "projects" / 
                   config["environment"] / config["project_key"] / "agents" / agent_id)
    
    def update_agent_yaml(self, agent_path: Path, agent_id: str) -> Dict:
        """Atualiza o agent.yaml com a nova estrutura v2.0."""
        agent_yaml_path = agent_path / "agent.yaml"
        
        if not agent_yaml_path.exists():
            raise FileNotFoundError(f"agent.yaml não encontrado em {agent_yaml_path}")
        
        with open(agent_yaml_path, 'r', encoding='utf-8') as f:
            agent_data = yaml.safe_load(f)
        
        config = self.agent_configs[agent_id]
        
        # Atualiza versão para 2.0
        agent_data['version'] = '2.0'
        
        # Adiciona execution_mode
        agent_data['execution_mode'] = config['execution_mode']
        
        # Adiciona target_context apenas para agentes de projeto
        if config['project_key'] is not None:
            agent_data['target_context'] = {
                'project_key': config['project_key'],
                'output_scope': config['output_scope']
            }
        
        return agent_data
    
    def migrate_agent(self, agent_id: str):
        """Migra um agente específico para a nova estrutura."""
        print(f"\n🔄 Migrando {agent_id}...")
        
        old_path = self.legacy_agents_path / agent_id
        new_path = self.get_new_agent_path(agent_id)
        
        if not old_path.exists():
            print(f"❌ Agente {agent_id} não encontrado em {old_path}")
            return False
        
        print(f"   📂 De: {old_path}")
        print(f"   📂 Para: {new_path}")
        
        if not self.dry_run:
            # Cria diretório de destino
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia todos os arquivos
            shutil.copytree(old_path, new_path, dirs_exist_ok=True)
            
            # Atualiza o agent.yaml
            try:
                updated_yaml = self.update_agent_yaml(new_path, agent_id)
                with open(new_path / "agent.yaml", 'w', encoding='utf-8') as f:
                    yaml.dump(updated_yaml, f, default_flow_style=False, allow_unicode=True)
                print(f"   ✅ agent.yaml atualizado para v2.0")
            except Exception as e:
                print(f"   ❌ Erro ao atualizar agent.yaml: {e}")
                return False
        
        config = self.agent_configs[agent_id]
        if config['project_key']:
            print(f"   🎯 Projeto: {config['project_key']}")
            print(f"   🔒 Escopo: {config['output_scope']}")
        else:
            print(f"   🤖 Meta-agente (sem projeto alvo)")
        
        return True
    
    def cleanup_legacy_structure(self):
        """Remove a estrutura legada após migração bem-sucedida."""
        if not self.dry_run:
            print(f"\n🧹 Removendo estrutura legada: {self.legacy_agents_path}")
            shutil.rmtree(self.legacy_agents_path)
            print("✅ Estrutura legada removida!")
    
    def validate_migration(self) -> bool:
        """Valida se a migração foi bem-sucedida."""
        print("\n🔍 Validando migração...")
        
        for agent_id in self.agent_configs.keys():
            new_path = self.get_new_agent_path(agent_id)
            
            if not self.dry_run and not new_path.exists():
                print(f"❌ Agente {agent_id} não encontrado em {new_path}")
                return False
            
            if not self.dry_run:
                agent_yaml = new_path / "agent.yaml"
                try:
                    with open(agent_yaml, 'r') as f:
                        data = yaml.safe_load(f)
                    
                    if data.get('version') != '2.0':
                        print(f"❌ {agent_id}: version não é 2.0")
                        return False
                    
                    if 'execution_mode' not in data:
                        print(f"❌ {agent_id}: execution_mode ausente")
                        return False
                        
                    # Valida target_context para agentes de projeto
                    config = self.agent_configs[agent_id]
                    if config['project_key'] and 'target_context' not in data:
                        print(f"❌ {agent_id}: target_context ausente")
                        return False
                    
                except Exception as e:
                    print(f"❌ Erro ao validar {agent_id}: {e}")
                    return False
            
            print(f"   ✅ {agent_id}")
        
        return True
    
    def run(self):
        """Executa a migração completa."""
        print("🚀 Iniciando Migração de Agentes v1.x → v2.0")
        print("=" * 50)
        
        if self.dry_run:
            print("🔍 MODO DRY-RUN: Nenhuma alteração será feita")
        
        # Lista agentes a serem migrados
        agents_to_migrate = [d for d in os.listdir(self.legacy_agents_path) 
                           if d in self.agent_configs]
        
        print(f"📋 Agentes a migrar: {len(agents_to_migrate)}")
        for agent in agents_to_migrate:
            print(f"   • {agent}")
        
        if not self.dry_run and not self.auto_confirm:
            response = input(f"\nProsseguir com a migração? (y/N): ")
            if response.lower() != 'y':
                print("Migração cancelada.")
                sys.exit(0)
        
        # Cria backup
        if not self.dry_run:
            self.create_backup()
        
        # Migra cada agente
        success_count = 0
        for agent_id in agents_to_migrate:
            if self.migrate_agent(agent_id):
                success_count += 1
        
        # Valida migração
        if self.validate_migration():
            print(f"\n✅ Migração bem-sucedida! {success_count}/{len(agents_to_migrate)} agentes migrados")
            
            if not self.dry_run:
                self.cleanup_legacy_structure()
            
            print("\n🎉 Arquitetura v2.0 implementada com sucesso!")
            print("🔗 Use: python scripts/genesis_agent.py --environment develop --project nex-web-backend --agent KotlinEntityCreator_Agent")
        else:
            print("\n❌ Validação falhou! Verifique os erros acima.")
            if not self.dry_run:
                print(f"💾 Backup disponível em: {self.backup_path}")
            sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Migra agentes v1.x para arquitetura v2.0")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Simula a migração sem fazer alterações")
    parser.add_argument("--yes", action="store_true",
                       help="Confirma automaticamente todas as perguntas")
    
    args = parser.parse_args()
    
    migrator = AgentMigrator(dry_run=args.dry_run, auto_confirm=args.yes)
    migrator.run()

if __name__ == "__main__":
    main()