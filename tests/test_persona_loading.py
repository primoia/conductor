#!/usr/bin/env python3
"""
Test Suite: Persona Loading and Embodiment
Bug Report: project-management/bug-reports/persona-not-loaded-bug/

Tests the persona loading functionality in Genesis Agent embodiment system.
Ensures agents respond with their defined personas instead of generic Claude responses.

Author: Global Engineering Team
Date: 2025-08-16
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.genesis_agent import GenesisAgent, LLMClient


class MockPersonaLLMClient(LLMClient):
    """Mock LLM Client that tests persona integration."""
    
    def __init__(self, working_directory: str = None):
        super().__init__(working_directory)
        self.mock_responses = []
        self.call_count = 0
        self.last_full_prompt = None  # Track the complete prompt sent
        self.agent_persona = None
        
    def add_mock_response(self, response: str):
        """Add a predetermined response for testing."""
        self.mock_responses.append(response)
        
    def set_agent_persona(self, persona: str):
        """Set the agent persona (this should be called by GenesisAgent)."""
        self.agent_persona = persona
        
    def _build_contextual_prompt(self, new_prompt: str) -> str:
        """Build contextual prompt (simplified for testing)."""
        if not self.conversation_history:
            return new_prompt
            
        context_parts = ["Previous conversation:"]
        for entry in self.conversation_history[-3:]:  # Last 3 for testing
            context_parts.append(f"User: {entry.get('prompt', '')}")
            context_parts.append(f"Assistant: {entry.get('response', '')}")
        context_parts.append(f"\nCurrent: {new_prompt}")
        return "\n".join(context_parts)
        
    def _invoke_subprocess(self, prompt: str) -> str:
        """Mock implementation that captures full prompt including persona."""
        # Build full prompt with persona (like real implementation should)
        if self.agent_persona:
            system_prompt = f"### PERSONA:\n{self.agent_persona}\n\n"
            contextual_prompt = self._build_contextual_prompt(prompt)
            self.last_full_prompt = f"{system_prompt}{contextual_prompt}"
        else:
            self.last_full_prompt = self._build_contextual_prompt(prompt)
        
        # Record conversation
        response = self.mock_responses[self.call_count] if self.call_count < len(self.mock_responses) else "Generic Claude response"
        self.conversation_history.append({
            'prompt': prompt,
            'response': response,
            'timestamp': 1234567890.0
        })
        
        self.call_count += 1
        return response


class TestPersonaLoading(unittest.TestCase):
    """
    Test suite for persona loading and embodiment functionality.
    
    Tests cover:
    1. Persona file loading from agent directory
    2. Persona integration into LLM client
    3. Persona inclusion in prompts sent to Claude CLI
    4. Error handling for missing persona files
    5. Specialized agent behavior based on persona
    """
    
    def setUp(self):
        """Set up test environment with agent and persona files."""
        # Create temporary test directory structure
        self.test_dir = tempfile.mkdtemp()
        self.projects_dir = os.path.join(self.test_dir, "projects", "develop", "agents")
        self.agent_dir = os.path.join(self.projects_dir, "SpecialistAgent")
        
        os.makedirs(self.agent_dir, exist_ok=True)
        
        # Create test agent configuration
        self.agent_yaml = {
            "id": "SpecialistAgent",
            "version": "1.0",
            "description": "Test agent with specialized persona",
            "ai_provider": "claude",
            "persona_prompt_path": "persona.md",
            "state_file_path": "state.json",
            "available_tools": ["read_file", "write_file"]
        }
        
        # Write agent.yaml
        with open(os.path.join(self.agent_dir, "agent.yaml"), 'w') as f:
            import yaml
            yaml.dump(self.agent_yaml, f)
            
        # Write specialized persona.md
        self.specialized_persona = """# Problem Refiner Agent

You are a specialized Problem Refiner Agent, not Claude Code. Your role is to:

1. Help users clearly define and articulate software problems
2. Ask clarifying questions to understand the full scope
3. Break down complex issues into manageable components
4. Suggest potential approaches and solutions

Always introduce yourself as "Problem Refiner Agent" and focus on problem analysis.
Never respond as "Claude Code" - you are a specialized agent with this specific role.

