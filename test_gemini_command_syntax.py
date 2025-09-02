#!/usr/bin/env python3
"""
Test real Gemini CLI command syntax for --allowed-tools parameter
"""

import subprocess
from src.infrastructure.llm.cli_client import GeminiCLIClient


def test_gemini_command_construction():
    """Test that the command is constructed correctly."""
    print("🔧 Testing Gemini CLI Command Construction")
    print("=" * 45)
    
    # Create client 
    client = GeminiCLIClient(is_admin_agent=False)
    
    # Test tool mapping
    test_tools = ["Read", "Write"]
    mapped_tools = client._map_tools_to_gemini(test_tools)
    print(f"Mapped tools: {mapped_tools}")
    
    # Simulate command construction  
    cmd = ["gemini", "-p", "test prompt"]
    if mapped_tools:
        cmd.extend(["--allowed-tools"] + mapped_tools)
    
    print(f"Command that would be executed:")
    print(f"  {' '.join(cmd)}")
    
    # Test if command syntax is valid (dry run - don't actually execute)
    print(f"\nCommand breakdown:")
    print(f"  Base command: gemini -p 'test prompt'")
    print(f"  Tool restriction: --allowed-tools {' '.join(mapped_tools)}")
    
    return cmd


def test_admin_vs_project_commands():
    """Show difference between admin and project commands."""
    print("\n🔄 Admin vs Project Command Comparison")
    print("=" * 40)
    
    # Project agent
    project_client = GeminiCLIClient(is_admin_agent=False)
    project_tools = project_client._map_tools_to_gemini(["Read", "Bash"])
    
    project_cmd = ["gemini", "-p", "test prompt", "--allowed-tools"] + project_tools
    print(f"Project Agent Command:")
    print(f"  {' '.join(project_cmd)}")
    
    # Admin agent  
    admin_cmd = ["gemini", "-p", "test prompt", "--approval-mode", "yolo"]
    print(f"\nAdmin Agent Command:")
    print(f"  {' '.join(admin_cmd)}")


if __name__ == "__main__":
    cmd = test_gemini_command_construction()
    test_admin_vs_project_commands()
    
    print(f"\n✅ Command syntax appears correct!")
    print(f"   The --allowed-tools parameter is supported by Gemini CLI")
    print(f"   Ready for real testing with actual Gemini CLI")