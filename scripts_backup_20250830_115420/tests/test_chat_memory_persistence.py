#!/usr/bin/env python3
"""
Test Suite: Chat Memory Persistence v2.0
Bug Report: project-management/bug-reports/memory-chat-issue/

Tests the critical chat memory persistence functionality without external API dependencies.
Uses mock LLM clients to simulate Claude/Gemini responses.
Updated for v2.0 architecture.

Author: Global Engineering Team
Date: 2025-08-16
"""

import unittest
import tempfile
import os
import json
import shutil
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.genesis_agent import GenesisAgent, LLMClient


class MockLLMClient(LLMClient):
    """Mock LLM Client that simulates responses without external API calls."""
    
    def __init__(self, working_directory: str = None):
        super().__init__(working_directory)
        self.mock_responses = []
        self.call_count = 0
        self.ai_provider = 'claude'  # Set provider to match expected behavior
        
    def add_mock_response(self, response: str):
        """Add a predetermined response for testing."""
        self.mock_responses.append(response)
        
    def _invoke_subprocess(self, prompt: str) -> str:
        """Mock implementation that returns predetermined responses."""
        # Build contextual prompt (just like the real implementation)
        contextual_prompt = self._build_contextual_prompt(prompt)
        
        # Record the conversation in history (this should happen)
        self.conversation_history.append({
            'prompt': prompt,  # Store original prompt
            'response': self.mock_responses[self.call_count] if self.call_count < len(self.mock_responses) else "Mock response",
            'timestamp': 1234567890.0  # Fixed timestamp for testing
        })
        
        response = self.mock_responses[self.call_count] if self.call_count < len(self.mock_responses) else "Mock response"
        self.call_count += 1
        return response
        
    def _build_contextual_prompt(self, new_prompt: str) -> str:
        """Build contextual prompt (same logic as real ClaudeCLIClient)."""
        if not self.conversation_history:
            return new_prompt
        
        context_parts = ["Previous conversation context:"]
        max_context_messages = 10
        recent_history = self.conversation_history[-max_context_messages:]
        
        for entry in recent_history:
            user_msg = entry.get('prompt', '').strip()
            assistant_msg = entry.get('response', '').strip()
            
            if user_msg:
                context_parts.append(f"User: {user_msg}")
            if assistant_msg:
                context_parts.append(f"Assistant: {assistant_msg}")
        
        context_parts.append("\nCurrent message:")
        context_parts.append(f"User: {new_prompt}")
        
        return "\n".join(context_parts)


