#!/usr/bin/env python3
"""
Test script for the new unified Conductor interface.
Tests all the new command combinations and modes.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description, expect_success=True):
    """Execute a command and show the result."""
    print(f"\n🧪 Testing: {description}")
    print(f"📝 Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        
        if (result.returncode == 0) == expect_success:
            print("✅ SUCCESS" if expect_success else "✅ EXPECTED FAILURE")
            if result.stdout:
                print("📤 Output:")
                print(result.stdout[:300] + "..." if len(result.stdout) > 300 else result.stdout)
        else:
            print("❌ UNEXPECTED RESULT")
            if result.stderr:
                print("📤 Error:")
                print(result.stderr[:300] + "..." if len(result.stderr) > 300 else result.stderr)
                
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT (15s) - command may be working but took too long")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

def main():
    """Test the new unified Conductor interface."""
    print("🚀 TESTING NEW UNIFIED CONDUCTOR INTERFACE")
    print("=" * 70)
    
    # Check if conductor exists
    conductor_path = Path("./conductor")
    if not conductor_path.exists():
        print("⚠️ File ./conductor not found, using python directly")
        base_cmd = "python src/cli/conductor.py"
    else:
        base_cmd = "./conductor"
    
    print("\n📋 SYSTEM OPERATIONS TESTS")
    system_tests = [
        (f"{base_cmd} --help", "Help message"),
        (f"{base_cmd} --list", "List all agents"),
        (f"{base_cmd} --validate", "Validate system configuration"),
        (f"{base_cmd} --info SystemGuide_Meta_Agent", "Agent information", False),  # May not exist
    ]
    
    for cmd, desc, *expect in system_tests:
        expect_success = expect[0] if expect else True
        run_command(cmd, desc, expect_success)
    
    print("\n🎯 EXECUTION MODE TESTS")
    execution_tests = [
        # Test argument validation
        (f"{base_cmd} --agent TestAgent", "Agent without input (should fail)", False),
        (f"{base_cmd} --interactive", "Interactive without agent (should fail)", False),
        (f"{base_cmd} --agent TestAgent --interactive", "Interactive without chat (should fail)", False),
        
        # Test new interface help
        (f"{base_cmd} --agent TestAgent --input 'test' --help", "Help with agent args", False),
    ]
    
    for cmd, desc, expect_success in execution_tests:
        run_command(cmd, desc, expect_success)
    
    print("\n🔄 LEGACY COMPATIBILITY TESTS")
    legacy_tests = [
        (f"{base_cmd} list-agents", "Legacy list-agents command"),
        (f"{base_cmd} validate-config", "Legacy validate-config command"),
        (f"{base_cmd} execute --help", "Legacy execute help"),
        (f"{base_cmd} repl --help", "Legacy repl help"),
        (f"{base_cmd} chat --help", "Legacy chat help"),
    ]
    
    for cmd, desc in legacy_tests:
        run_command(cmd, desc)
    
    print("\n" + "=" * 70)
    print("🏆 TEST SUMMARY")
    print("✅ If system operations work, the new interface is functional")
    print("✅ If legacy commands work, backward compatibility is maintained")
    print("✅ If validation tests fail as expected, argument validation works")
    
    print("\n💡 MANUAL TESTS TO RUN:")
    print("# Test stateless execution (if you have agents)")
    print(f"{base_cmd} --agent SystemGuide_Meta_Agent --input 'How does Conductor work?'")
    
    print("\n# Test contextual chat (if you have agents)")
    print(f"{base_cmd} --agent SystemGuide_Meta_Agent --chat --input 'Explain the architecture'")
    print(f"{base_cmd} --agent SystemGuide_Meta_Agent --chat --input 'Continue explaining'")
    
    print("\n# Test interactive mode (if you have agents)")
    print(f"{base_cmd} --agent SystemGuide_Meta_Agent --chat --interactive")
    
    print("\n# Test simulation mode")
    print(f"{base_cmd} --agent SystemGuide_Meta_Agent --input 'test' --simulate")
    
    print("\n🎯 NEW INTERFACE FEATURES TO VERIFY:")
    print("1. Stateless execution is faster (no history loading)")
    print("2. Contextual chat preserves conversation history")
    print("3. Interactive mode works after initial message")
    print("4. Simulation mode doesn't call real AI")
    print("5. Legacy commands still work for backward compatibility")

if __name__ == "__main__":
    main()