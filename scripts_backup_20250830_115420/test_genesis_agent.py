#!/usr/bin/env python3
"""
Unit tests for Genesis Agent Milestone 1

Tests the deterministic logic:
- Command line argument parsing
- Agent YAML loading and parsing
- Agent directory location logic
"""

import unittest
import tempfile
import os
import sys
import yaml
from unittest.mock import patch, mock_open
from io import StringIO

# Add the scripts directory to the path to import genesis_agent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import genesis_agent


class TestGenesisAgentArgumentParsing(unittest.TestCase):
    """Test command line argument parsing functionality."""
    
    def test_parse_arguments_with_required_embody(self):
        """Test that --embody argument is correctly parsed."""
        with patch('sys.argv', ['genesis_agent.py', '--embody', 'TestAgent']):
            args = genesis_agent.parse_arguments()
            self.assertEqual(args.embody, 'TestAgent')
            self.assertFalse(args.verbose)
            self.assertIsNone(args.state)
    
    def test_parse_arguments_with_all_options(self):
        """Test parsing with all command line options."""
        with patch('sys.argv', ['genesis_agent.py', '--embody', 'TestAgent', '--state', 'test.json', '--verbose']):
            args = genesis_agent.parse_arguments()
            self.assertEqual(args.embody, 'TestAgent')
            self.assertTrue(args.verbose)
            self.assertEqual(args.state, 'test.json')
    
    def test_parse_arguments_missing_embody(self):
        """Test that missing --embody argument raises SystemExit."""
        with patch('sys.argv', ['genesis_agent.py']):
            with self.assertRaises(SystemExit):
                genesis_agent.parse_arguments()
    
    def test_parse_arguments_verbose_flag(self):
        """Test that --verbose flag is correctly parsed."""
        with patch('sys.argv', ['genesis_agent.py', '--embody', 'TestAgent', '--verbose']):
            args = genesis_agent.parse_arguments()
            self.assertTrue(args.verbose)
    
    def test_parse_arguments_state_option(self):
        """Test that --state option is correctly parsed."""
        with patch('sys.argv', ['genesis_agent.py', '--embody', 'TestAgent', '--state', 'session.json']):
            args = genesis_agent.parse_arguments()
            self.assertEqual(args.state, 'session.json')


class TestGenesisAgentDirectoryLocation(unittest.TestCase):
    """Test agent directory location logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.genesis = genesis_agent.GenesisAgent('TestAgent')
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.path.abspath')
    @patch('os.path.dirname')
    def test_locate_agent_directory_success(self, mock_dirname, mock_abspath, mock_isdir, mock_exists):
        """Test successful agent directory location."""
        # Mock the path resolution
        mock_abspath.return_value = '/mock/conductor/scripts/genesis_agent.py'
        mock_dirname.side_effect = ['/mock/conductor/scripts', '/mock/conductor']
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        result = self.genesis.locate_agent_directory()
        
        self.assertTrue(result)
        self.assertEqual(self.genesis.agent_path, '/mock/conductor/projects/develop/agents/TestAgent')
    
    @patch('os.path.exists')
    def test_locate_agent_directory_not_exists(self, mock_exists):
        """Test agent directory location when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = self.genesis.locate_agent_directory()
        
        self.assertFalse(result)
        self.assertIsNone(self.genesis.agent_path)
    
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_locate_agent_directory_not_directory(self, mock_isdir, mock_exists):
        """Test agent directory location when path exists but is not a directory."""
        mock_exists.return_value = True
        mock_isdir.return_value = False
        
        result = self.genesis.locate_agent_directory()
        
        self.assertFalse(result)
        self.assertIsNone(self.genesis.agent_path)


