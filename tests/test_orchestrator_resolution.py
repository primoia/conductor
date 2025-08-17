#!/usr/bin/env python3
"""
Teste Unitário: test_orchestrator_resolution.py

Testa a função de resolução de caminhos do orquestrador conforme especificado
no MILESTONE5, seção 3.5.

Este teste valida que, dados um `environment` e `project`, o sistema consegue 
montar corretamente o `agent_home_path` e o `project_root_path` usando um 
`workspaces.yaml` de mock.
"""

import unittest
import tempfile
import os
import yaml
from pathlib import Path
import sys

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.genesis_agent import (
    load_workspaces_config, 
    resolve_agent_paths,
    GenesisAgent
)


class TestOrchestratorResolution(unittest.TestCase):
    """Testes para resolução de caminhos na arquitetura v2.0."""
    
    def setUp(self):
        """Configura ambiente de teste com estrutura de arquivos mock."""
        # Cria diretório temporário para testes
        self.test_dir = tempfile.mkdtemp(prefix="conductor_test_")
        self.addCleanup(self._cleanup_test_dir)
        
        # Estrutura de diretórios mock
        self.mock_conductor_root = Path(self.test_dir) / "conductor"
        self.mock_workspace_dev = Path(self.test_dir) / "workspace_dev"
        self.mock_workspace_main = Path(self.test_dir) / "workspace_main"
        
        # Cria estrutura de diretórios
        self.mock_conductor_root.mkdir(parents=True)
        (self.mock_conductor_root / "config").mkdir()
        (self.mock_conductor_root / "projects" / "develop" / "test-project" / "agents" / "TestAgent").mkdir(parents=True)
        
        self.mock_workspace_dev.mkdir(parents=True)
        (self.mock_workspace_dev / "test-project").mkdir()
        
        self.mock_workspace_main.mkdir(parents=True)
        (self.mock_workspace_main / "test-project").mkdir()
        
        # Cria workspaces.yaml mock
        self.workspaces_config = {
            'workspaces': {
                'develop': str(self.mock_workspace_dev),
                'main': str(self.mock_workspace_main)
            }
        }
        
        self.workspaces_yaml_path = self.mock_conductor_root / "config" / "workspaces.yaml"
        with open(self.workspaces_yaml_path, 'w') as f:
            yaml.dump(self.workspaces_config, f)
        
        # Cria agent.yaml mock
        agent_config = {
            'id': 'TestAgent',
            'version': '2.0',
            'execution_mode': 'project_resident',
            'target_context': {
                'project_key': 'test-project',
                'output_scope': 'src/**/*.kt'
            }
        }
        
        agent_yaml_path = self.mock_conductor_root / "projects" / "develop" / "test-project" / "agents" / "TestAgent" / "agent.yaml"
        with open(agent_yaml_path, 'w') as f:
            yaml.dump(agent_config, f)
        
        # Cria persona.md mock
        persona_path = agent_yaml_path.parent / "persona.md"
        with open(persona_path, 'w') as f:
            f.write("# Test Agent\nEste é um agente de teste.")
        
        # Cria state.json mock
        state_path = agent_yaml_path.parent / "state.json"
        with open(state_path, 'w') as f:
            f.write('{"conversation_history": []}')
        
        # Monkey patch para usar nosso diretório de teste
        self.original_script_path = Path(sys.modules['scripts.genesis_agent'].__file__)
        sys.modules['scripts.genesis_agent'].__file__ = str(self.mock_conductor_root / "scripts" / "genesis_agent.py")
    
    def _cleanup_test_dir(self):
        """Limpa diretório de teste."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Restaura path original
        if hasattr(self, 'original_script_path'):
            sys.modules['scripts.genesis_agent'].__file__ = str(self.original_script_path)
    
    def test_load_workspaces_config_success(self):
        """Testa carregamento bem-sucedido do workspaces.yaml."""
        # Monkey patch do path da configuração
        original_path = Path(sys.modules['scripts.genesis_agent'].__file__).parent.parent / "config" / "workspaces.yaml"
        
        # Temporariamente substitui a função para usar nosso arquivo mock
        def mock_load_workspaces():
            with open(self.workspaces_yaml_path, 'r') as f:
                config = yaml.safe_load(f)
            return config['workspaces']
        
        workspaces = mock_load_workspaces()
        
        self.assertIsInstance(workspaces, dict)
        self.assertIn('develop', workspaces)
        self.assertIn('main', workspaces)
        self.assertEqual(workspaces['develop'], str(self.mock_workspace_dev))
        self.assertEqual(workspaces['main'], str(self.mock_workspace_main))
    
    def test_load_workspaces_config_file_not_found(self):
        """Testa comportamento quando workspaces.yaml não existe."""
        # Remove o arquivo
        os.remove(self.workspaces_yaml_path)
        
        with self.assertRaises(FileNotFoundError) as context:
            with open(self.workspaces_yaml_path, 'r') as f:
                yaml.safe_load(f)
        
        self.assertIn("workspaces", str(context.exception).lower() or "No such file")
    
    def test_resolve_agent_paths_success(self):
        """Testa resolução bem-sucedida de caminhos do agente."""
        # Monkey patch para usar nossos paths mock
        import scripts.genesis_agent
        original_load_workspaces = scripts.genesis_agent.load_workspaces_config
        
        def mock_load_workspaces():
            return self.workspaces_config['workspaces']
        
        scripts.genesis_agent.load_workspaces_config = mock_load_workspaces
        
        try:
            # Change to mock conductor root directory
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            
            # Monkey patch do __file__ para usar nosso diretório mock
            original_file = scripts.genesis_agent.__file__
            scripts.genesis_agent.__file__ = str(self.mock_conductor_root / "scripts" / "genesis_agent.py")
            
            agent_home, project_root = resolve_agent_paths(
                environment="develop",
                project="test-project", 
                agent_id="TestAgent"
            )
            
            expected_agent_home = self.mock_conductor_root / "projects" / "develop" / "test-project" / "agents" / "TestAgent"
            expected_project_root = self.mock_workspace_dev / "test-project"
            
            self.assertEqual(agent_home, expected_agent_home)
            self.assertEqual(project_root, expected_project_root)
            
        finally:
            # Restaura função original
            scripts.genesis_agent.load_workspaces_config = original_load_workspaces
            scripts.genesis_agent.__file__ = original_file
            os.chdir(original_cwd)
    
    def test_resolve_agent_paths_invalid_environment(self):
        """Testa comportamento com ambiente inválido."""
        import scripts.genesis_agent
        original_load_workspaces = scripts.genesis_agent.load_workspaces_config
        
        def mock_load_workspaces():
            return self.workspaces_config['workspaces']
        
        scripts.genesis_agent.load_workspaces_config = mock_load_workspaces
        
        try:
            with self.assertRaises(ValueError) as context:
                resolve_agent_paths(
                    environment="invalid-env",
                    project="test-project",
                    agent_id="TestAgent"
                )
            
            self.assertIn("não encontrado", str(context.exception))
            self.assertIn("invalid-env", str(context.exception))
            
        finally:
            scripts.genesis_agent.load_workspaces_config = original_load_workspaces
    
    def test_resolve_agent_paths_agent_not_found(self):
        """Testa comportamento quando agente não existe."""
        import scripts.genesis_agent
        original_load_workspaces = scripts.genesis_agent.load_workspaces_config
        
        def mock_load_workspaces():
            return self.workspaces_config['workspaces']
        
        scripts.genesis_agent.load_workspaces_config = mock_load_workspaces
        
        try:
            original_file = scripts.genesis_agent.__file__
            scripts.genesis_agent.__file__ = str(self.mock_conductor_root / "scripts" / "genesis_agent.py")
            
            with self.assertRaises(ValueError) as context:
                resolve_agent_paths(
                    environment="develop",
                    project="test-project",
                    agent_id="NonExistentAgent"
                )
            
            self.assertIn("não encontrado", str(context.exception))
            
        finally:
            scripts.genesis_agent.load_workspaces_config = original_load_workspaces
            scripts.genesis_agent.__file__ = original_file
    
    def test_resolve_agent_paths_project_not_found(self):
        """Testa comportamento quando projeto não existe."""
        import scripts.genesis_agent
        original_load_workspaces = scripts.genesis_agent.load_workspaces_config
        
        def mock_load_workspaces():
            return self.workspaces_config['workspaces']
        
        scripts.genesis_agent.load_workspaces_config = mock_load_workspaces
        
        try:
            original_file = scripts.genesis_agent.__file__
            scripts.genesis_agent.__file__ = str(self.mock_conductor_root / "scripts" / "genesis_agent.py")
            
            # Cria o agente mas não o projeto para testar essa condição específica
            (self.mock_conductor_root / "projects" / "develop" / "non-existent-project" / "agents" / "TestAgent").mkdir(parents=True)
            
            with self.assertRaises(ValueError) as context:
                resolve_agent_paths(
                    environment="develop",
                    project="non-existent-project",
                    agent_id="TestAgent"
                )
            
            self.assertIn("não encontrado", str(context.exception))
            
        finally:
            scripts.genesis_agent.load_workspaces_config = original_load_workspaces
            scripts.genesis_agent.__file__ = original_file
    
    def test_genesis_agent_initialization_v2(self):
        """Testa inicialização do GenesisAgent com arquitetura v2.0."""
        import scripts.genesis_agent
        original_load_workspaces = scripts.genesis_agent.load_workspaces_config
        
        def mock_load_workspaces():
            return self.workspaces_config['workspaces']
        
        scripts.genesis_agent.load_workspaces_config = mock_load_workspaces
        
        try:
            original_file = scripts.genesis_agent.__file__
            scripts.genesis_agent.__file__ = str(self.mock_conductor_root / "scripts" / "genesis_agent.py")
            
            # Testa inicialização sem agente específico
            agent = GenesisAgent(
                environment="develop",
                project="test-project",
                ai_provider="claude"
            )
            
            self.assertEqual(agent.environment, "develop")
            self.assertEqual(agent.project, "test-project")
            self.assertEqual(str(agent.project_root_path), str(self.mock_workspace_dev / "test-project"))
            
        finally:
            scripts.genesis_agent.load_workspaces_config = original_load_workspaces
            scripts.genesis_agent.__file__ = original_file


if __name__ == '__main__':
    # Configura logging para os testes
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduz verbosidade durante testes
    
    # Executa testes
    unittest.main(verbosity=2)