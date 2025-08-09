#!/usr/bin/env python3
"""
Smart CLI Conductor - Optimal routing between Claude/Gemini/DeepSeek
Combines the best of all three approaches for maximum efficiency
"""

import subprocess
import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Optional

class SmartCLIConductor:
    """Intelligent conductor that routes tasks to optimal LLM"""
    
    def __init__(self):
        self.stats = {
            "claude": {"calls": 0, "successes": 0, "total_time": 0},
            "gemini": {"calls": 0, "successes": 0, "total_time": 0},
            "deepseek": {"calls": 0, "successes": 0, "total_time": 0}
        }
        self.ollama_url = "http://localhost:11434/api/chat"
        self.deepseek_model = "deepseek-coder-v2:16b"
    
    def process_file(self, file_path: str, task_type: str, custom_prompt: str = None) -> Dict:
        """
        Smart routing: Choose optimal LLM based on task and file characteristics
        
        Routing Logic:
        1. DeepSeek Local: Simple extraction, fast tasks, privacy-sensitive
        2. Claude CLI: Complex analysis, external files, code review
        3. Gemini CLI: Summarization, local files, documentation
        """
        
        print(f"🧠 Smart routing for: {Path(file_path).name} ({task_type})")
        
        # STEP 1: Analyze task characteristics
        routing_decision = self._analyze_routing_decision(file_path, task_type, custom_prompt)
        
        print(f"   🎯 Chosen: {routing_decision['chosen_llm']} ({routing_decision['reason']})")
        
        # STEP 2: Execute with chosen LLM
        start_time = time.time()
        
        if routing_decision["chosen_llm"] == "deepseek":
            result = self._process_with_deepseek(file_path, task_type, custom_prompt)
        elif routing_decision["chosen_llm"] == "claude":
            result = self._process_with_claude(file_path, task_type, custom_prompt)
        elif routing_decision["chosen_llm"] == "gemini":
            result = self._process_with_gemini(file_path, task_type, custom_prompt)
        else:
            result = {"status": "ERROR", "result": "Unknown LLM choice"}
        
        end_time = time.time()
        total_time = int((end_time - start_time) * 1000)
        
        # STEP 3: Update stats and add metadata
        llm_name = routing_decision["chosen_llm"]
        self.stats[llm_name]["calls"] += 1
        self.stats[llm_name]["total_time"] += total_time
        
        if result.get("status") == "SUCCESS":
            self.stats[llm_name]["successes"] += 1
        
        result.update({
            "chosen_llm": llm_name,
            "routing_reason": routing_decision["reason"],
            "total_time_ms": total_time,
            "cost_estimate": routing_decision["cost_estimate"]
        })
        
        print(f"   ✅ Result: {result.get('result', 'Error')[:60]}...")
        print(f"   ⏱️ Time: {total_time}ms | 💰 Cost: {result['cost_estimate']}")
        
        return result
    
    def _analyze_routing_decision(self, file_path: str, task_type: str, custom_prompt: str) -> Dict:
        """Analyze task and decide which LLM to use"""
        
        file_path_obj = Path(file_path)
        is_local = self._is_file_local(file_path)
        file_size = self._get_file_size(file_path)
        
        # ROUTING RULES:
        
        # 1. DeepSeek Local (Priority: Fast, Free, Private)
        if (task_type in ["gradle_version", "test_count", "dependency_check"] and 
            file_size < 50000):  # < 50KB
            return {
                "chosen_llm": "deepseek",
                "reason": "simple_extraction_task",
                "cost_estimate": "$0.00"
            }
        
        # 2. Claude CLI (Priority: Complex Analysis, External Files)
        if (task_type in ["security_scan", "code_quality", "analyze"] or 
            not is_local or 
            custom_prompt):
            return {
                "chosen_llm": "claude", 
                "reason": "complex_analysis_or_external_file",
                "cost_estimate": "$0.02"
            }
        
        # 3. Gemini CLI (Priority: Local Documentation, Summarization)
        if (task_type in ["summarize", "documentation"] and 
            is_local and 
            file_size < 100000):  # < 100KB
            return {
                "chosen_llm": "gemini",
                "reason": "local_documentation_task", 
                "cost_estimate": "$0.01"
            }
        
        # Default: Claude (most reliable)
        return {
            "chosen_llm": "claude",
            "reason": "default_fallback",
            "cost_estimate": "$0.02"
        }
    
    def _is_file_local(self, file_path: str) -> bool:
        """Check if file is in current workspace"""
        try:
            current_dir = Path.cwd()
            target_path = Path(file_path).resolve()
            return current_dir in target_path.parents or current_dir == target_path.parent
        except:
            return False
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size safely"""
        try:
            return Path(file_path).stat().st_size
        except:
            return 0
    
    def _process_with_deepseek(self, file_path: str, task_type: str, custom_prompt: str) -> Dict:
        """Process with local DeepSeek via Ollama"""
        
        try:
            # Read file content
            content = Path(file_path).read_text(encoding='utf-8')[:2000]  # Limit size
            
            # Build task-specific prompt
            if custom_prompt:
                user_prompt = custom_prompt.replace("{file_path}", file_path)
                system_prompt = "You are a helpful code assistant. Be concise and accurate."
            else:
                prompts = {
                    "gradle_version": {
                        "system": "Extract Gradle version numbers. Respond with only the version (e.g., 7.4) or UNKNOWN.",
                        "user": f"Extract Gradle version from:\n{content}\nVersion:"
                    },
                    "test_count": {
                        "system": "Count test methods. Respond with only the number or 0.",
                        "user": f"Count @Test methods in:\n{content}\nCount:"
                    },
                    "dependency_check": {
                        "system": "List dependencies. Be concise.",
                        "user": f"List main dependencies from:\n{content}\nDependencies:"
                    }
                }
                
                prompt_config = prompts.get(task_type, {
                    "system": "Analyze the code and provide brief insights.",
                    "user": f"Analyze:\n{content}\nInsights:"
                })
                
                system_prompt = prompt_config["system"]
                user_prompt = prompt_config["user"]
            
            # Call DeepSeek via Ollama
            response = requests.post(self.ollama_url, json={
                "model": self.deepseek_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 50
                }
            }, timeout=20)
            
            if response.status_code == 200:
                result_data = response.json()
                raw_result = result_data["message"]["content"].strip()
                
                return {
                    "status": "SUCCESS",
                    "result": raw_result,
                    "confidence": 0.85,
                    "method": "deepseek_local"
                }
            else:
                return {"status": "ERROR", "result": f"DeepSeek API error: {response.status_code}"}
                
        except Exception as e:
            return {"status": "ERROR", "result": f"DeepSeek error: {str(e)}"}
    
    def _process_with_claude(self, file_path: str, task_type: str, custom_prompt: str) -> Dict:
        """Process with Claude CLI"""
        
        try:
            if custom_prompt:
                prompt = custom_prompt.replace("{file_path}", file_path)
            else:
                prompts = {
                    "gradle_version": f"Analyze this Gradle file and extract ONLY the version number: {file_path}",
                    "security_scan": f"Scan for security vulnerabilities and respond SECURE or VULNERABLE: {file_path}",
                    "code_quality": f"Rate code quality 1-10 with brief explanation: {file_path}",
                    "analyze": f"Provide key insights about this code: {file_path}",
                    "summarize": f"Summarize the main purpose of: {file_path}"
                }
                prompt = prompts.get(task_type, prompts["analyze"])
            
            cmd = ["claude", "--print", "--dangerously-skip-permissions", prompt]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "result": result.stdout.strip(),
                    "confidence": 0.9,
                    "method": "claude_cli"
                }
            else:
                return {"status": "ERROR", "result": f"Claude error: {result.stderr}"}
                
        except Exception as e:
            return {"status": "ERROR", "result": f"Claude exception: {str(e)}"}
    
    def _process_with_gemini(self, file_path: str, task_type: str, custom_prompt: str) -> Dict:
        """Process with Gemini CLI - changes directory for better file access"""
        
        try:
            original_dir = Path.cwd()
            target_path = Path(file_path)
            
            # Determine best working directory and relative path
            if target_path.is_absolute():
                if target_path.exists():
                    # Change to file's directory for better access
                    work_dir = target_path.parent
                    relative_file = target_path.name
                else:
                    # File doesn't exist, use original directory
                    work_dir = original_dir
                    relative_file = str(target_path)
            else:
                # Relative path, use current directory
                work_dir = original_dir
                relative_file = file_path
            
            if custom_prompt:
                prompt = custom_prompt.replace("{file_path}", relative_file)
            else:
                prompts = {
                    "summarize": f"Provide a concise summary of: {relative_file}",
                    "documentation": f"Explain what this file does: {relative_file}",
                    "analyze": f"Analyze and explain: {relative_file}"
                }
                prompt = prompts.get(task_type, prompts["analyze"])
            
            # Use shell command with cd for better directory handling
            cmd = f"cd '{work_dir}' && npx https://github.com/google-gemini/gemini-cli --prompt '{prompt}'"
            
            result = subprocess.run(
                cmd, 
                shell=True,  # Use shell to handle cd command
                capture_output=True, 
                text=True, 
                timeout=40
            )
            
            if result.returncode == 0:
                # Clean Gemini output
                output = result.stdout.strip()
                lines = [line for line in output.split('\n') 
                        if not any(skip in line.lower() for skip in [
                            'error discovering', 'error connecting', 'loaded cached',
                            'mcp error', 'jetbrains'
                        ])]
                clean_output = '\n'.join(lines).strip()
                
                return {
                    "status": "SUCCESS",
                    "result": clean_output,
                    "confidence": 0.8,
                    "method": "gemini_cli",
                    "work_dir": str(work_dir),
                    "relative_file": relative_file
                }
            else:
                return {"status": "ERROR", "result": f"Gemini error: {result.stderr}"}
                
        except Exception as e:
            return {"status": "ERROR", "result": f"Gemini exception: {str(e)}"}
    
    def get_performance_report(self) -> Dict:
        """Generate performance report for all LLMs"""
        
        report = {}
        
        for llm_name, stats in self.stats.items():
            if stats["calls"] > 0:
                success_rate = (stats["successes"] / stats["calls"]) * 100
                avg_time = stats["total_time"] / stats["calls"]
                
                report[llm_name] = {
                    "calls": stats["calls"],
                    "success_rate": f"{success_rate:.1f}%",
                    "avg_time_ms": int(avg_time),
                    "total_time_ms": stats["total_time"]
                }
            else:
                report[llm_name] = {"calls": 0, "success_rate": "0%", "avg_time_ms": 0}
        
        return report

def demo_smart_cli_conductor():
    """Demonstrate the smart CLI conductor"""
    
    print("🧠 SMART CLI CONDUCTOR DEMO")
    print("=" * 50)
    print("Intelligent routing: DeepSeek (free) → Claude (powerful) → Gemini (local)")
    
    conductor = SmartCLIConductor()
    
    # Test cases designed to trigger different routing decisions
    test_cases = [
        {
            "name": "Simple Gradle Version (→ DeepSeek)",
            "file_path": "/mnt/ramdisk/primoia-main/codenoob-social-profile/gradle/wrapper/gradle-wrapper.properties",
            "task_type": "gradle_version"
        },
        {
            "name": "Complex Code Analysis (→ Claude)",
            "file_path": "examples/simple-agent-demo.py",
            "task_type": "analyze"
        },
        {
            "name": "Local Documentation (→ Gemini)",
            "file_path": "README.md",
            "task_type": "summarize"
        },
        {
            "name": "Security Scan (→ Claude)",
            "file_path": "examples/cli-agents-demo.py",
            "task_type": "security_scan"
        },
        {
            "name": "Custom Analysis (→ Claude)",
            "file_path": "examples/simple-agent-demo.py",
            "task_type": "custom",
            "custom_prompt": "What are the main classes and their responsibilities in {file_path}?"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}")
        print("-" * 50)
        
        result = conductor.process_file(
            file_path=test_case["file_path"],
            task_type=test_case["task_type"],
            custom_prompt=test_case.get("custom_prompt")
        )
        
        print(f"   📊 Status: {result.get('status', 'unknown')}")
        print(f"   🎯 Confidence: {result.get('confidence', 0):.0%}")
    
    # Performance report
    print(f"\n📊 PERFORMANCE REPORT:")
    print("-" * 30)
    report = conductor.get_performance_report()
    
    for llm_name, stats in report.items():
        if stats["calls"] > 0:
            print(f"   {llm_name.title():>8}: {stats['calls']} calls, {stats['success_rate']} success, {stats['avg_time_ms']}ms avg")
        else:
            print(f"   {llm_name.title():>8}: Not used")
    
    # Cost analysis
    total_estimated_cost = sum([
        0.00 * report["deepseek"]["calls"],  # Free local
        0.02 * report["claude"]["calls"],    # Estimated Claude API cost
        0.01 * report["gemini"]["calls"]     # Estimated Gemini API cost
    ])
    
    print(f"\n💰 ESTIMATED TOTAL COST: ${total_estimated_cost:.3f}")
    print(f"   (vs all-Claude: ${0.02 * sum(stats['calls'] for stats in report.values()):.3f})")

if __name__ == "__main__":
    demo_smart_cli_conductor()
