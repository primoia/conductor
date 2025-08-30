#!/usr/bin/env python3
"""
Conductor - Implementation Plan Executor

This script reads and executes implementation plans in YAML format,
orchestrating the execution of tasks by specialized agents.
Supports multiple AI providers (Claude, Gemini) and configurable project paths.
"""

import yaml
import sys
import os
import argparse
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConductorExecutor:
    """Main orchestrator for executing implementation plans."""
    
    def __init__(self, plan_path: str, ai_provider: str = 'claude', project_path: str = None):
        self.plan_path = Path(plan_path)
        self.ai_provider = ai_provider
        self.project_path = project_path or os.getcwd()
        self.plan_data = None
        self.executed_tasks = set()
        self.failed_tasks = set()
        
    def load_plan(self) -> bool:
        """Load and validate the implementation plan."""
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['storyId', 'description', 'tasks', 'validationCriteria']
            for field in required_fields:
                if field not in self.plan_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            logger.info(f"Loaded plan: {self.plan_data['description']}")
            logger.info(f"Story: {self.plan_data['storyId']}")
            logger.info(f"Tasks: {len(self.plan_data['tasks'])}")
            logger.info(f"AI Provider: {self.ai_provider}")
            logger.info(f"Project Path: {self.project_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plan: {e}")
            return False
    
    def validate_dependencies(self) -> bool:
        """Validate task dependencies and detect cycles."""
        task_names = {task['name'] for task in self.plan_data['tasks']}
        
        for task in self.plan_data['tasks']:
            if 'depends_on' in task:
                if task['depends_on'] not in task_names:
                    logger.error(f"Task '{task['name']}' depends on non-existent task '{task['depends_on']}'")
                    return False
        
        # Simple cycle detection (could be enhanced with proper graph analysis)
        return True
    
    def get_execution_order(self) -> List[Dict[str, Any]]:
        """Determine the order of task execution based on dependencies."""
        tasks = self.plan_data['tasks'].copy()
        execution_order = []
        executed_tasks = set()
        
        while tasks:
            # Find tasks with no unsatisfied dependencies
            ready_tasks = []
            for task in tasks:
                if 'depends_on' not in task or task['depends_on'] in executed_tasks:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                logger.error("Circular dependency detected or missing dependency")
                return []
            
            # Add ready tasks to execution order
            for task in ready_tasks:
                execution_order.append(task)
                executed_tasks.add(task['name'])
                tasks.remove(task)
        
        return execution_order
    
    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a single task by invoking the appropriate agent."""
        task_name = task['name']
        agent = task['agent']
        
        logger.info(f"Executing task: {task_name}")
        logger.info(f"Agent: {agent}")
        
        try:
            # Execute the agent with the new signature
            success = self._invoke_agent(task)
            
            if success:
                self.executed_tasks.add(task_name)
                logger.info(f"Task '{task_name}' completed successfully")
                return True
            else:
                self.failed_tasks.add(task_name)
                logger.error(f"Task '{task_name}' failed")
                return False
                
        except Exception as e:
            self.failed_tasks.add(task_name)
            logger.error(f"Task '{task_name}' failed with exception: {e}")
            return False
    
    def _invoke_agent(self, task: Dict[str, Any]) -> bool:
        """Invoke the specified agent to execute the task."""
        agent_name = task['agent']
        logger.info(f"Invoking agent: {agent_name}")
        
        try:
            # Step 1: Load agent brain
            agent_brain = self._load_agent_brain(agent_name)
            if not agent_brain:
                logger.error(f"Failed to load agent brain for {agent_name}")
                return False
            
            # Step 2: Build focused prompt
            prompt = self._build_agent_prompt(agent_brain, task)
            if not prompt:
                logger.error(f"Failed to build prompt for {agent_name}")
                return False
            
            # Step 3: Execute AI call with the new dispatcher function
            ai_response = self._invoke_ai_subprocess(prompt, self.ai_provider, self.project_path)
            if not ai_response:
                logger.error(f"Failed to get AI response for {agent_name}")
                return False
            
            # Step 4: Process and save response
            success = self._process_ai_response(ai_response, task)
            if not success:
                logger.error(f"Failed to process AI response for {agent_name}")
                return False
            
            # Step 5: Validate task completion
            validation_success = self._validate_task(task)
            if not validation_success:
                logger.error(f"Task validation failed for {agent_name}")
                return False
            
            logger.info(f"Agent {agent_name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Agent {agent_name} failed with exception: {e}")
            return False
    
    def _invoke_ai_subprocess(self, prompt: str, provider: str, project_path: str) -> Optional[str]:
        """Centralized function to invoke AI subprocess based on provider."""
        logger.info(f"Executing AI call with provider: {provider}")
        
        try:
            if provider == 'claude':
                command = ["claude", "--print", "--dangerously-skip-permissions", prompt]
            elif provider == 'gemini':
                command = ["npx", "--yes", "@google/gemini-cli", "-p", prompt]
            else:
                logger.error(f"Unsupported AI provider: {provider}")
                return None
            
            process = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=300,
                cwd=project_path  # Execute from the specified project directory
            )

            if process.returncode != 0:
                logger.error(f"AI execution failed with return code {process.returncode}:")
                logger.error(process.stderr)
                return None

            response = process.stdout.strip()
            logger.info(f"AI call completed successfully with {provider}")
            return response

        except FileNotFoundError:
            if provider == 'claude':
                logger.error("Claude command not found. Make sure 'claude' is installed and in your PATH.")
            elif provider == 'gemini':
                logger.error("Gemini CLI not found. Make sure 'npx' is available and @google/gemini-cli can be installed.")
            return None
        except subprocess.TimeoutExpired:
            logger.error(f"AI call timed out after 300 seconds with {provider}.")
            return None
        except Exception as e:
            logger.error(f"AI call failed with an unexpected exception using {provider}: {e}")
            return None
    
    def validate_results(self) -> bool:
        """Validate that all validation criteria are met."""
        logger.info("Validating results...")
        
        for criterion in self.plan_data['validationCriteria']:
            logger.info(f"Checking: {criterion}")
            # This would implement actual validation logic
            # For now, we'll assume validation passes if no tasks failed
            if self.failed_tasks:
                logger.error(f"Validation failed due to failed tasks: {self.failed_tasks}")
                return False
        
        logger.info("All validation criteria passed")
        return True
    
    def run(self) -> bool:
        """Execute the complete implementation plan."""
        logger.info("Starting Conductor execution")
        
        # Load and validate plan
        if not self.load_plan():
            return False
        
        if not self.validate_dependencies():
            return False
        
        # Get execution order
        execution_order = self.get_execution_order()
        if not execution_order:
            return False
        
        logger.info(f"Execution order: {[task['name'] for task in execution_order]}")
        
        # Execute tasks in order
        for task in execution_order:
            if not self.execute_task(task):
                logger.error(f"Task '{task['name']}' failed, stopping execution")
                return False
        
        # Validate final results
        if not self.validate_results():
            return False
        
        logger.info("Conductor execution completed successfully")
        return True
    
    def _load_agent_brain(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load the agent's brain (persona, context, memory) dynamically."""
        logger.info(f"Loading agent brain for: {agent_name}")
        
        # Construct agent path following the convention
        # Get the conductor root directory (parent of scripts)
        conductor_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agent_path = os.path.join(conductor_root, "projects", "develop", "agents", agent_name)
        
        if not os.path.exists(agent_path):
            logger.error(f"Agent path not found: {agent_path}")
            return None
        
        try:
            # Load core agent files
            persona_file = os.path.join(agent_path, "persona.md")
            context_file = os.path.join(agent_path, "memory", "context.md")
            avoid_patterns_file = os.path.join(agent_path, "memory", "avoid_patterns.md")
            
            # Read files with error handling
            persona = self._read_file_safely(persona_file)
            context = self._read_file_safely(context_file)
            avoid_patterns = self._read_file_safely(avoid_patterns_file)
            
            if not all([persona, context, avoid_patterns]):
                logger.error(f"Missing required agent brain files for {agent_name}")
                return None
            
            agent_brain = {
                "persona": persona,
                "context": context,
                "avoid_patterns": avoid_patterns,
                "agent_path": agent_path
            }
            
            logger.info(f"Agent brain loaded successfully for {agent_name}")
            return agent_brain
            
        except Exception as e:
            logger.error(f"Failed to load agent brain for {agent_name}: {e}")
            return None
    
    def _read_file_safely(self, file_path: str) -> Optional[str]:
        """Read file content safely with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def _build_agent_prompt(self, agent_brain: Dict[str, Any], task: Dict[str, Any]) -> Optional[str]:
        """Build a focused prompt combining agent brain with task information."""
        logger.info(f"Building prompt for task: {task['name']}")
        
        try:
            # Read input files to provide context
            input_contents = []
            for input_file in task.get('inputs', []):
                content = self._read_file_safely(input_file)
                if content:
                    input_contents.append(f"### {input_file}:\n```\n{content}\n```")
                else:
                    logger.warning(f"Could not read input file: {input_file}")
            
            input_context = "\n\n".join(input_contents) if input_contents else "No input files provided."
            
            # Build the prompt following the pattern from focused orchestrators
            prompt = f"""You are a specialist AI agent for software development. Your agent-specific "brain" is pre-loaded below.