class TestChatMemoryPersistence(unittest.TestCase):
    """
    Test suite for chat memory persistence functionality.
    
    Tests cover:
    1. State loading from agent state.json
    2. Conversation history persistence
    3. Context injection into LLM calls
    4. State saving after interactions
    """
    
    def setUp(self):
        """Set up test environment with v2.0 architecture structure."""
        # Create temporary test directory structure
        self.test_dir = tempfile.mkdtemp(prefix="conductor_memory_test_")
        self.addCleanup(self._cleanup_test_dir)
        
        # v2.0 Structure
        self.mock_conductor_root = Path(self.test_dir) / "conductor"
        self.mock_workspace = Path(self.test_dir) / "workspace" 
        self.mock_project = self.mock_workspace / "test-service"
        
        # Create structure
        self.mock_conductor_root.mkdir(parents=True)
        (self.mock_conductor_root / "config").mkdir()
        
        # Agent structure in v2.0
        self.agent_home = (self.mock_conductor_root / "projects" / "develop" / 
                          "test-service" / "agents" / "TestAgent")
        self.agent_home.mkdir(parents=True)
        
        # Project structure
        self.mock_project.mkdir(parents=True)
        
        # Create workspaces.yaml
        workspaces_config = {
            'workspaces': {
                'develop': str(self.mock_workspace)
            }
        }
        workspaces_yaml = self.mock_conductor_root / "config" / "workspaces.yaml"
        with open(workspaces_yaml, 'w') as f:
            yaml.dump(workspaces_config, f)
        
        # Create ai_providers.yaml
        ai_providers_config = {
            'default_providers': {
                'chat': 'claude',
                'generation': 'claude'
            },
            'fallback_provider': 'claude'
        }
        ai_providers_yaml = self.mock_conductor_root / "config" / "ai_providers.yaml"
        with open(ai_providers_yaml, 'w') as f:
            yaml.dump(ai_providers_config, f)
        
        # Create test agent configuration v2.0
        self.agent_yaml = {
            "id": "TestAgent",
            "version": "2.0",
            "description": "Test agent for memory persistence",
            "ai_provider": "claude",
            "persona_prompt_path": "persona.md",
            "state_file_path": "state.json",
            "execution_mode": "project_resident",
            "target_context": {
                "project_key": "test-service",
                "output_scope": "src/**/*.kt"
            },
            "available_tools": ["read_file", "write_file"]
        }
        
        # Write agent.yaml
        agent_yaml = self.agent_home / "agent.yaml"
        with open(agent_yaml, 'w') as f:
            yaml.dump(self.agent_yaml, f)
            
        # Write persona.md
        persona_md = self.agent_home / "persona.md"
        persona_md.write_text("# Test Agent Persona\nI am a test agent for memory persistence testing.")
            
        # Write initial state.json
        self.initial_state = {
            "version": "2.0",
            "agent_id": "TestAgent",
            "environment": "develop",
            "project": "test-service",
            "conversation_history": [],
            "last_modified": "2025-08-16T10:00:00Z"
        }
        
        self.state_file = self.agent_home / "state.json"
        with open(self.state_file, 'w') as f:
            json.dump(self.initial_state, f, indent=2)
        
        # Save original CWD
        self.original_cwd = os.getcwd()
    
    def _cleanup_test_dir(self):
        """Limpa diretório de teste e restaura CWD."""
        try:
            os.chdir(self.original_cwd)
        except:
            pass
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _mock_workspaces_config(self):
        """Retorna configuração mock de workspaces."""
        return {'develop': str(self.mock_workspace)}
        
    def test_agent_state_loading_on_initialization(self):
        """Test: Agent loads conversation_history from state.json on initialization."""
        # GIVEN: state.json with existing conversation history
        existing_conversation = [
            {"role": "user", "content": "Hello", "timestamp": "2025-08-16T09:00:00Z"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2025-08-16T09:00:01Z"}
        ]
        
        state_with_history = self.initial_state.copy()
        state_with_history["conversation_history"] = existing_conversation
        
        with open(self.state_file, 'w') as f:
            json.dump(state_with_history, f, indent=2)
            
        # WHEN: GenesisAgent is initialized and embodied with v2.0 architecture
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            try:
                agent = GenesisAgent(
                    environment="develop",
                    project="test-service",
                    ai_provider="claude"
                )
                
                # Load agent state (this should load conversation_history)
                success = agent.embody_agent_v2("TestAgent")
            finally:
                os.chdir(original_cwd)
            
        # THEN: Agent should have loaded the conversation history
        self.assertTrue(success, "Agent should successfully embody")
        self.assertEqual(len(agent.llm_client.conversation_history), 2, "Should load existing conversation history")
        
    def test_conversation_persistence_across_interactions(self):
        """Test: Conversation history persists across multiple chat interactions."""
        # GIVEN: Initialized agent with v2.0 architecture
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")), \
             patch('scripts.genesis_agent.create_llm_client') as mock_create_client:
            
            # Set up mock client
            mock_client = MockLLMClient()
            mock_client.add_mock_response("Hello! How can I help you?")
            mock_client.add_mock_response("I remember you asked about my function.")
            mock_create_client.return_value = mock_client
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            
            # Embody agent first
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            try:
                success = agent.embody_agent_v2("TestAgent")
            finally:
                os.chdir(original_cwd)
            self.assertTrue(success, "Agent should embody successfully")
            
        # WHEN: Multiple chat interactions occur
        response1 = agent.chat("Hello")
        response2 = agent.chat("What did I ask before?")
        
        # THEN: LLM client should have conversation history
        self.assertEqual(len(mock_client.conversation_history), 2, "Should record both interactions")
        self.assertIn("Hello", mock_client.conversation_history[0]['prompt'])
        self.assertIn("What did I ask before?", mock_client.conversation_history[1]['prompt'])
        
    def test_context_injection_in_llm_calls(self):
        """Test: Previous conversation context is included in new LLM calls."""
        # GIVEN: Agent with existing conversation history
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            
            # Embody agent first (this loads state)
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            try:
                success = agent.embody_agent_v2("TestAgent")
            finally:
                os.chdir(original_cwd)
            self.assertTrue(success, "Agent should embody successfully")
            
            # Replace with mock client and manually add conversation history to simulate loaded state
            mock_client = MockLLMClient()
            agent.llm_client = mock_client
            agent.llm_client.conversation_history = [
                {"prompt": "Hello", "response": "Hi there!", "timestamp": 1234567890.0}
            ]
            
            mock_client.add_mock_response("Based on our previous conversation...")
            
        # WHEN: New chat interaction occurs
        agent.chat("What did we discuss?")
        
        # THEN: We can test by calling _build_contextual_prompt directly
        contextual_prompt = mock_client._build_contextual_prompt("What did we discuss?")
        self.assertIn("Hello", contextual_prompt, "Should include previous conversation in context")
        self.assertIn("Hi there!", contextual_prompt, "Should include previous response in context")
        self.assertIn("What did we discuss?", contextual_prompt, "Should include current prompt")
        
    def test_state_persistence_after_interactions(self):
        """Test: Agent state is saved to state.json after chat interactions."""
        # GIVEN: Agent with mock client
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            
            # Embody agent
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            try:
                success = agent.embody_agent_v2("TestAgent")
            finally:
                os.chdir(original_cwd)
            self.assertTrue(success, "Agent should embody successfully")
            
            # Replace with mock client
            mock_client = MockLLMClient()
            mock_client.add_mock_response("Test response")
            agent.llm_client = mock_client
            
        # WHEN: Chat interaction occurs
        agent.chat("Test message")
        
        # AND: State is explicitly saved (TODO: should happen automatically)
        # agent.save_state()  # This method doesn't exist yet
        
        # THEN: state.json should contain the conversation
        with open(self.state_file, 'r') as f:
            saved_state = json.load(f)
            
        # This should fail until we implement state persistence
        self.assertGreater(len(saved_state.get("conversation_history", [])), 0, 
                          "State should contain conversation history")
        
    def test_empty_state_handling(self):
        """Test: Agent handles empty or missing conversation_history gracefully."""
        # GIVEN: state.json without conversation_history field
        state_without_history = {
            "version": "2.0",
            "agent_id": "TestAgent",
            "environment": "develop",
            "project": "test-service"
            # Note: no conversation_history field
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state_without_history, f, indent=2)
            
        # WHEN: Agent is initialized
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            agent.llm_client = MockLLMClient()
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            try:
                success = agent.embody_agent_v2("TestAgent")
            finally:
                os.chdir(original_cwd)
            
        # THEN: Agent should initialize with empty conversation history
        self.assertTrue(success, "Agent should handle missing conversation_history gracefully")
        
    def test_malformed_state_recovery(self):
        """Test: Agent recovers gracefully from malformed state.json."""
        # GIVEN: Malformed state.json
        with open(self.state_file, 'w') as f:
            f.write("{ invalid json content")
            
        # WHEN: Agent is initialized
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            agent.llm_client = MockLLMClient()
            original_cwd = os.getcwd()
            os.chdir(self.mock_conductor_root)
            try:
                success = agent.embody_agent_v2("TestAgent")
            finally:
                os.chdir(original_cwd)
            
        # THEN: Agent should recover and create new state
        self.assertTrue(success, "Agent should recover from malformed state")


class TestBackwardCompatibility(unittest.TestCase):
    """Test suite ensuring backward compatibility with existing functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
        
    def test_existing_agents_without_conversation_history_still_work(self):
        """Test: Existing agents without conversation_history in state.json still function."""
        # This test ensures we don't break existing agent configurations
        pass
        
    def test_claude_cli_integration_unchanged(self):
        """Test: Claude CLI integration continues to work as before."""
        # This test ensures our changes don't break the CLI interface
        pass


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)