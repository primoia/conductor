#!/usr/bin/env python3
"""
Test Tool Permissions - SAGA-013 Implementation Tests

This module tests the tool permission system for both Claude and Gemini agents,
ensuring that agent.yaml configuration controls tool access properly.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.core.agent_logic import AgentLogic
from src.core.prompt_engine import PromptEngine
from src.infrastructure.llm.cli_client import ClaudeCLIClient, GeminiCLIClient
from src.infrastructure.persistence.state_repository import FileStateRepository


class TestToolPermissions(unittest.TestCase):
    """Test tool permission control system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_fixtures_path = Path(__file__).parent / "fixtures" / "test_agents"
        self.claude_agent_path = self.test_fixtures_path / "TestRestrictedAgent_Claude"
        self.gemini_agent_path = self.test_fixtures_path / "TestRestrictedAgent_Gemini"
        
        # Create temporary working directory
        self.temp_dir = tempfile.mkdtemp()
        self.working_directory = self.temp_dir
        
    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_claude_client_tool_permissions_configuration(self):
        """Test that Claude client correctly adds allowed tools from agent config."""
        # Create mock genesis agent with restricted tools
        mock_genesis_agent = Mock()
        mock_genesis_agent.get_available_tools.return_value = ["Read"]
        
        # Create Claude client (project agent - not admin)
        client = ClaudeCLIClient(
            working_directory=self.working_directory,
            timeout=30,
            is_admin_agent=False
        )
        client.genesis_agent = mock_genesis_agent
        
        # Mock subprocess to capture the command
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Test response"
            
            try:
                client.invoke("Test prompt")
            except Exception:
                pass  # We're only testing command construction
            
            # Verify the command includes allowed tools
            call_args = mock_run.call_args[0][0] if mock_run.called else []
            self.assertIn("--allowedTools", call_args)
            self.assertIn("Read", call_args)
    
    def test_gemini_client_project_agent_tool_permissions(self):
        """Test that Gemini client uses yolo mode for project agents (temporary solution)."""
        # Create mock genesis agent with restricted tools
        mock_genesis_agent = Mock()
        mock_genesis_agent.get_available_tools.return_value = ["Read"]
        
        # Create Gemini client (project agent - not admin)
        client = GeminiCLIClient(
            working_directory=self.working_directory,
            timeout=30,
            is_admin_agent=False
        )
        client.genesis_agent = mock_genesis_agent
        
        # Mock subprocess to capture the command
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Test response"
            
            try:
                client.invoke("Test prompt")
            except Exception:
                pass  # We're only testing command construction
            
            # Verify the command uses yolo mode (temporary solution)
            call_args = mock_run.call_args[0][0] if mock_run.called else []
            self.assertIn("--approval-mode", call_args)
            self.assertIn("yolo", call_args)
            # No longer testing for --allowed-tools as it doesn't exist
    
    def test_gemini_client_admin_agent_unrestricted_access(self):
        """Test that Gemini client uses yolo mode for admin agents."""
        # Create mock genesis agent 
        mock_genesis_agent = Mock()
        mock_genesis_agent.get_available_tools.return_value = ["Read", "Write", "Bash"]
        
        # Create Gemini client (admin agent)
        client = GeminiCLIClient(
            working_directory=self.working_directory,
            timeout=30,
            is_admin_agent=True
        )
        client.genesis_agent = mock_genesis_agent
        
        # Mock subprocess to capture the command
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Test response"
            
            try:
                client.invoke("Test prompt")
            except Exception:
                pass  # We're only testing command construction
            
            # Verify the command includes yolo mode (not tool configuration)
            call_args = mock_run.call_args[0][0] if mock_run.called else []
            self.assertIn("--approval-mode", call_args)
            self.assertIn("yolo", call_args)
    
    def test_prompt_engine_available_tools_loading(self):
        """Test that PromptEngine correctly loads available_tools from agent.yaml."""
        if not self.claude_agent_path.exists():
            self.skipTest(f"Test fixture not found: {self.claude_agent_path}")
        
        # Load agent configuration through PromptEngine
        prompt_engine = PromptEngine(self.claude_agent_path)
        prompt_engine.load_context()
        
        # Verify tools are loaded correctly
        available_tools = prompt_engine.get_available_tools()
        self.assertEqual(available_tools, ["Read"])
        self.assertNotIn("Write", available_tools)
        self.assertNotIn("Bash", available_tools)
    
    def test_agent_logic_tool_access(self):
        """Test that AgentLogic correctly exposes tools from PromptEngine."""
        if not self.claude_agent_path.exists():
            self.skipTest(f"Test fixture not found: {self.claude_agent_path}")
        
        # Create mocked dependencies
        mock_state_repo = Mock(spec=FileStateRepository)
        mock_state_repo.load_state.return_value = {
            "conversation_history": [],
            "last_modified": "2025-09-02T00:00:00",
            "agent_id": "TestRestrictedAgent_Claude"
        }
        
        mock_llm_client = Mock()
        mock_llm_client.conversation_history = []
        
        # Create AgentLogic instance
        agent_logic = AgentLogic(mock_state_repo, mock_llm_client)
        
        # Embody the test agent
        success = agent_logic.embody_agent(
            environment="test",
            project="conductor",
            agent_id="TestRestrictedAgent_Claude",
            agent_home_path=self.claude_agent_path,
            project_root_path=Path(self.working_directory)
        )
        
        self.assertTrue(success)
        
        # Verify tools are accessible
        available_tools = agent_logic.get_available_tools()
        self.assertEqual(available_tools, ["Read"])
    
    def test_multiple_tools_configuration(self):
        """Test configuration with multiple allowed tools."""
        # Create temporary agent with multiple tools
        temp_agent_dir = Path(self.temp_dir) / "MultiToolAgent"
        temp_agent_dir.mkdir()
        
        agent_config = """
ai_provider: claude
available_tools:
- Read
- Write
- Grep
description: Test agent with multiple tools
execution_mode: project_resident
id: MultiToolAgent
persona_prompt_path: persona.md
state_file_path: state.json
version: '2.0'
"""
        
        persona_content = "# Persona: Multi Tool Agent\nTest agent with multiple tools."
        state_content = '{"conversation_history": []}'
        
        (temp_agent_dir / "agent.yaml").write_text(agent_config)
        (temp_agent_dir / "persona.md").write_text(persona_content)
        (temp_agent_dir / "state.json").write_text(state_content)
        
        # Load and test
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()
        
        available_tools = prompt_engine.get_available_tools()
        self.assertEqual(sorted(available_tools), ["Grep", "Read", "Write"])
    
    def test_no_tools_configuration(self):
        """Test configuration with no available_tools field."""
        # Create temporary agent with no tools
        temp_agent_dir = Path(self.temp_dir) / "NoToolAgent"
        temp_agent_dir.mkdir()
        
        agent_config = """
ai_provider: claude
description: Test agent with no tools
execution_mode: project_resident
id: NoToolAgent
persona_prompt_path: persona.md
state_file_path: state.json
version: '2.0'
"""
        
        persona_content = "# Persona: No Tool Agent\nTest agent with no tools."
        state_content = '{"conversation_history": []}'
        
        (temp_agent_dir / "agent.yaml").write_text(agent_config)
        (temp_agent_dir / "persona.md").write_text(persona_content)
        (temp_agent_dir / "state.json").write_text(state_content)
        
        # Load and test
        prompt_engine = PromptEngine(temp_agent_dir)
        prompt_engine.load_context()
        
        available_tools = prompt_engine.get_available_tools()
        self.assertEqual(available_tools, [])
    
    def test_gemini_yolo_mode_consistency(self):
        """Test that both admin and project agents use yolo mode (current implementation)."""
        # Create clients
        admin_client = GeminiCLIClient(
            working_directory=self.working_directory,
            timeout=30,
            is_admin_agent=True
        )
        project_client = GeminiCLIClient(
            working_directory=self.working_directory,
            timeout=30,
            is_admin_agent=False
        )
        
        # Mock subprocess to capture commands
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Test response"
            
            # Test admin agent
            try:
                admin_client.invoke("Test admin prompt")
            except Exception:
                pass
                
            # Test project agent  
            try:
                project_client.invoke("Test project prompt")
            except Exception:
                pass
            
            # Both should use yolo mode
            self.assertEqual(mock_run.call_count, 2)
            for call in mock_run.call_args_list:
                call_args = call[0][0]
                self.assertIn("--approval-mode", call_args)
                self.assertIn("yolo", call_args)
    
    def test_gemini_tool_mapping_method_exists(self):
        """Test that tool mapping method still exists (for future use)."""
        # Create Gemini client
        client = GeminiCLIClient(
            working_directory=self.working_directory,
            timeout=30,
            is_admin_agent=False
        )
        
        # Verify method exists even though not currently used
        self.assertTrue(hasattr(client, '_map_tools_to_gemini'))
        
        # Test it still works for future implementation
        test_tools = ["Read", "Write"]
        mapped_tools = client._map_tools_to_gemini(test_tools)
        
        expected_tools = ["read_file", "write_file"]
        self.assertEqual(mapped_tools, expected_tools)


if __name__ == '__main__':
    # Create test output directory
    output_dir = Path(__file__).parent / "fixtures" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    unittest.main()