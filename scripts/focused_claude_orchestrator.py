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
    reference_files = task["details"]["reference_files_to_read"]
    target_file = task["details"]["target_file_to_create_content_for"]
    
    # Convert absolute paths to relative paths for the prompt
    relative_paths = []
    for abs_path in reference_files:
        if project_path in abs_path:
            rel_path = abs_path.replace(project_path + "/", "")
            relative_paths.append(rel_path)
        else:
            relative_paths.append(abs_path)  # Keep as-is if not within project
    
    reference_paths_str = '\n'.join([f"- {path}" for path in relative_paths])
    
    prompt = f"""You are a specialist AI agent for software development. Your agent-specific "brain" is pre-loaded below.

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

1. **Read Reference Files:** You are working in directory `{project_path}`. Read and analyze these files to understand existing code patterns:
{reference_paths_str}

2. **Generate Code:** Create complete Kotlin content for the integration test file following the requirements in your mission.

3. **PRIMARY ACTION (DIRECT SAVE):** Try to save the generated code directly to: `{target_file}`
   If successful, respond with ONLY: `[SAVE_SUCCESS]`

4. **FALLBACK ACTION (TEXT RETURN):** If you cannot save the file, return the complete source code within:
   ```
   <source_code>
   (complete kotlin code here)
   </source_code>
   ```

**Key Requirements:**
{chr(10).join([f"- {req}" for req in task["details"]["key_requirements"]])}

Execute the task now.
"""
    
    return prompt

def main():
    print("-" * 80)
    print("|🤖 FOCUSED CLAUDE ORCHESTRATOR V6.0 🤖|")
    print("-" * 80)

    # Configuration
    agent_name = "QuotationReceiptService_IntegrationTest_Agent"
    agent_path = f"/mnt/ramdisk/primoia-main/conductor/projects/develop/agents/{agent_name}"
    project_path = "/mnt/ramdisk/develop/nex-web-backend"
    
    print(f"📁 Agent: {agent_name}")
    print(f"📂 Project: {project_path}")

    # Load agent brain (ONLY agent-specific files)
    agent_brain = load_agent_brain(agent_path)
    if not agent_brain:
        sys.exit(1)

    # Build focused prompt
    prompt = build_focused_prompt(agent_brain, project_path)
    
    # Save prompt for analysis
    prompt_log_path = os.path.join(agent_path, "focused_prompt.txt")
    print(f"\n💾 Saving prompt to: {prompt_log_path}")
    with open(prompt_log_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    # Execute Claude
    print(f"\n🚀 Executing Claude from {project_path}...")
    try:
        command = ["claude", "--print", "--dangerously-skip-permissions", prompt]
        process = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=300, 
            cwd=project_path
        )

        if process.returncode != 0:
            print("❌ CLAUDE EXECUTION FAILED:", file=sys.stderr)
            print(process.stderr, file=sys.stderr)
            sys.exit(1)

        response = process.stdout.strip()
        print("  ✅ Claude responded successfully")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Process Response
    print(f"\n🔍 Processing response...")
    if response == "[SAVE_SUCCESS]":
        print("  ✅ Claude reported successful file creation!")
        print(f"  📄 File created: {agent_brain['task']['details']['target_file_to_create_content_for']}")
    else:
        print("  ℹ️ Using fallback: extracting code from response...")
        code_match = re.search(r'<source_code>(.*?)</source_code>', response, re.DOTALL)
        if code_match:
            generated_code = code_match.group(1).strip()
            target_file = agent_brain['task']['details']['target_file_to_create_content_for']
            try:
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(generated_code)
                print(f"  ✅ File saved successfully: {target_file}")
            except Exception as e:
                print(f"❌ FILE SAVE FAILED: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("❌ FALLBACK FAILED: No <source_code> tag found")
            print(f"--- FULL CLAUDE RESPONSE ---\n{response}")
            sys.exit(1)

    print("-" * 80)
    print("|🏁 FOCUSED ORCHESTRATION V6.0 COMPLETED 🏁|")
    print("-" * 80)

if __name__ == "__main__":
    main()