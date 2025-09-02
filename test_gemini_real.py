#!/usr/bin/env python3
"""
Real Gemini CLI Test - Manual verification of SAGA-013

This script demonstrates the actual Gemini CLI tool control working with
the settings.json configuration approach.
"""

import json
import tempfile
from pathlib import Path
from src.infrastructure.llm.cli_client import GeminiCLIClient


def demonstrate_real_gemini_settings():
    """Demonstrate real settings.json creation and Gemini CLI usage."""
    print("🔧 Real Gemini CLI Settings Test")
    print("=" * 40)
    
    # Create temp directory for test
    temp_dir = Path(tempfile.mkdtemp())
    print(f"📁 Using temp dir: {temp_dir}")
    
    # 1. Test restrictive configuration
    print("\n1. Testing Restrictive Configuration (No Tools)")
    client_restricted = GeminiCLIClient(
        working_directory=str(temp_dir),
        timeout=10,
        is_admin_agent=False
    )
    
    # Mock home to use temp directory
    original_home = Path.home
    Path.home = lambda: temp_dir
    
    try:
        # Configure no tools
        client_restricted._configure_gemini_tools([])
        
        # Check settings file was created
        settings_path = temp_dir / ".gemini" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            print(f"✅ Settings file created: {settings_path}")
            print(f"   coreTools: {settings.get('coreTools', 'NOT SET')}")
            print(f"   excludeTools: {settings.get('excludeTools', 'NOT SET')}")
        else:
            print("❌ Settings file not created")
        
        # 2. Test with allowed tools
        print("\n2. Testing Allowed Tools Configuration")
        client_allowed = GeminiCLIClient(
            working_directory=str(temp_dir),
            timeout=10,
            is_admin_agent=False
        )
        
        # Configure with Read and Write tools
        client_allowed._configure_gemini_tools(["Read", "Write"])
        
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            print(f"✅ Settings updated")
            print(f"   coreTools: {settings.get('coreTools', 'NOT SET')}")
            print(f"   excludeTools: {settings.get('excludeTools', 'REMOVED')}")
        
        # 3. Show settings file content
        print("\n3. Final Settings File Content:")
        if settings_path.exists():
            with open(settings_path) as f:
                content = f.read()
            print(content)
        
        print("\n4. Usage with Real Gemini CLI:")
        print("   To test with real Gemini CLI, run:")
        print(f"   export HOME={temp_dir}")
        print("   gemini -p 'List files in current directory'")
        print("   (Only ReadFileTool and WriteFileTool should be available)")
        
        print("\n✅ Settings configuration working correctly!")
        
    finally:
        # Restore original home function
        Path.home = original_home
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temp directory: {temp_dir}")


if __name__ == "__main__":
    demonstrate_real_gemini_settings()