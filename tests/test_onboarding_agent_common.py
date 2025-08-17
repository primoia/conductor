#!/usr/bin/env python3
"""
Test Suite: OnboardingGuide_Agent as Meta-Agent
Tests the OnboardingGuide_Agent functioning as a meta-agent in projects/_common/agents/

Author: Global Engineering Team  
Date: 2025-08-17
"""

import unittest
import tempfile
import os
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.agent_common import resolve_agent_paths
from scripts.admin import AdminAgent


class TestOnboardingAgentAsMetaAgent(unittest.TestCase):
    """Tests for OnboardingGuide_Agent as meta-agent."""
    
    def setUp(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="conductor_onboarding_test_")
        self.addCleanup(self._cleanup_test_dir)
        
        # Mock conductor root structure
        self.mock_conductor_root = Path(self.test_dir) / "conductor"
        self.mock_conductor_root.mkdir(parents=True)
        
        # Create _common/agents structure with OnboardingGuide_Agent
        self.onboarding_agent_dir = (self.mock_conductor_root / "projects" / "_common" / 
                                    "agents" / "OnboardingGuide_Agent")
        self.onboarding_agent_dir.mkdir(parents=True)
        
        # Create mock agent.yaml for OnboardingGuide_Agent
        agent_config = {
            'id': 'OnboardingGuide_Agent',
            'version': '2.0',
            'execution_mode': 'project_resident',
            'ai_provider': 'claude',
            'description': 'Conductor Guide - Mentor especialista em guiar novos usuários',
            'available_tools': [
                'collect_user_profile',
                'collect_project_context', 
                'suggest_team_template',
                'apply_team_template',
                'create_example_project'
            ]
        }
        
        agent_yaml_path = self.onboarding_agent_dir / "agent.yaml"
        with open(agent_yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(agent_config, f)
        
        # Create mock persona.md
        persona_path = self.onboarding_agent_dir / "persona.md"
        with open(persona_path, 'w', encoding='utf-8') as f:
            f.write("# OnboardingGuide_Agent\nMentor especialista em onboarding")
        
        # Create mock state.json
        state_path = self.onboarding_agent_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            f.write('{"conversation_history": []}')
    
    def _cleanup_test_dir(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_onboarding_agent_is_meta_agent(self):
        """Test that OnboardingGuide_Agent is recognized as meta-agent."""
        # Change to mock conductor root
        original_cwd = os.getcwd()
        try:
            os.chdir(self.mock_conductor_root)
            
            # Test resolve_agent_paths recognizes it as meta-agent
            agent_home, project_root = resolve_agent_paths(
                environment="develop", 
                project="any-project",
                agent_id="OnboardingGuide_Agent"
            )
            
            # Should resolve to _common location
            expected_agent_home = self.mock_conductor_root / "projects" / "_common" / "agents" / "OnboardingGuide_Agent"
            self.assertEqual(agent_home, expected_agent_home)
            
            # Meta-agents use current directory as project root
            self.assertEqual(project_root, self.mock_conductor_root)
            
        finally:
            os.chdir(original_cwd)
    
    def test_onboarding_agent_config_has_no_target_context(self):
        """Test that OnboardingGuide_Agent has no target_context (meta-agent requirement)."""
        agent_yaml_path = self.onboarding_agent_dir / "agent.yaml"
        
        with open(agent_yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Meta-agents should not have target_context
        self.assertNotIn('target_context', config, 
                        "Meta-agents should not have target_context")
    
    def test_admin_agent_can_load_onboarding_agent(self):
        """Test that AdminAgent can load OnboardingGuide_Agent."""
        original_cwd = os.getcwd()
        try:
            os.chdir(self.mock_conductor_root)
            
            # Create AI providers config mock
            config_dir = self.mock_conductor_root / "config"
            config_dir.mkdir(exist_ok=True)
            
            ai_providers_config = {
                'ai_providers': {
                    'claude': {'claude_cli_path': 'claude'},
                    'gemini': {'gemini_cli_path': 'gemini'}
                }
            }
            
            with open(config_dir / "ai_providers.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(ai_providers_config, f)
            
            # Test AdminAgent initialization
            admin_agent = AdminAgent(agent_id="OnboardingGuide_Agent")
            
            # Should successfully find the agent
            self.assertTrue(admin_agent.agent_home_path.exists())
            self.assertEqual(admin_agent.agent_home_path.name, "OnboardingGuide_Agent")
            
        finally:
            os.chdir(original_cwd)


class TestMetaAgentResolutionGeneral(unittest.TestCase):
    """General tests for meta-agent resolution logic."""
    
    def test_meta_agent_vs_project_agent_precedence(self):
        """Test that meta-agents in _common take precedence over project agents."""
        test_dir = tempfile.mkdtemp(prefix="conductor_precedence_test_")
        self.addCleanup(lambda: __import__('shutil').rmtree(test_dir, ignore_errors=True))
        
        mock_root = Path(test_dir) / "conductor"
        mock_root.mkdir(parents=True)
        
        # Create same-named agent in both locations
        agent_name = "TestPrecedenceAgent"
        
        # 1. Create project agent
        project_agent_dir = (mock_root / "projects" / "develop" / "test-project" / 
                            "agents" / agent_name)
        project_agent_dir.mkdir(parents=True)
        
        # 2. Create meta-agent (should take precedence)
        meta_agent_dir = (mock_root / "projects" / "_common" / "agents" / agent_name)
        meta_agent_dir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(mock_root)
            
            agent_home, project_root = resolve_agent_paths(
                environment="develop",
                project="test-project", 
                agent_id=agent_name
            )
            
            # Should resolve to meta-agent location, not project agent
            self.assertEqual(agent_home, meta_agent_dir.resolve())
            self.assertEqual(project_root, mock_root)
            
        finally:
            os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main()