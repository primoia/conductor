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
        # Create temporary test directory structure
        self.test_dir = tempfile.mkdtemp()
        self.projects_dir = os.path.join(self.test_dir, "projects", "develop", "agents")
        self.agent_dir = os.path.join(self.projects_dir, "TestAgent")
        
        os.makedirs(self.agent_dir, exist_ok=True)
        
        # Create test agent configuration
        self.agent_yaml = {
            "id": "TestAgent",
            "version": "1.0",
            "description": "Test agent for placeholder resolution",
            "ai_provider": "claude",
            "persona_prompt_path": "persona.md",
            "state_file_path": "state.json",
            "available_tools": ["read_file", "write_file"]
        }
        
        # Write agent.yaml
        with open(os.path.join(self.agent_dir, "agent.yaml"), 'w') as f:
            import yaml
            yaml.dump(self.agent_yaml, f)
            
        # Write initial state.json
        self.initial_state = {
            "version": "1.0",
            "agent_id": "TestAgent",
            "status": "IDLE",
            "conversation_history": [],
            "last_updated": "2025-08-16T10:00:00Z"
        }
        
        with open(os.path.join(self.agent_dir, "state.json"), 'w') as f:
            json.dump(self.initial_state, f, indent=2)
            
    def tearDown(self):
        """Clean up test environment."""
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
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("TestAgent")
            
        # THEN: Agent should successfully embody
        self.assertTrue(success, "Agent should successfully embody")
        
        # AND: "Contexto" should be replaced with "TestAgent"
        self.assertIn("TestAgent", mock_client.agent_persona, "Should replace 'Contexto' with 'TestAgent'")
        self.assertNotIn("Contexto", mock_client.agent_persona, "Should not contain 'Contexto' placeholder")
        
        # AND: Multiple instances should be replaced
        testag_count = mock_client.agent_persona.count("TestAgent")
        self.assertGreaterEqual(testag_count, 3, "Should replace all instances of 'Contexto'")
        
    def test_agent_id_placeholder_resolution(self):
        """Test: {{agent_id}} placeholder is replaced with actual agent ID."""
        # GIVEN: Persona with {{agent_id}} placeholder
        persona_content = """# Persona: {{agent_id}}

You are {{agent_id}}, a specialized agent.

Your name is {{agent_id}}."""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("TestAgent")
            
        # THEN: {{agent_id}} should be replaced with "TestAgent"
        self.assertTrue(success, "Agent should successfully embody")
        self.assertIn("TestAgent", mock_client.agent_persona, "Should replace {{agent_id}} with 'TestAgent'")
        self.assertNotIn("{{agent_id}}", mock_client.agent_persona, "Should not contain {{agent_id}} placeholder")
        
    def test_agent_description_placeholder_resolution(self):
        """Test: {{agent_description}} placeholder is replaced with config description."""
        # GIVEN: Persona with {{agent_description}} placeholder
        persona_content = """# Persona: Test Agent

Your purpose: {{agent_description}}

You specialize in: {{agent_description}}"""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(persona_content)
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("TestAgent")
            
        # THEN: {{agent_description}} should be replaced with actual description
        self.assertTrue(success, "Agent should successfully embody")
        self.assertIn("Test agent for placeholder resolution", mock_client.agent_persona, 
                     "Should replace {{agent_description}} with config description")
        self.assertNotIn("{{agent_description}}", mock_client.agent_persona, 
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
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("TestAgent")
            
        # THEN: All placeholders should be resolved
        self.assertTrue(success, "Agent should successfully embody")
        
        resolved_persona = mock_client.agent_persona
        
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
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("TestAgent")
            
        # THEN: Persona should remain unchanged
        self.assertTrue(success, "Agent should successfully embody")
        self.assertEqual(persona_content, mock_client.agent_persona, 
                        "Persona without placeholders should remain unchanged")
        
    def test_problemrefiner_agent_specific_case(self):
        """Test: Specific fix for ProblemRefiner_Agent 'Contexto' issue."""
        # GIVEN: ProblemRefiner_Agent configuration
        problemrefiner_dir = os.path.join(self.projects_dir, "ProblemRefiner_Agent")
        os.makedirs(problemrefiner_dir, exist_ok=True)
        
        # Create ProblemRefiner_Agent config
        problemrefiner_yaml = {
            "id": "ProblemRefiner_Agent",
            "version": "1.0", 
            "description": "Refina uma declaração de problema inicial através de um diálogo interativo",
            "ai_provider": "claude",
            "persona_prompt_path": "persona.md",
            "state_file_path": "state.json"
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
            json.dump({"version": "1.0", "agent_id": "ProblemRefiner_Agent", "conversation_history": []}, f)
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: ProblemRefiner_Agent is embodied
            success = agent.embody_agent("ProblemRefiner_Agent")
            
        # THEN: "Contexto" should be replaced with "ProblemRefiner_Agent"
        self.assertTrue(success, "ProblemRefiner_Agent should successfully embody")
        self.assertIn("ProblemRefiner_Agent", mock_client.agent_persona, 
                     "Should replace 'Contexto' with 'ProblemRefiner_Agent'")
        self.assertNotIn("Contexto", mock_client.agent_persona, 
                        "Should not contain 'Contexto' placeholder in resolved persona")


if __name__ == '__main__':
    unittest.main(verbosity=2)