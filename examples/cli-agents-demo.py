#!/usr/bin/env python3
"""
CLI Agents Demo - Using Claude and Gemini CLI for file processing
Demonstrates direct CLI integration with system commands
"""

import subprocess
import json
import time
import os
from pathlib import Path
from typing import Dict, Optional, List

class CLIAgentBase:
    """Base class for CLI-based agents"""
    
    def __init__(self, agent_name: str, cli_command: str):
        self.agent_name = agent_name
        self.cli_command = cli_command
        self.stats = {"executions": 0, "successes": 0, "total_time_ms": 0}
    
    def execute_task(self, task_params: Dict) -> Dict:
        """Execute task using CLI"""
        
        self.stats["executions"] += 1
        start_time = time.time()
        
        try:
            result = self._call_cli(task_params)
            end_time = time.time()
            
            self.stats["total_time_ms"] += int((end_time - start_time) * 1000)
            
            if result["status"] == "SUCCESS":
                self.stats["successes"] += 1
            
            return {
                **result,
                "agent_name": self.agent_name,
                "time_ms": int((end_time - start_time) * 1000)
            }
            
        except Exception as e:
            end_time = time.time()
            self.stats["total_time_ms"] += int((end_time - start_time) * 1000)
            
            return {
                "agent_name": self.agent_name,
                "status": "ERROR",
                "result": f"Exception: {str(e)}",
                "time_ms": int((end_time - start_time) * 1000)
            }
    
    def _call_cli(self, task_params: Dict) -> Dict:
        """Override in subclasses"""
        raise NotImplementedError
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        success_rate = (self.stats["successes"] / max(self.stats["executions"], 1)) * 100
        avg_time = self.stats["total_time_ms"] / max(self.stats["executions"], 1)
        
        return {
            **self.stats,
            "success_rate": f"{success_rate:.1f}%",
            "avg_time_ms": int(avg_time)
        }

