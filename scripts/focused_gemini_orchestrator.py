#!/usr/bin/env python3

import os
import json
import subprocess
import sys
import re

def read_file_content(file_path):
    """Read file content safely with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ ERROR reading {file_path}: {e}", file=sys.stderr)
        return None

def load_agent_brain(agent_path):
    """Load only agent-specific files (persona, context, avoid_patterns, task)"""
    print("\n📖 Loading agent brain...")
    
    # Load core agent files
    persona = read_file_content(os.path.join(agent_path, "persona.md"))
    context = read_file_content(os.path.join(agent_path, "memory", "context.md"))
    avoid_patterns = read_file_content(os.path.join(agent_path, "memory", "avoid_patterns.md"))
    
    # Load task from inbox
    task_file_path = os.path.join(agent_path, "workspace", "inbox", "task-001.json")
    task_data_str = read_file_content(task_file_path)
    
    if not all([persona, context, avoid_patterns, task_data_str]):
        print("❌ CRITICAL: Missing agent brain components", file=sys.stderr)
        return None
        
    try:
        task = json.loads(task_data_str)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR parsing task JSON: {e}", file=sys.stderr)
        return None
    
    print("  ✅ Agent brain loaded successfully")
    return {
        "persona": persona,
        "context": context,
        "avoid_patterns": avoid_patterns,
        "task": task
    }

def build_focused_prompt(agent_brain, project_path):
    """Build a focused prompt with only agent-specific context"""
    print("\n📝 Building focused prompt...")
    
    task = agent_brain["task"]
    
    # For analysis tasks, we might not have reference files, so we handle that
    reference_files = task["details"].get("reference_files_to_read", [])
    
    # The target file might also be optional for analysis tasks
    target_file = task["details"].get("target_file_to_create_content_for")

    reference_paths_str = 'No specific files to read for this analysis.'
    if reference_files:
        relative_paths = []
        for abs_path in reference_files:
            if project_path in abs_path:
                rel_path = abs_path.replace(project_path + "/", "")
                relative_paths.append(rel_path)
            else:
                relative_paths.append(abs_path)
        reference_paths_str = '\n'.join([f"- {path}" for path in relative_paths])

    action_instruction = ""
    if target_file:
        action_instruction = f"""
3. **PRIMARY ACTION (DIRECT SAVE):** Try to save the generated code directly to: `{target_file}`
   If successful, respond with ONLY: `[SAVE_SUCCESS]`

4. **FALLBACK ACTION (TEXT RETURN):** If you cannot save the file, return the complete source code within:
   ```
   <source_code>
   (complete kotlin code here)
   </source_code>
   """
    else:
        action_instruction = """
3. **ACTION (TEXT RETURN):** Return your complete analysis or response within the following tags:
   ```
   <source_code>
   (your full analysis or response here)
   </source_code>
   """

    prompt = f"""You are a specialist AI agent for software development. Your agent-specific \"brain\" is pre-loaded below.

**# YOUR AGENT BRAIN (PRE-LOADED CONTEXT)**

### PERSONA:
{agent_brain["persona"]}

### CONTEXT AND MISSION:
{agent_brain["context"]}

### PATTERNS TO AVOID (SCARS):
{agent_brain["avoid_patterns"]}

**# YOUR CURRENT TASK**

{task["instruction"]}

**Objective:** {task["details"]["objective"]}

**Steps to execute:**

1. **Analyze Context:** You are working in directory `{project_path}`. If reference files are provided below, read and analyze them to understand existing code patterns.
{reference_paths_str}

2. **Generate Response:** Create a complete response (analysis, code, etc.) following the requirements in your mission.

{action_instruction}

**Key Requirements:**
{chr(10).join([f"- {req}" for req in task["details"]["key_requirements"]])}

Execute the task now.
"""
    
    return prompt

def main():
    print("-" * 80)
    print("|🤖 FOCUSED GEMINI ORCHESTRATOR V1.0 🤖|")
    print("-" * 80)

    if len(sys.argv) < 2:
        print("❌ USAGE: python focused_gemini_orchestrator.py <agent_name> [project_path]")
        print("   Example: python focused_gemini_orchestrator.py QuotationReceiptService_IntegrationTest_Agent /mnt/ramdisk/develop/nex-web-backend")
        sys.exit(1)

    # Configuration
    agent_name = sys.argv[1]
    agent_path = f"/mnt/ramdisk/primoia-main/conductor/projects/develop/agents/{agent_name}"
    # Project path is optional, defaults to current dir if not provided
    project_path = sys.argv[2] if len(sys.argv) > 2 else "."
    project_path = os.path.abspath(project_path)

    print(f"📁 Agent: {agent_name}")
    print(f"📂 Project: {project_path}")

    # Load agent brain
    agent_brain = load_agent_brain(agent_path)
    if not agent_brain:
        sys.exit(1)

    # Build focused prompt
    prompt = build_focused_prompt(agent_brain, project_path)
    
    # Save prompt for analysis
    prompt_log_path = os.path.join(agent_path, "focused_prompt_gemini.txt")
    print(f"\n💾 Saving prompt to: {prompt_log_path}")
    with open(prompt_log_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    # Execute Gemini
    print(f"\n🚀 Executing Gemini from {project_path}...")
    try:
        # Using npx to run the Gemini CLI
        command = ["npx", "--yes", "@google/gemini-cli", "--prompt", prompt]
        process = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=300, 
            cwd=project_path
        )

        if process.returncode != 0:
            print("❌ GEMINI EXECUTION FAILED:", file=sys.stderr)
            print(process.stderr, file=sys.stderr)
            sys.exit(1)

        response = process.stdout.strip()
        print("  ✅ Gemini responded successfully")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Process Response
    print(f"\n🔍 Processing response...")
    if response == "[SAVE_SUCCESS]":
        print("  ✅ Gemini reported successful file creation!")
        target_file = agent_brain['task']['details'].get('target_file_to_create_content_for')
        if target_file:
            print(f"  📄 File should be at: {target_file}")
    else:
        print("  ℹ️ Extracting content from response...")
        code_match = re.search(r'<source_code>(.*?)</source_code>', response, re.DOTALL)
        if code_match:
            generated_content = code_match.group(1).strip()
            target_file = agent_brain['task']['details'].get('target_file_to_create_content_for')
            
            if target_file:
                try:
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(generated_content)
                    print(f"  ✅ File saved successfully: {target_file}")
                except Exception as e:
                    print(f"❌ FILE SAVE FAILED: {e}", file=sys.stderr)
                    # Still print the content if save fails
                    print(f"--- FULL GEMINI RESPONSE ---\n{generated_content}")
                    sys.exit(1)
            else:
                # If no target file, it's an analysis task, just print the output
                print("--- ANALYSIS RESULT ---")
                print(generated_content)
                print("-----------------------")

        else:
            print("❌ EXTRACTION FAILED: No <source_code> tag found")
            print(f"--- FULL GEMINI RESPONSE ---\n{response}")
            sys.exit(1)

    print("-" * 80)
    print("|🏁 FOCUSED GEMINI ORCHESTRATION V1.0 COMPLETED 🏁|")
    print("-" * 80)

if __name__ == "__main__":
    main()
