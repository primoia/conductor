#!/usr/bin/env python3
"""
Test Suite: Persona Placeholder Resolution
Bug Report: Persona Template Placeholder Bug

Tests the placeholder resolution functionality in Genesis Agent persona loading.
Ensures placeholders like "Contexto" are replaced with actual agent names.

Author: Global Engineering Team
Date: 2025-08-16
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Import the modules under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.genesis_agent import GenesisAgent, LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM Client for testing placeholder resolution."""
    
    def __init__(self, working_directory: str = None):
        super().__init__(working_directory)
        self.agent_persona = None
        self.mock_responses = []
        self.call_count = 0
        
    def set_agent_persona(self, persona: str):
        """Store the persona for testing."""
        self.agent_persona = persona
        
    def _invoke_subprocess(self, prompt: str) -> str:
        """Mock implementation for testing."""
        return "Mock response from agent"


class TestPersonaPlaceholderResolution(unittest.TestCase):
    """
    Test suite for persona placeholder resolution functionality.
    
    Tests cover:
    1. "Contexto" placeholder resolution to agent_id
    2. {{agent_id}} placeholder resolution  
    3. {{agent_description}} placeholder resolution
    4. Multiple placeholder resolution in same content
    5. No placeholders (backward compatibility)
    """
    
    def setUp(self):
        """Set up test environment with agent and persona files."""
        # Create temporary test directory structure for v2.0
        self.test_dir = tempfile.mkdtemp()
        
        # Save original CWD to restore later
        self.original_cwd = os.getcwd()
        
        # Workspace structure (where projects live)
        self.workspace_dir = os.path.join(self.test_dir, "workspace")
        self.project_workspace_dir = os.path.join(self.workspace_dir, "test-service")
        os.makedirs(self.project_workspace_dir, exist_ok=True)
        
        # Conductor structure (where agent definitions live)
        self.conductor_dir = os.path.join(self.test_dir, "conductor")
        self.projects_dir = os.path.join(self.conductor_dir, "projects", "develop", "test-service")
        self.agents_dir = os.path.join(self.projects_dir, "agents")
        self.agent_dir = os.path.join(self.agents_dir, "TestAgent")
        
        os.makedirs(self.agent_dir, exist_ok=True)
        
        # Create config directory in conductor
        self.config_dir = os.path.join(self.conductor_dir, "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Create test agent configuration with v2.0 schema
        self.agent_yaml = {
            "id": "TestAgent",
            "version": "2.0",
            "description": "Test agent for placeholder resolution",
            "ai_provider": "claude",
            "persona_prompt_path": "persona.md",
            "state_file_path": "state.json",
            "execution_mode": "project_resident",
            "available_tools": ["Read", "Write"],
            "target_context": {
                "project_key": "test-service",
                "output_scope": "workspace/analysis/*.md"
            }
        }
        
        # Write agent.yaml
        with open(os.path.join(self.agent_dir, "agent.yaml"), 'w') as f:
            import yaml
            yaml.dump(self.agent_yaml, f)
            
        # Write initial state.json
        self.initial_state = {
            "version": "2.0",
            "agent_id": "TestAgent",
            "status": "IDLE",
            "conversation_history": [],
            "last_updated": "2025-08-16T10:00:00Z"
        }
        
        with open(os.path.join(self.agent_dir, "state.json"), 'w') as f:
            json.dump(self.initial_state, f, indent=2)
            
        # Create workspaces config
        self.workspaces_config = {
            "workspaces": {
                "develop": self.workspace_dir
            }
        }
        
        with open(os.path.join(self.config_dir, "workspaces.yaml"), 'w') as f:
            import yaml
            yaml.dump(self.workspaces_config, f)
            
        # Create ai_providers config
        self.ai_providers_config = {
            "default_providers": {
                "chat": "claude",
                "generation": "claude"
            },
            "fallback_provider": "claude"
        }
        
        with open(os.path.join(self.config_dir, "ai_providers.yaml"), 'w') as f:
            import yaml
            yaml.dump(self.ai_providers_config, f)
            
    def tearDown(self):
        """Clean up test environment."""
        # Restore original CWD before deleting test directory
        try:
            os.chdir(self.original_cwd)
        except:
            # If original CWD was also deleted, use a safe directory
            os.chdir(str(Path.home()))
        
        shutil.rmtree(self.test_dir)
        
    def test_contexto_placeholder_resolution(self):
        """Test: 'Contexto' placeholder is replaced with agent_id."""
        # GIVEN: Persona with "Contexto" placeholder
        persona_content = """# Persona: Test Agent

Você é o **"Contexto"**, especializado em análise de sistemas.

Seu nome é **"Contexto"**.

Como Contexto, sua função é analisar problemas."""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self.workspaces_config["workspaces"]), \
             patch('scripts.genesis_agent.__file__', os.path.join(self.conductor_dir, 'scripts', 'genesis_agent.py')), \
             patch('os.getcwd', return_value=self.test_dir):
            
            agent = GenesisAgent(environment="develop", project="test-service", ai_provider="claude")
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent_v2("TestAgent")
            
        # THEN: Agent should successfully embody
        self.assertTrue(success, "Agent should successfully embody")
        
        # AND: "Contexto" should be replaced with "Test" (extracted from persona title)
        # Check both the agent's persona and the mock client's persona
        self.assertIsNotNone(agent.agent_persona, "Agent should have loaded persona")
        self.assertIn("Test", agent.agent_persona, "Should replace 'Contexto' with 'Test' in agent")
        self.assertNotIn("Contexto", agent.agent_persona, "Should not contain 'Contexto' placeholder in agent")
        
        # If mock client has persona set, check it too
        if mock_client.agent_persona is not None:
            self.assertIn("Test", mock_client.agent_persona, "Should replace 'Contexto' with 'Test' in client")
            self.assertNotIn("Contexto", mock_client.agent_persona, "Should not contain 'Contexto' placeholder in client")
        
        # AND: Multiple instances should be replaced (note: "Test Agent" -> "Test")
        test_count = agent.agent_persona.count("Test")
        self.assertGreaterEqual(test_count, 3, "Should replace all instances of 'Contexto'")
        
    def test_agent_id_placeholder_resolution(self):
        """Test: {{agent_id}} placeholder is replaced with actual agent ID."""
        # GIVEN: Persona with {{agent_id}} placeholder
        persona_content = """# Persona: {{agent_id}}

You are {{agent_id}}, a specialized agent.

Your name is {{agent_id}}."""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self.workspaces_config["workspaces"]), \
             patch('scripts.genesis_agent.__file__', os.path.join(self.conductor_dir, 'scripts', 'genesis_agent.py')), \
             patch('os.getcwd', return_value=self.test_dir):
            
            agent = GenesisAgent(environment="develop", project="test-service", ai_provider="claude")
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent_v2("TestAgent")
            
        # THEN: {{agent_id}} should be replaced with "TestAgent"
        self.assertTrue(success, "Agent should successfully embody")
        self.assertIsNotNone(agent.agent_persona, "Agent should have loaded persona")
        self.assertIn("TestAgent", agent.agent_persona, "Should replace {{agent_id}} with 'TestAgent'")
        self.assertNotIn("{{agent_id}}", agent.agent_persona, "Should not contain {{agent_id}} placeholder")
        
    def test_agent_description_placeholder_resolution(self):
        """Test: {{agent_description}} placeholder is replaced with config description."""
        # GIVEN: Persona with {{agent_description}} placeholder
        persona_content = """# Persona: Test Agent

Your purpose: {{agent_description}}

You specialize in: {{agent_description}}"""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self.workspaces_config["workspaces"]), \
             patch('scripts.genesis_agent.__file__', os.path.join(self.conductor_dir, 'scripts', 'genesis_agent.py')), \
             patch('os.getcwd', return_value=self.test_dir):
            
            agent = GenesisAgent(environment="develop", project="test-service", ai_provider="claude")
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent_v2("TestAgent")
            
        # THEN: {{agent_description}} should be replaced with actual description
        self.assertTrue(success, "Agent should successfully embody")
        self.assertIsNotNone(agent.agent_persona, "Agent should have loaded persona")
        self.assertIn("Test agent for placeholder resolution", agent.agent_persona, 
                     "Should replace {{agent_description}} with config description")
        self.assertNotIn("{{agent_description}}", agent.agent_persona, 
                        "Should not contain {{agent_description}} placeholder")
        
    def test_multiple_different_placeholders(self):
        """Test: Multiple different placeholders resolved in same content."""
        # GIVEN: Persona with multiple placeholder types
        persona_content = """# Persona: {{agent_id}}

You are Contexto, also known as {{agent_id}}.

Your purpose: {{agent_description}}

As Contexto, you work with {{agent_id}} capabilities."""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self.workspaces_config["workspaces"]), \
             patch('scripts.genesis_agent.__file__', os.path.join(self.conductor_dir, 'scripts', 'genesis_agent.py')), \
             patch('os.getcwd', return_value=self.test_dir):
            
            agent = GenesisAgent(environment="develop", project="test-service", ai_provider="claude")
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent_v2("TestAgent")
            
        # THEN: All placeholders should be resolved
        self.assertTrue(success, "Agent should successfully embody")
        
        self.assertIsNotNone(agent.agent_persona, "Agent should have loaded persona")
        resolved_persona = agent.agent_persona
        
        # Check all placeholders are replaced
        self.assertNotIn("Contexto", resolved_persona, "Should not contain 'Contexto'")
        self.assertNotIn("{{agent_id}}", resolved_persona, "Should not contain {{agent_id}}")
        self.assertNotIn("{{agent_description}}", resolved_persona, "Should not contain {{agent_description}}")
        
        # Check replacements are present
        self.assertIn("TestAgent", resolved_persona, "Should contain resolved agent_id")
        self.assertIn("Test agent for placeholder resolution", resolved_persona, "Should contain resolved description")
        
    def test_no_placeholders_backward_compatibility(self):
        """Test: Persona without placeholders works unchanged (backward compatibility)."""
        # GIVEN: Persona without any placeholders
        persona_content = """# Persona: Simple Agent

You are a simple agent with no placeholders.

Your role is to help users with their tasks."""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self.workspaces_config["workspaces"]), \
             patch('scripts.genesis_agent.__file__', os.path.join(self.conductor_dir, 'scripts', 'genesis_agent.py')), \
             patch('os.getcwd', return_value=self.test_dir):
            
            agent = GenesisAgent(environment="develop", project="test-service", ai_provider="claude")
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent_v2("TestAgent")
            
        # THEN: Persona should remain unchanged
        self.assertTrue(success, "Agent should successfully embody")
        self.assertIsNotNone(agent.agent_persona, "Agent should have loaded persona")
        self.assertEqual(persona_content, agent.agent_persona, 
                        "Persona without placeholders should remain unchanged")
        
    def test_problemrefiner_agent_specific_case(self):
        """Test: Specific fix for ProblemRefiner_Agent 'Contexto' issue."""
        # GIVEN: ProblemRefiner_Agent configuration
        problemrefiner_dir = os.path.join(self.agents_dir, "ProblemRefiner_Agent")
        os.makedirs(problemrefiner_dir, exist_ok=True)
        
        # Create ProblemRefiner_Agent config with v2.0 schema
        problemrefiner_yaml = {
            "id": "ProblemRefiner_Agent",
            "version": "2.0", 
            "description": "Refina uma declaração de problema inicial através de um diálogo interativo",
            "ai_provider": "claude",
            "persona_prompt_path": "persona.md",
            "state_file_path": "state.json",
            "execution_mode": "project_resident",
            "available_tools": ["Read", "Write"],
            "target_context": {
                "project_key": "test-service",
                "output_scope": "workspace/analysis/*.md"
            }
        }
        
        with open(os.path.join(problemrefiner_dir, "agent.yaml"), 'w') as f:
            import yaml
            yaml.dump(problemrefiner_yaml, f)
        
        # Create problematic persona (like the real one)
        persona_content = """# Persona: Agente Analisador de Problemas

## 1. Identidade e Papel

Você é um Arquiteto de Software Sênior e Analista de Sistemas especialista em diagnóstico de problemas. Seu nome é **"Contexto"**.

Seu único objetivo é colaborar com o desenvolvedor."""
        
        with open(os.path.join(problemrefiner_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
            
        # Create state file
        with open(os.path.join(problemrefiner_dir, "state.json"), 'w') as f:
            json.dump({"version": "2.0", "agent_id": "ProblemRefiner_Agent", "conversation_history": []}, f)
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self.workspaces_config["workspaces"]), \
             patch('scripts.genesis_agent.__file__', os.path.join(self.conductor_dir, 'scripts', 'genesis_agent.py')), \
             patch('os.getcwd', return_value=self.test_dir):
            
            agent = GenesisAgent(environment="develop", project="test-service", ai_provider="claude")
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: ProblemRefiner_Agent is embodied
            success = agent.embody_agent_v2("ProblemRefiner_Agent")
            
        # THEN: "Contexto" should be replaced with "Agente Analisador de Problemas" (from title)
        self.assertTrue(success, "ProblemRefiner_Agent should successfully embody")
        self.assertIsNotNone(agent.agent_persona, "Agent should have loaded persona")
        self.assertIn("Agente Analisador de Problemas", agent.agent_persona, 
                     "Should replace 'Contexto' with extracted title")
        self.assertNotIn("Contexto", agent.agent_persona, 
                        "Should not contain 'Contexto' placeholder in resolved persona")


if __name__ == '__main__':
    unittest.main(verbosity=2)