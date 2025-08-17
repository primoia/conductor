#!/usr/bin/env python3
"""
Teste de Integração: test_dual_providers.py

Testa o sistema de provedores duais que usa Gemini para chat e Claude para geração.
"""

import unittest
import tempfile
import os
import yaml
import json
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.genesis_agent import GenesisAgent, load_ai_providers_config


class TestDualProviders(unittest.TestCase):
    """Teste de integração para sistema de provedores duais."""
    
    def setUp(self):
        """Configura ambiente de teste."""
        self.test_dir = tempfile.mkdtemp(prefix="conductor_dual_providers_test_")
        self.addCleanup(self._cleanup_test_dir)
        
        # Estrutura de diretórios
        self.mock_conductor_root = Path(self.test_dir) / "conductor"
        self.mock_workspace = Path(self.test_dir) / "workspace"
        self.mock_project = self.mock_workspace / "test-service"
        
        # Cria estrutura completa
        self.mock_conductor_root.mkdir(parents=True)
        (self.mock_conductor_root / "config").mkdir()
        
        # Estrutura do agente sem ai_provider (para usar defaults)
        self.agent_home = (self.mock_conductor_root / "projects" / "develop" / 
                          "test-service" / "agents" / "DualProviderTestAgent")
        self.agent_home.mkdir(parents=True)
        
        # Estrutura do projeto alvo
        self.mock_project.mkdir(parents=True)
        (self.mock_project / "src" / "main" / "kotlin").mkdir(parents=True)
        
        # Cria workspaces.yaml
        workspaces_config = {
            'workspaces': {
                'develop': str(self.mock_workspace)
            }
        }
        workspaces_yaml = self.mock_conductor_root / "config" / "workspaces.yaml"
        with open(workspaces_yaml, 'w') as f:
            yaml.dump(workspaces_config, f)
        
        # Cria ai_providers.yaml
        ai_providers_config = {
            'default_providers': {
                'chat': 'gemini',
                'generation': 'claude'
            },
            'fallback_provider': 'claude'
        }
        ai_providers_yaml = self.mock_conductor_root / "config" / "ai_providers.yaml"
        with open(ai_providers_yaml, 'w') as f:
            yaml.dump(ai_providers_config, f)
        
        # Cria agent.yaml SEM ai_provider (para usar sistema dual)
        agent_config = {
            'id': 'DualProviderTestAgent',
            'version': '2.0',
            'description': 'Agente para testar sistema de provedores duais',
            'persona_prompt_path': 'persona.md',
            'state_file_path': 'state.json',
            'execution_mode': 'project_resident',
            'target_context': {
                'project_key': 'test-service',
                'output_scope': 'src/main/kotlin/*.kt'
            },
            'available_tools': ['read_file', 'write_file']
            # Nota: SEM ai_provider para testar defaults
        }
        
        agent_yaml = self.agent_home / "agent.yaml"
        with open(agent_yaml, 'w') as f:
            yaml.dump(agent_config, f)
        
        # Cria persona.md
        persona_md = self.agent_home / "persona.md"
        persona_md.write_text("# Dual Provider Test Agent\\nTesta sistema de provedores duais.")
        
        # Cria state.json inicial
        self.state_json_path = self.agent_home / "state.json"
        initial_state = {
            'conversation_history': [],
            'last_modified': '2025-01-01T00:00:00'
        }
        with open(self.state_json_path, 'w') as f:
            json.dump(initial_state, f)
        
        # Salva CWD original
        try:
            self.original_cwd = os.getcwd()
        except FileNotFoundError:
            # Se CWD atual foi removido, use um diretório seguro
            self.original_cwd = str(Path.home())
    
    def _cleanup_test_dir(self):
        """Limpa diretório de teste e restaura CWD."""
        import shutil
        try:
            os.chdir(self.original_cwd)
        except:
            pass
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _mock_workspaces_config(self):
        """Retorna configuração mock de workspaces."""
        return {'develop': str(self.mock_workspace)}
    
    def test_load_ai_providers_config(self):
        """Testa carregamento da configuração de provedores de IA."""
        
        with patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            config = load_ai_providers_config()
            
            self.assertIn('default_providers', config)
            self.assertEqual(config['default_providers']['chat'], 'gemini')
            self.assertEqual(config['default_providers']['generation'], 'claude')
            self.assertEqual(config['fallback_provider'], 'claude')
    
    def test_dual_provider_resolution(self):
        """Testa resolução de provedores para diferentes tipos de tarefa."""
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            # Inicializa agente sem ai_provider específico
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider=None  # Não especifica provider
            )
            
            # Embody agente
            success = agent.embody_agent_v2("DualProviderTestAgent")
            self.assertTrue(success, "Falha ao embodar agente")
            
            # Testa resolução de provedores
            chat_provider = agent.get_chat_provider()
            generation_provider = agent.get_generation_provider()
            
            # Verifica se está usando a configuração dual correta
            self.assertEqual(chat_provider, 'gemini', "Chat provider deveria ser Gemini")
            self.assertEqual(generation_provider, 'claude', "Generation provider deveria ser Claude")
            
            print(f"✅ Chat provider: {chat_provider}")
            print(f"✅ Generation provider: {generation_provider}")
    
    def test_agent_specific_override(self):
        """Testa que agente com ai_provider específico sobrescreve defaults."""
        
        # Cria agente com override específico
        override_agent_home = (self.mock_conductor_root / "projects" / "develop" / 
                              "test-service" / "agents" / "OverrideTestAgent")
        override_agent_home.mkdir(parents=True)
        
        # Agent config COM ai_provider específico
        agent_config_override = {
            'id': 'OverrideTestAgent',
            'version': '2.0',
            'description': 'Agente com override específico',
            'ai_provider': 'claude',  # Override específico
            'persona_prompt_path': 'persona.md',
            'state_file_path': 'state.json',
            'execution_mode': 'project_resident',
            'target_context': {
                'project_key': 'test-service',
                'output_scope': 'src/main/kotlin/*.kt'
            },
            'available_tools': ['read_file', 'write_file']
        }
        
        agent_yaml_override = override_agent_home / "agent.yaml"
        with open(agent_yaml_override, 'w') as f:
            yaml.dump(agent_config_override, f)
        
        # Cria arquivos obrigatórios
        (override_agent_home / "persona.md").write_text("# Override Test Agent")
        (override_agent_home / "state.json").write_text('{}')
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider=None
            )
            
            success = agent.embody_agent_v2("OverrideTestAgent")
            self.assertTrue(success, "Falha ao embodar agente com override")
            
            # Verifica se override funciona
            chat_provider = agent.get_chat_provider()
            generation_provider = agent.get_generation_provider()
            
            # Ambos deveriam ser Claude devido ao override
            self.assertEqual(chat_provider, 'claude', "Override deveria usar Claude para chat")
            self.assertEqual(generation_provider, 'claude', "Override deveria usar Claude para generation")
            
            print(f"✅ Override - Chat provider: {chat_provider}")
            print(f"✅ Override - Generation provider: {generation_provider}")
    
    def test_cli_override_priority(self):
        """Testa que override via CLI tem a maior prioridade."""
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            # Agente com CLI override (maior prioridade)
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="gemini"  # CLI override
            )
            
            success = agent.embody_agent_v2("DualProviderTestAgent")
            self.assertTrue(success, "Falha ao embodar agente com CLI override")
            
            # CLI override deveria ter precedência
            chat_provider = agent.get_chat_provider()
            generation_provider = agent.get_generation_provider()
            
            # Ambos deveriam ser Gemini devido ao CLI override
            self.assertEqual(chat_provider, 'gemini', "CLI override deveria usar Gemini para chat")
            self.assertEqual(generation_provider, 'gemini', "CLI override deveria usar Gemini para generation")
            
            print(f"✅ CLI Override - Chat provider: {chat_provider}")
            print(f"✅ CLI Override - Generation provider: {generation_provider}")
    
    def test_fallback_provider(self):
        """Testa fallback quando configuração está incompleta."""
        
        # Cria config com providers faltando
        incomplete_config = {
            'default_providers': {
                'chat': 'gemini'
                # 'generation' faltando
            },
            'fallback_provider': 'claude'
        }
        
        ai_providers_yaml = self.mock_conductor_root / "config" / "ai_providers.yaml"
        with open(ai_providers_yaml, 'w') as f:
            yaml.dump(incomplete_config, f)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider=None
            )
            
            success = agent.embody_agent_v2("DualProviderTestAgent")
            self.assertTrue(success, "Falha ao embodar agente")
            
            chat_provider = agent.get_chat_provider()
            generation_provider = agent.get_generation_provider()
            
            # Chat deveria usar Gemini, generation deveria usar fallback (Claude)
            self.assertEqual(chat_provider, 'gemini', "Chat provider encontrado")
            self.assertEqual(generation_provider, 'claude', "Generation deveria usar fallback")
            
            print(f"✅ Fallback - Chat provider: {chat_provider}")
            print(f"✅ Fallback - Generation provider: {generation_provider}")


if __name__ == '__main__':
    # Configura logging
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executa testes
    unittest.main(verbosity=2)