class TestGenesisAgentYamlLoading(unittest.TestCase):
    """Test YAML loading and parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.genesis = genesis_agent.GenesisAgent('TestAgent')
        self.genesis.agent_path = '/mock/agent/path'
    
    def test_load_agent_yaml_no_path_set(self):
        """Test YAML loading when agent path is not set."""
        self.genesis.agent_path = None
        result = self.genesis.load_agent_yaml()
        self.assertFalse(result)
    
    @patch('os.path.exists')
    def test_load_agent_yaml_file_not_exists(self, mock_exists):
        """Test YAML loading when agent.yaml doesn't exist."""
        mock_exists.return_value = False
        
        result = self.genesis.load_agent_yaml()
        
        self.assertFalse(result)
        self.assertIsNone(self.genesis.agent_data)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_agent_yaml_success(self, mock_file, mock_exists):
        """Test successful YAML loading with valid agent data."""
        mock_exists.return_value = True
        valid_yaml_content = """
id: TestAgent
version: 1.0
description: "Test agent for unit testing"
persona_prompt_path: "persona.md"
state_file_path: "state.json"
execution_task: "Test task"
available_tools:
  - read_file
  - write_file
"""
        mock_file.return_value.read.return_value = valid_yaml_content
        
        result = self.genesis.load_agent_yaml()
        
        self.assertTrue(result)
        self.assertIsNotNone(self.genesis.agent_data)
        self.assertEqual(self.genesis.agent_data['id'], 'TestAgent')
        self.assertEqual(self.genesis.agent_data['version'], 1.0)
        self.assertEqual(self.genesis.agent_data['description'], 'Test agent for unit testing')
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_agent_yaml_missing_required_fields(self, mock_file, mock_exists):
        """Test YAML loading with missing required fields."""
        mock_exists.return_value = True
        invalid_yaml_content = """
id: TestAgent
description: "Missing version field"
"""
        mock_file.return_value.read.return_value = invalid_yaml_content
        
        result = self.genesis.load_agent_yaml()
        
        self.assertFalse(result)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_agent_yaml_id_mismatch(self, mock_file, mock_exists):
        """Test YAML loading with mismatched agent ID."""
        mock_exists.return_value = True
        invalid_yaml_content = """
id: DifferentAgent
version: 1.0
description: "Agent with wrong ID"
"""
        mock_file.return_value.read.return_value = invalid_yaml_content
        
        result = self.genesis.load_agent_yaml()
        
        self.assertFalse(result)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_agent_yaml_invalid_yaml(self, mock_file, mock_exists):
        """Test YAML loading with invalid YAML syntax."""
        mock_exists.return_value = True
        invalid_yaml_content = """
id: TestAgent
version: 1.0
description: "Invalid YAML
  missing quote
"""
        mock_file.return_value.read.return_value = invalid_yaml_content
        
        result = self.genesis.load_agent_yaml()
        
        self.assertFalse(result)


class TestGenesisAgentIntegration(unittest.TestCase):
    """Integration tests for the complete agent loading process."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.genesis = genesis_agent.GenesisAgent('TestAgent')
    
    @patch.object(genesis_agent.GenesisAgent, 'locate_agent_directory')
    @patch.object(genesis_agent.GenesisAgent, 'load_agent_yaml')
    def test_load_agent_success(self, mock_load_yaml, mock_locate_dir):
        """Test successful complete agent loading."""
        mock_locate_dir.return_value = True
        mock_load_yaml.return_value = True
        
        result = self.genesis.load_agent()
        
        self.assertTrue(result)
        mock_locate_dir.assert_called_once()
        mock_load_yaml.assert_called_once()
    
    @patch.object(genesis_agent.GenesisAgent, 'locate_agent_directory')
    def test_load_agent_directory_failure(self, mock_locate_dir):
        """Test agent loading failure when directory location fails."""
        mock_locate_dir.return_value = False
        
        result = self.genesis.load_agent()
        
        self.assertFalse(result)
        mock_locate_dir.assert_called_once()
    
    @patch.object(genesis_agent.GenesisAgent, 'locate_agent_directory')
    @patch.object(genesis_agent.GenesisAgent, 'load_agent_yaml')
    def test_load_agent_yaml_failure(self, mock_load_yaml, mock_locate_dir):
        """Test agent loading failure when YAML loading fails."""
        mock_locate_dir.return_value = True
        mock_load_yaml.return_value = False
        
        result = self.genesis.load_agent()
        
        self.assertFalse(result)
        mock_locate_dir.assert_called_once()
        mock_load_yaml.assert_called_once()
    
    def test_get_agent_data_not_loaded(self):
        """Test getting agent data when no agent is loaded."""
        with self.assertRaises(RuntimeError):
            self.genesis.get_agent_data()
    
    def test_get_agent_data_loaded(self):
        """Test getting agent data when agent is loaded."""
        test_data = {'id': 'TestAgent', 'version': 1.0, 'description': 'Test'}
        self.genesis.agent_data = test_data
        
        result = self.genesis.get_agent_data()
        
        self.assertEqual(result, test_data)
        # Ensure we get a copy, not the original
        self.assertIsNot(result, self.genesis.agent_data)


class TestGenesisAgentOutput(unittest.TestCase):
    """Test output formatting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.genesis = genesis_agent.GenesisAgent('TestAgent')
        self.genesis.agent_path = '/mock/agent/path'
        self.genesis.agent_data = {
            'id': 'TestAgent',
            'version': 1.0,
            'description': 'Test agent for unit testing'
        }
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_agent_summary(self, mock_stdout):
        """Test that agent summary is printed correctly."""
        self.genesis.print_agent_summary()
        
        output = mock_stdout.getvalue()
        self.assertIn('GENESIS AGENT - MILESTONE 1 OUTPUT', output)
        self.assertIn('Agent ID: TestAgent', output)
        self.assertIn('Version: 1.0', output)
        self.assertIn('Description: Test agent for unit testing', output)
        self.assertIn('Agent Path: /mock/agent/path', output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_agent_summary_no_data(self, mock_stdout):
        """Test printing summary when no agent data is loaded."""
        self.genesis.agent_data = None
        
        self.genesis.print_agent_summary()
        
        output = mock_stdout.getvalue()
        self.assertEqual(output, '')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)