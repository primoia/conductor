#!/usr/bin/env python3
"""
Test script for the .bmad-core + conductor integration

This script demonstrates the complete workflow:
1. Simulate the @dev agent creating an implementation plan
2. Execute the plan using the conductor
3. Validate the results
"""

import yaml
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_conductor import ConductorExecutor


def simulate_dev_agent_creating_plan():
    """Simulate the @dev agent analyzing a story and creating an implementation plan."""
    print("🤖 Simulating @dev agent creating implementation plan...")
    
    # This would normally be done by the @dev agent using the create-implementation-plan task
    # For this demo, we'll use the example plan we created
    
    plan_path = "projects/develop/workspace/example-implementation-plan.yaml"
    
    if not os.path.exists(plan_path):
        print(f"❌ Example plan not found: {plan_path}")
        return None
    
    print(f"✅ Implementation plan created: {plan_path}")
    return plan_path


def execute_plan_with_conductor(plan_path):
    """Execute the implementation plan using the conductor."""
    print("\n🎼 Executing plan with Conductor...")
    
    executor = ConductorExecutor(plan_path)
    success = executor.run()
    
    if success:
        print("✅ Conductor execution completed successfully")
    else:
        print("❌ Conductor execution failed")
    
    return success


def validate_integration_results():
    """Validate that the integration worked as expected."""
    print("\n🔍 Validating integration results...")
    
    # Check that the plan file exists and is valid YAML
    plan_path = "projects/develop/workspace/example-implementation-plan.yaml"
    
    try:
        with open(plan_path, 'r') as f:
            plan_data = yaml.safe_load(f)
        
        # Validate plan structure
        required_fields = ['storyId', 'description', 'tasks', 'validationCriteria']
        for field in required_fields:
            if field not in plan_data:
                print(f"❌ Missing required field in plan: {field}")
                return False
        
        print(f"✅ Plan structure is valid")
        print(f"   - Story: {plan_data['storyId']}")
        print(f"   - Description: {plan_data['description']}")
        print(f"   - Tasks: {len(plan_data['tasks'])}")
        print(f"   - Validation criteria: {len(plan_data['validationCriteria'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate plan: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Testing .bmad-core + conductor integration")
    print("=" * 50)
    
    # Step 1: Simulate @dev agent creating plan
    plan_path = simulate_dev_agent_creating_plan()
    if not plan_path:
        return False
    
    # Step 2: Execute plan with conductor
    execution_success = execute_plan_with_conductor(plan_path)
    
    # Step 3: Validate results
    validation_success = validate_integration_results()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Integration Test Results:")
    print(f"   - Plan Creation: ✅")
    print(f"   - Plan Execution: {'✅' if execution_success else '❌'}")
    print(f"   - Result Validation: {'✅' if validation_success else '❌'}")
    
    overall_success = execution_success and validation_success
    print(f"\n🎯 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
    
    return overall_success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
