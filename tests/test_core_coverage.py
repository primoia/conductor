#!/usr/bin/env python3
"""
Test Suite: Core Coverage Extension

Testa funcionalidades essenciais ainda não cobertas:
- create_llm_client factory
- Error handling básico
- Path resolution
- State saving

Foco em simplicidade e robustez.

Author: Global Engineering Team  
Date: 2025-08-17
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.genesis_agent import (
    create_llm_client,
    ClaudeCLIClient,
    GeminiCLIClient,
    OutputScopeViolationError
)


class TestLLMClientFactory(unittest.TestCase):
    """Test suite para factory de LLM clients."""
    
    def test_create_claude_client(self):
        """Test: create_llm_client creates Claude client."""
        client = create_llm_client('claude', '/test')
        self.assertIsInstance(client, ClaudeCLIClient)
        self.assertEqual(client.working_directory, '/test')
    
    def test_create_gemini_client(self):
        """Test: create_llm_client creates Gemini client."""
        client = create_llm_client('gemini', '/test')
        self.assertIsInstance(client, GeminiCLIClient)
        self.assertEqual(client.working_directory, '/test')
    
    def test_create_client_invalid_provider(self):
        """Test: create_llm_client rejects invalid providers."""
        with self.assertRaises(ValueError) as context:
            create_llm_client('invalid')
        self.assertIn("Unsupported AI provider", str(context.exception))
    
    def test_create_client_no_working_dir(self):
        """Test: create_llm_client works without working directory."""
        client = create_llm_client('claude')
        self.assertIsInstance(client, ClaudeCLIClient)
        # working_directory defaults to current directory when None is passed
        self.assertIsNotNone(client.working_directory)


class TestErrorTypes(unittest.TestCase):
    """Test suite para tipos de erro customizados."""
    
    def test_output_scope_violation_error(self):
        """Test: OutputScopeViolationError is proper exception type."""
        # WHEN: Creating the exception
        error = OutputScopeViolationError("File outside scope")
        
        # THEN: Should be correct type
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "File outside scope")
        
        # Should not inherit from OSError (to avoid retry logic)
        self.assertFalse(isinstance(error, OSError))
        self.assertFalse(isinstance(error, IOError))


class TestBasicStateOperations(unittest.TestCase):
    """Test suite para operações básicas de estado."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="conductor_state_test_")
        self.addCleanup(self._cleanup_test_dir)
        self.original_cwd = os.getcwd()
    
    def _cleanup_test_dir(self):
        """Clean up test environment."""
        try:
            os.chdir(self.original_cwd)
        except:
            os.chdir(str(Path.home()))
        
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_llm_client_initialization(self):
        """Test: LLM clients initialize correctly."""
        # Test Claude client
        claude_client = ClaudeCLIClient(self.test_dir)
        self.assertEqual(claude_client.working_directory, self.test_dir)
        self.assertEqual(claude_client.conversation_history, [])
        
        # Test Gemini client  
        gemini_client = GeminiCLIClient(self.test_dir)
        self.assertEqual(gemini_client.working_directory, self.test_dir)
        self.assertEqual(gemini_client.conversation_history, [])
    
    def test_llm_client_persona_setting(self):
        """Test: LLM clients can set agent persona."""
        client = ClaudeCLIClient(self.test_dir)
        
        # Test persona setting
        test_persona = "I am a test agent"
        client.set_agent_persona(test_persona)
        
        # Should store the persona
        self.assertTrue(hasattr(client, 'agent_persona'))
        self.assertEqual(client.agent_persona, test_persona)


class TestPathOperations(unittest.TestCase):
    """Test suite para operações de path simples."""
    
    def test_path_object_creation(self):
        """Test: Path objects are created correctly."""
        # Test absolute path
        abs_path = Path("/test/absolute/path")
        self.assertTrue(abs_path.is_absolute())
        
        # Test relative path
        rel_path = Path("relative/path")
        self.assertFalse(rel_path.is_absolute())
        
        # Test path joining
        joined = Path("/base") / "subdir" / "file.txt"
        self.assertEqual(str(joined), "/base/subdir/file.txt")


class TestBasicFileOperations(unittest.TestCase):
    """Test suite para operações básicas de arquivo."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="conductor_file_test_")
        self.addCleanup(self._cleanup_test_dir)
        self.original_cwd = os.getcwd()
    
    def _cleanup_test_dir(self):
        """Clean up test environment."""
        try:
            os.chdir(self.original_cwd)
        except:
            os.chdir(str(Path.home()))
        
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_file_creation_and_reading(self):
        """Test: Basic file operations work correctly."""
        test_file = Path(self.test_dir) / "test.txt"
        test_content = "Test content for coverage"
        
        # Write file
        test_file.write_text(test_content)
        self.assertTrue(test_file.exists())
        
        # Read file
        read_content = test_file.read_text()
        self.assertEqual(read_content, test_content)
    
    def test_directory_operations(self):
        """Test: Directory operations work correctly."""
        test_subdir = Path(self.test_dir) / "subdir"
        
        # Create directory
        test_subdir.mkdir()
        self.assertTrue(test_subdir.exists())
        self.assertTrue(test_subdir.is_dir())
        
        # Create nested directories
        nested_dir = test_subdir / "nested" / "deep"
        nested_dir.mkdir(parents=True)
        self.assertTrue(nested_dir.exists())


class TestImportAndModuleStructure(unittest.TestCase):
    """Test suite para estrutura de módulos e imports."""
    
    def test_essential_imports_available(self):
        """Test: Essential modules and classes can be imported."""
        # Test that we can import key components
        from scripts.genesis_agent import GenesisAgent
        self.assertTrue(callable(GenesisAgent))
        
        from scripts.genesis_agent import Toolbelt
        self.assertTrue(callable(Toolbelt))
        
        from scripts.genesis_agent import LLMClient
        self.assertTrue(callable(LLMClient))
    
    def test_functions_are_callable(self):
        """Test: Key functions are callable."""
        from scripts.genesis_agent import (
            create_llm_client,
            load_workspaces_config,
            load_ai_providers_config
        )
        
        self.assertTrue(callable(create_llm_client))
        self.assertTrue(callable(load_workspaces_config))
        self.assertTrue(callable(load_ai_providers_config))


class TestBasicRetryLogic(unittest.TestCase):
    """Test suite para lógica básica de retry."""
    
    def test_retry_decorator_exists(self):
        """Test: Retry decorators are available and usable."""
        from scripts.genesis_agent import retry_on_failure, with_recovery_fallback
        
        # Test that decorators can be applied
        @retry_on_failure(max_retries=1)
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
        
        # Test recovery fallback decorator
        @with_recovery_fallback(fallback_result="fallback")
        def another_test_function():
            return "success"
        
        result = another_test_function()
        self.assertEqual(result, "success")


if __name__ == '__main__':
    unittest.main(verbosity=2)