class ClaudeAgent(CLIAgentBase):
    """Agent using Claude CLI for file analysis"""
    
    def __init__(self):
        super().__init__("claude-agent", "claude")
    
    def _call_cli(self, task_params: Dict) -> Dict:
        """Call Claude CLI with file analysis task"""
        
        file_path = task_params.get("file_path")
        task_type = task_params.get("task_type", "analyze")
        custom_prompt = task_params.get("prompt")
        
        if not file_path:
            return {"status": "ERROR", "result": "file_path is required"}
        
        # Build prompt based on task type
        if custom_prompt:
            prompt = custom_prompt.replace("{file_path}", file_path)
        else:
            prompts = {
                "gradle_version": f"Analyze this Gradle file and extract ONLY the version number: {file_path}",
                "security_scan": f"Scan this file for potential security vulnerabilities and respond with SECURE or VULNERABLE: {file_path}",
                "code_quality": f"Analyze code quality of this file and rate it 1-10: {file_path}",
                "test_count": f"Count the number of test methods in this file: {file_path}",
                "summarize": f"Provide a brief summary of this file's purpose: {file_path}",
                "analyze": f"Analyze this file and provide key insights: {file_path}"
            }
            prompt = prompts.get(task_type, prompts["analyze"])
        
        # Execute Claude CLI
        try:
            cmd = [
                "claude", 
                "--print", 
                "--dangerously-skip-permissions",
                prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return {
                    "status": "SUCCESS",
                    "result": output,
                    "confidence": 0.9,  # Claude is generally very reliable
                    "method": "claude_cli"
                }
            else:
                return {
                    "status": "ERROR",
                    "result": f"Claude CLI error: {result.stderr}",
                    "method": "claude_cli"
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "ERROR", "result": "Claude CLI timeout"}
        except Exception as e:
            return {"status": "ERROR", "result": f"Claude CLI exception: {str(e)}"}

class GeminiAgent(CLIAgentBase):
    """Agent using Gemini CLI for file analysis"""
    
    def __init__(self):
        super().__init__("gemini-agent", "npx https://github.com/google-gemini/gemini-cli")
    
    def _call_cli(self, task_params: Dict) -> Dict:
        """Call Gemini CLI with file analysis task"""
        
        file_path = task_params.get("file_path")
        task_type = task_params.get("task_type", "analyze")
        custom_prompt = task_params.get("prompt")
        
        if not file_path:
            return {"status": "ERROR", "result": "file_path is required"}
        
        # Gemini works better with relative paths from current directory
        try:
            current_dir = Path.cwd()
            target_path = Path(file_path)
            
            # Try to make relative path if possible
            if target_path.is_absolute():
                try:
                    relative_path = target_path.relative_to(current_dir)
                    file_path = str(relative_path)
                except ValueError:
                    # If can't make relative, use absolute but it might fail
                    pass
        except:
            pass
        
        # Build prompt based on task type
        if custom_prompt:
            prompt = custom_prompt.replace("{file_path}", file_path)
        else:
            prompts = {
                "gradle_version": f"Extract ONLY the Gradle version number from this file: {file_path}",
                "security_scan": f"Scan for security issues in {file_path} and respond SECURE or VULNERABLE",
                "code_quality": f"Rate code quality 1-10 for {file_path}",
                "test_count": f"Count test methods in {file_path}",
                "summarize": f"Summarize the main purpose of {file_path}",
                "analyze": f"Analyze {file_path} and provide key insights"
            }
            prompt = prompts.get(task_type, prompts["analyze"])
        
        # Execute Gemini CLI
        try:
            cmd = [
                "npx", 
                "https://github.com/google-gemini/gemini-cli",
                "--prompt",
                prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,  # Gemini might be slower
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Clean up Gemini output (remove loading messages, etc.)
                lines = output.split('\n')
                clean_lines = []
                for line in lines:
                    if not any(skip in line.lower() for skip in [
                        'error discovering', 'error connecting', 'loaded cached', 
                        'mcp error', 'jetbrains'
                    ]):
                        clean_lines.append(line)
                
                clean_output = '\n'.join(clean_lines).strip()
                
                return {
                    "status": "SUCCESS",
                    "result": clean_output,
                    "confidence": 0.85,  # Gemini is reliable but sometimes verbose
                    "method": "gemini_cli"
                }
            else:
                return {
                    "status": "ERROR",
                    "result": f"Gemini CLI error: {result.stderr}",
                    "method": "gemini_cli"
                }
                
        except subprocess.TimeoutExpired:
            return {"status": "ERROR", "result": "Gemini CLI timeout"}
        except Exception as e:
            return {"status": "ERROR", "result": f"Gemini CLI exception: {str(e)}"}

class MultiCLIOrchestrator:
    """Orchestrator that can use multiple CLI agents"""
    
    def __init__(self):
        self.claude_agent = ClaudeAgent()
        self.gemini_agent = GeminiAgent()
        self.agents = {
            "claude": self.claude_agent,
            "gemini": self.gemini_agent
        }
    
    def analyze_with_best_agent(self, task_params: Dict) -> Dict:
        """Choose best agent for task and execute"""
        
        task_type = task_params.get("task_type", "analyze")
        file_path = task_params.get("file_path", "")
        
        # Choose agent based on task characteristics
        chosen_agent = self._choose_agent(task_type, file_path)
        
        print(f"🤖 Using {chosen_agent.agent_name} for {task_type}")
        
        result = chosen_agent.execute_task(task_params)
        result["chosen_agent"] = chosen_agent.agent_name
        
        return result
    
    def analyze_with_both(self, task_params: Dict) -> Dict:
        """Run task with both agents and compare results"""
        
        print(f"🤖 Running with both Claude and Gemini...")
        
        # Run both in parallel (could be optimized with threading)
        claude_result = self.claude_agent.execute_task(task_params)
        gemini_result = self.gemini_agent.execute_task(task_params)
        
        return {
            "claude": claude_result,
            "gemini": gemini_result,
            "comparison": self._compare_results(claude_result, gemini_result)
        }
    
    def _choose_agent(self, task_type: str, file_path: str) -> CLIAgentBase:
        """Choose best agent based on task characteristics"""
        
        # Claude is generally better for:
        # - Code analysis, security scans, complex reasoning
        # - Files outside current directory (has --dangerously-skip-permissions)
        
        # Gemini is better for:
        # - Summarization, documentation
        # - Files within current workspace
        
        if task_type in ["security_scan", "code_quality", "gradle_version"]:
            return self.claude_agent
        elif task_type in ["summarize", "test_count"]:
            return self.gemini_agent
        else:
            # Default to Claude for complex analysis
            return self.claude_agent
    
    def _compare_results(self, claude_result: Dict, gemini_result: Dict) -> Dict:
        """Compare results from both agents"""
        
        comparison = {
            "both_succeeded": (claude_result.get("status") == "SUCCESS" and 
                             gemini_result.get("status") == "SUCCESS"),
            "claude_faster": claude_result.get("time_ms", 9999) < gemini_result.get("time_ms", 9999),
            "results_similar": False
        }
        
        if comparison["both_succeeded"]:
            claude_text = claude_result.get("result", "").lower().strip()
            gemini_text = gemini_result.get("result", "").lower().strip()
            
            # Simple similarity check
            comparison["results_similar"] = (
                claude_text == gemini_text or 
                claude_text in gemini_text or 
                gemini_text in claude_text
            )
        
        return comparison
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all agents"""
        return {
            "claude": self.claude_agent.get_stats(),
            "gemini": self.gemini_agent.get_stats()
        }

def demo_cli_agents():
    """Demonstrate CLI agents in action"""
    
    print("🚀 CLI AGENTS DEMO - CLAUDE & GEMINI")
    print("=" * 50)
    
    orchestrator = MultiCLIOrchestrator()
    
    # Test cases
    test_cases = [
        {
            "name": "Gradle Version Extraction",
            "params": {
                "file_path": "/mnt/ramdisk/primoia-main/codenoob-social-profile/gradle/wrapper/gradle-wrapper.properties",
                "task_type": "gradle_version"
            }
        },
        {
            "name": "Project Summary",
            "params": {
                "file_path": "README.md",
                "task_type": "summarize"
            }
        },
        {
            "name": "Custom Analysis",
            "params": {
                "file_path": "examples/simple-agent-demo.py",
                "task_type": "analyze",
                "prompt": "What design patterns are used in {file_path}? List them briefly."
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ TEST: {test_case['name']}")
        print("-" * 40)
        
        # Test with best agent
        result = orchestrator.analyze_with_best_agent(test_case["params"])
        
        print(f"   🤖 Agent: {result.get('chosen_agent', 'unknown')}")
        print(f"   📊 Status: {result.get('status', 'unknown')}")
        print(f"   ⏱️ Time: {result.get('time_ms', 0)}ms")
        print(f"   🎯 Result: {result.get('result', 'No result')[:100]}...")
        
        # For first test, also compare both agents
        if i == 1:
            print(f"\n   🔍 COMPARISON TEST:")
            comparison = orchestrator.analyze_with_both(test_case["params"])
            
            claude_time = comparison["claude"].get("time_ms", 0)
            gemini_time = comparison["gemini"].get("time_ms", 0)
            
            print(f"   Claude: {claude_time}ms - {comparison['claude'].get('status', 'unknown')}")
            print(f"   Gemini: {gemini_time}ms - {comparison['gemini'].get('status', 'unknown')}")
            print(f"   Similar results: {comparison['comparison']['results_similar']}")
    
    # Show final statistics
    print(f"\n📊 FINAL STATISTICS:")
    stats = orchestrator.get_all_stats()
    for agent_name, agent_stats in stats.items():
        print(f"   {agent_name.title()}: {agent_stats['success_rate']} success, {agent_stats['avg_time_ms']}ms avg")

if __name__ == "__main__":
    demo_cli_agents()
