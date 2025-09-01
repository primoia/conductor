#!/usr/bin/env python3
"""
End-to-End Test for Full Agent Lifecycle
  
This test simulates the complete usage of the conductor framework:
1. CREATE: Create a new test agent via CLI
2. VALIDATE CREATE: Verify agent files were created properly
3. EXECUTE: Run the agent with a simple command via CLI
4. VALIDATE EXECUTION: Verify execution was successful and state was updated
5. CLEANUP: Remove test agent to keep tests idempotent

This ensures the framework works end-to-end as a real user would use it.
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.exceptions import ConductorException, AgentNotFoundError


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.manual  
class TestFullAgentLifecycle(unittest.TestCase):
    """
    End-to-End test that validates the complete agent lifecycle.
    
    This test uses subprocess to call the CLI commands directly,
    ensuring a true integration test that mirrors real user interaction.
    
    MARKED AS MANUAL - Run only when needed:
    - Requires AgentCreator_Agent to be available
    - Creates/deletes files in filesystem  
    - Makes actual CLI calls with subprocess
    - Takes longer to run (network calls, file operations)
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_agent_id = "_TestDummyAgent"
        cls.base_path = Path(__file__).parent.parent.parent
        cls.test_agent_path = cls.base_path / "projects" / "_common" / "agents" / cls.test_agent_id
        
        # Ensure test environment is clean
        if cls.test_agent_path.exists():
            shutil.rmtree(cls.test_agent_path)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if cls.test_agent_path.exists():
            shutil.rmtree(cls.test_agent_path)
    
    def test_full_agent_lifecycle_e2e(self):
        """
        Test the complete agent lifecycle End-to-End.
        
        This test simulates the real user workflow:
        CREATE -> VALIDATE CREATE -> EXECUTE -> VALIDATE EXECUTION -> CLEANUP
        """
        print(f"\n🚀 Starting E2E Agent Lifecycle Test")
        print(f"   Test Agent: {self.test_agent_id}")
        print(f"   Agent Path: {self.test_agent_path}")
        
        # PHASE 1: CREATE - Create a new test agent
        print(f"\n📝 PHASE 1: Creating test agent...")
        
        create_command = [
            "python", "-m", "src.cli.admin",
            "--agent", "AgentCreator_Agent",
            "--destination-path", str(self.test_agent_path.parent),
            "--input", f"Create a simple test agent named {self.test_agent_id} for E2E testing. This agent should be able to respond to basic greetings."
        ]
        
        create_result = subprocess.run(
            create_command,
            cwd=self.base_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"   Create command exit code: {create_result.returncode}")
        if create_result.stderr:
            print(f"   Create stderr: {create_result.stderr}")
        
        # Check if creation was successful (exit code 0)
        if create_result.returncode != 0:
            # If AgentCreator_Agent is not available, skip this test
            if "Agent 'AgentCreator_Agent' not found" in create_result.stderr:
                self.skipTest("AgentCreator_Agent not available - skipping E2E test")
            else:
                self.fail(f"Agent creation failed: {create_result.stderr}")
        
        # PHASE 2: VALIDATE CREATE - Verify agent files were created
        print(f"\n✅ PHASE 2: Validating agent creation...")
        
        # Check if agent directory was created
        self.assertTrue(self.test_agent_path.exists(), 
                       f"Agent directory was not created: {self.test_agent_path}")
        
        # Check if required files exist
        agent_yaml_path = self.test_agent_path / "agent.yaml"
        persona_md_path = self.test_agent_path / "persona.md"
        state_json_path = self.test_agent_path / "state.json"
        
        self.assertTrue(agent_yaml_path.exists(),
                       f"agent.yaml not found: {agent_yaml_path}")
        self.assertTrue(persona_md_path.exists(),
                       f"persona.md not found: {persona_md_path}")
        
        # Validate agent.yaml content
        with open(agent_yaml_path, 'r', encoding='utf-8') as f:
            agent_config = yaml.safe_load(f) if 'yaml' in globals() else None
        
        if agent_config is None:
            # If yaml is not available, just check the file is not empty
            with open(agent_yaml_path, 'r', encoding='utf-8') as f:
                agent_yaml_content = f.read().strip()
                self.assertTrue(len(agent_yaml_content) > 0,
                               "agent.yaml is empty")
        else:
            self.assertIn('name', agent_config,
                         "agent.yaml missing 'name' field")
        
        # Validate persona.md is not empty
        with open(persona_md_path, 'r', encoding='utf-8') as f:
            persona_content = f.read().strip()
            self.assertTrue(len(persona_content) > 0,
                           "persona.md is empty")
        
        print(f"   ✅ Agent files created successfully")
        
        # PHASE 3: EXECUTE - Run the agent with a simple command
        print(f"\n🤖 PHASE 3: Executing test agent...")
        
        execute_command = [
            "python", "-m", "src.cli.admin",
            "--agent", self.test_agent_id,
            "--input", "Hello! Please respond with a simple greeting."
        ]
        
        execute_result = subprocess.run(
            execute_command,
            cwd=self.base_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"   Execute command exit code: {execute_result.returncode}")
        if execute_result.stderr:
            print(f"   Execute stderr: {execute_result.stderr}")
        
        # Check if execution was successful
        self.assertEqual(execute_result.returncode, 0,
                        f"Agent execution failed: {execute_result.stderr}")
        
        # Verify that there was some response output
        self.assertTrue(len(execute_result.stdout) > 0,
                       "No output received from agent execution")
        
        print(f"   ✅ Agent executed successfully")
        
        # PHASE 4: VALIDATE EXECUTION - Verify state was updated
        print(f"\n📊 PHASE 4: Validating execution state...")
        
        # Check if state.json was created/updated after execution
        self.assertTrue(state_json_path.exists(),
                       f"state.json not found after execution: {state_json_path}")
        
        # Validate state.json content
        with open(state_json_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        # Check if conversation history was recorded
        self.assertIn('conversation_history', state_data,
                     "conversation_history not found in state.json")
        
        conversation_history = state_data['conversation_history']
        self.assertTrue(len(conversation_history) > 0,
                       "No conversation history recorded")
        
        # Check if the last interaction contains our input
        last_interaction = conversation_history[-1]
        self.assertIn('prompt', last_interaction,
                     "Last interaction missing 'prompt' field")
        self.assertIn('response', last_interaction,
                     "Last interaction missing 'response' field")
        
        # Verify our input is in the prompt
        self.assertIn('Hello', last_interaction['prompt'],
                     "Our input not found in conversation history")
        
        print(f"   ✅ Agent state updated successfully")
        
        # PHASE 5: CLEANUP - Remove test agent (handled by tearDownClass)
        print(f"\n🧹 PHASE 5: Cleanup will be handled by tearDownClass")
        
        print(f"\n🎉 E2E Agent Lifecycle Test PASSED!")
        print(f"   All phases completed successfully:")
        print(f"   ✅ CREATE: Agent created via CLI")
        print(f"   ✅ VALIDATE CREATE: Agent files verified")
        print(f"   ✅ EXECUTE: Agent executed via CLI") 
        print(f"   ✅ VALIDATE EXECUTION: State updated correctly")


if __name__ == "__main__":
    # Try to import yaml for better validation, but don't require it
    try:
        import yaml
    except ImportError:
        yaml = None
        print("⚠️  Warning: PyYAML not available, skipping agent.yaml validation")
    
    unittest.main(verbosity=2)