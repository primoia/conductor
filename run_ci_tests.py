#!/usr/bin/env python3
"""
Script to run CI-safe tests that don't require external services like Claude or Gemini.
This script runs the same tests that would run in GitHub Actions CI environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle its output."""
    print(f"\n🔧 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Exit code: {e.returncode}")
        return False

def main():
    """Main test runner function."""
    print("🚀 Running CI-Safe Tests")
    print("=" * 50)
    print("These tests use only mocks and don't call external services like Claude/Gemini")

    # Change to project directory
    os.chdir(Path(__file__).parent)

    tests_passed = 0
    tests_failed = 0

    # Test commands to run
    test_commands = [
        (
            "poetry run pytest -v --tb=short -m \"not e2e and not integration and not manual and not mongo\" --maxfail=10 tests/",
            "All Unit Tests (excluding external services)"
        ),
        (
            """poetry run pytest -v --tb=short \
                tests/core/services/test_task_execution_service.py \
                tests/core/services/test_agent_storage_service.py \
                tests/core/test_prompt_engine.py \
                tests/core/services/test_configuration_service.py \
                tests/core/services/test_tool_management_service.py \
                tests/core/services/test_session_management_service.py \
                tests/core/services/test_storage_service.py \
                tests/test_argument_parser.py""",
            "Core Service Tests (specific safe tests)"
        )
    ]

    # Run each test command
    for command, description in test_commands:
        if run_command(command, description):
            tests_passed += 1
        else:
            tests_failed += 1

    # Final summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary")
    print("=" * 50)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")

    if tests_failed == 0:
        print("\n🎉 All CI-safe tests passed! Ready for GitHub Actions.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please fix before pushing to CI.")
        sys.exit(1)

if __name__ == "__main__":
    main()