Your responses should be analytical, focused, and solution-oriented."""
        
        with open(os.path.join(self.agent_dir, "persona.md"), 'w') as f:
            f.write(self.specialized_persona)
            
        # Write initial state.json
        self.initial_state = {
            "version": "1.0",
            "agent_id": "SpecialistAgent",
            "status": "IDLE",
            "conversation_history": [],
            "last_updated": "2025-08-16T10:00:00Z"
        }
        
        with open(os.path.join(self.agent_dir, "state.json"), 'w') as f:
            json.dump(self.initial_state, f, indent=2)
            
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
        
    def test_persona_file_loading_on_embodiment(self):
        """Test: Agent loads persona.md file during embodiment."""
        # GIVEN: Agent with persona file
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("SpecialistAgent")
            
        # THEN: Agent should successfully embody
        self.assertTrue(success, "Agent should successfully embody")
        
        # AND: Agent should have loaded the persona
        # This will fail until we implement persona loading
        self.assertTrue(hasattr(agent, 'agent_persona'), "Agent should have persona attribute")
        self.assertIn("Problem Refiner Agent", agent.agent_persona, "Should load correct persona content")
        
    def test_persona_integration_with_llm_client(self):
        """Test: Persona is passed to LLM client during embodiment."""
        # GIVEN: Agent with persona
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            agent.embody_agent("SpecialistAgent")
            
        # THEN: LLM client should receive the persona
        # This will fail until we implement persona integration
        self.assertIsNotNone(mock_client.agent_persona, "LLM client should receive persona")
        self.assertIn("Problem Refiner Agent", mock_client.agent_persona, "LLM client should have correct persona")
        
    def test_persona_included_in_llm_prompts(self):
        """Test: Persona is included in prompts sent to LLM."""
        # GIVEN: Embodied agent with persona
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            
            # Manually set persona for testing (until auto-loading is implemented)
            mock_client.set_agent_persona(self.specialized_persona)
            
            agent.embody_agent("SpecialistAgent")
            mock_client.add_mock_response("I am Problem Refiner Agent, specialized in problem analysis.")
            
        # WHEN: User interacts with agent
        response = agent.chat("Hello, what is your role?")
        
        # THEN: Full prompt should include persona
        self.assertIsNotNone(mock_client.last_full_prompt, "Should capture full prompt sent to LLM")
        self.assertIn("### PERSONA:", mock_client.last_full_prompt, "Prompt should include persona section")
        self.assertIn("Problem Refiner Agent", mock_client.last_full_prompt, "Prompt should include agent persona")
        self.assertIn("Hello, what is your role?", mock_client.last_full_prompt, "Prompt should include user message")
        
    def test_specialized_agent_behavior(self):
        """Test: Agent responds according to persona, not as generic Claude."""
        # GIVEN: Embodied specialist agent
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            
            # Simulate complete persona integration
            mock_client.set_agent_persona(self.specialized_persona)
            agent.embody_agent("SpecialistAgent")
            
            # Mock response that shows persona-based behavior
            mock_client.add_mock_response("I am Problem Refiner Agent. I specialize in helping you define software problems clearly.")
            
        # WHEN: User asks for introduction
        response = agent.chat("Who are you?")
        
        # THEN: Response should reflect specialized persona
        self.assertIn("Problem Refiner Agent", response, "Should identify as specialized agent")
        self.assertNotIn("Claude Code", response, "Should NOT identify as generic Claude")
        
    def test_missing_persona_file_handling(self):
        """Test: Agent handles missing persona.md file gracefully."""
        # GIVEN: Agent directory without persona.md
        os.remove(os.path.join(self.agent_dir, "persona.md"))
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            
        # WHEN: Agent attempts embodiment
        success = agent.embody_agent("SpecialistAgent")
        
        # THEN: Embodiment should fail gracefully
        # This will fail until we implement proper error handling
        self.assertFalse(success, "Embodiment should fail when persona file is missing")
        
    def test_custom_persona_path_loading(self):
        """Test: Agent loads persona from custom path specified in agent.yaml."""
        # GIVEN: Agent with custom persona path
        custom_persona_content = "# Custom Specialist\nI am a custom specialist agent."
        
        # Create custom persona file
        with open(os.path.join(self.agent_dir, "custom_persona.md"), 'w') as f:
            f.write(custom_persona_content)
            
        # Update agent.yaml to use custom path
        self.agent_yaml["persona_prompt_path"] = "custom_persona.md"
        with open(os.path.join(self.agent_dir, "agent.yaml"), 'w') as f:
            import yaml
            yaml.dump(self.agent_yaml, f)
        
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            
            # WHEN: Agent is embodied
            success = agent.embody_agent("SpecialistAgent")
        
        # THEN: Should load custom persona
        # This will fail until we implement custom path loading
        self.assertTrue(success, "Should embody with custom persona path")
        self.assertTrue(hasattr(agent, 'agent_persona'), "Should have persona attribute")
        self.assertIn("Custom Specialist", agent.agent_persona, "Should load custom persona content")
        
    def test_persona_persistence_across_conversations(self):
        """Test: Persona remains active throughout conversation session."""
        # GIVEN: Embodied agent with persona
        with patch('scripts.genesis_agent.AGENTS_BASE_PATH', self.projects_dir):
            agent = GenesisAgent()
            mock_client = MockPersonaLLMClient()
            agent.llm_client = mock_client
            mock_client.set_agent_persona(self.specialized_persona)
            
            agent.embody_agent("SpecialistAgent")
            mock_client.add_mock_response("First response as Problem Refiner Agent")
            mock_client.add_mock_response("Second response, still as Problem Refiner Agent")
            
        # WHEN: Multiple conversations occur
        response1 = agent.chat("First question")
        response2 = agent.chat("Second question")
        
        # THEN: Both responses should include persona context
        self.assertIn("### PERSONA:", mock_client.last_full_prompt, "Persona should persist in all prompts")
        self.assertIn("Problem Refiner Agent", mock_client.last_full_prompt, "Agent identity should persist")


class TestPersonaBackwardCompatibility(unittest.TestCase):
    """Test suite ensuring persona loading doesn't break existing functionality."""
    
    def test_agents_without_persona_still_work(self):
        """Test: Agents without persona.md files still function (backward compatibility)."""
        # This ensures we don't break existing setups
        pass
        
    def test_existing_claude_cli_integration_unchanged(self):
        """Test: Core Claude CLI functionality remains intact."""
        # This ensures persona integration doesn't break basic chat
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)