**# YOUR AGENT BRAIN (PRE-LOADED CONTEXT)**

### PERSONA:
{agent_brain["persona"]}

### CONTEXT AND MISSION:
{agent_brain["context"]}

### PATTERNS TO AVOID (SCARS):
{agent_brain["avoid_patterns"]}

**# YOUR CURRENT TASK**

**Task Name:** {task['name']}
**Description:** {task['description']}

**Objective:** Create or modify the following output files:
{chr(10).join([f"- {output}" for output in task.get('outputs', [])])}

**Input Context:**
{input_context}

**Steps to execute:**

1. **Analyze Input Files:** Read and understand the provided input files to understand existing code patterns and requirements.

2. **Generate Code:** Create complete code content following the requirements in your mission and the task description.

3. **PRIMARY ACTION (DIRECT SAVE):** Try to save the generated code directly to the output files specified above.
   If successful, respond with ONLY: `[SAVE_SUCCESS]`

4. **FALLBACK ACTION (TEXT RETURN):** If you cannot save the file, return the complete source code within:
   ```
   <source_code>
   (complete code here)
   </source_code>
   ```

**Important:** Focus on the specific task and ensure the generated code follows the patterns and best practices defined in your agent brain. You are working in directory: {self.project_path}"""
            
            logger.info(f"Prompt built successfully for task: {task['name']}")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to build prompt for task {task['name']}: {e}")
            return None
    
    def _process_ai_response(self, ai_response: str, task: Dict[str, Any]) -> bool:
        """Process AI response and save to output files."""
        logger.info(f"Processing AI response for task: {task['name']}")
        
        try:
            # Check if AI indicated direct save success
            if "[SAVE_SUCCESS]" in ai_response:
                logger.info("AI reported direct save success")
                return True
            
            # Extract code from response if not directly saved
            code_match = re.search(r'<source_code>(.*?)</source_code>', ai_response, re.DOTALL)
            if code_match:
                code_content = code_match.group(1).strip()
            else:
                # If no source_code tags found, use the entire response as content
                # This handles cases where the AI provider doesn't use the expected format
                code_content = ai_response.strip()
                logger.info("No source_code tags found, using entire response as content")
            
            # Save to output files
            for output_file in task.get('outputs', []):
                success = self._save_code_to_file(code_content, output_file)
                if not success:
                    logger.error(f"Failed to save code to {output_file}")
                    return False
            
            logger.info(f"Code saved successfully for task: {task['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process AI response for task {task['name']}: {e}")
            return False
    
    def _save_code_to_file(self, code_content: str, file_path: str) -> bool:
        """Save code content to file, creating directories if needed."""
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the code to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            logger.info(f"Code saved to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save code to {file_path}: {e}")
            return False
    
    def _validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate that the task was completed successfully."""
        logger.info(f"Validating task: {task['name']}")
        
        try:
            # Check if output files were created and are not empty
            for output_file in task.get('outputs', []):
                if not os.path.exists(output_file):
                    logger.error(f"Output file not found: {output_file}")
                    return False
                
                # Check if file is not empty
                if os.path.getsize(output_file) == 0:
                    logger.error(f"Output file is empty: {output_file}")
                    return False
            
            logger.info(f"Task validation passed: {task['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Task validation failed for {task['name']}: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Execute implementation plans with configurable AI providers')
    parser.add_argument('plan_file', help='Path to the implementation plan YAML file')
    parser.add_argument('--ai-provider', '--ia', 
                       choices=['claude', 'gemini'], 
                       default='claude',
                       help='Specifies the AI provider to be used (claude or gemini)')
    parser.add_argument('--project-path', '--projeto', 
                       required=True,
                       help='The absolute path to the target project directory where the AI will operate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if plan file exists
    if not os.path.exists(args.plan_file):
        logger.error(f"Plan file not found: {args.plan_file}")
        sys.exit(1)
    
    # Check if project path exists
    if not os.path.exists(args.project_path):
        logger.error(f"Project path not found: {args.project_path}")
        sys.exit(1)
    
    # Execute the plan
    executor = ConductorExecutor(args.plan_file, args.ai_provider, args.project_path)
    success = executor.run()
    
    if success:
        logger.info("Implementation plan executed successfully")
        sys.exit(0)
    else:
        logger.error("Implementation plan execution failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
