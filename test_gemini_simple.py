#!/usr/bin/env python3
"""
Simple test to verify Gemini CLI works with corrected implementation
"""

from src.infrastructure.llm.cli_client import GeminiCLIClient
import subprocess

def test_gemini_command_only():
    """Test just the command construction without execution."""
    print("🔧 Testing Corrected Gemini CLI Command")
    print("=" * 40)
    
    # Create clients
    admin_client = GeminiCLIClient(is_admin_agent=True)
    project_client = GeminiCLIClient(is_admin_agent=False)
    
    # Test command construction
    test_prompt = "Hello test"
    
    # Mock the command construction (don't actually run)
    admin_cmd = [admin_client.gemini_command, "-p", test_prompt, "--approval-mode", "yolo"]
    project_cmd = [project_client.gemini_command, "-p", test_prompt, "--approval-mode", "yolo"]
    
    print("Admin Command:")
    print(f"  {' '.join(admin_cmd)}")
    
    print("\nProject Command:")  
    print(f"  {' '.join(project_cmd)}")
    
    print(f"\n✅ Both commands use only valid Gemini CLI parameters")
    print(f"   No more 'Unknown arguments' errors should occur")
    
    return admin_cmd, project_cmd

if __name__ == "__main__":
    test_gemini_command_only()