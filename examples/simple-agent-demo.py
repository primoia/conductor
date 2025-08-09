#!/usr/bin/env python3
"""
Simple Conductor Agent Demo
Demonstrates the core concept: Filesystem + Local Processing + DeepSeek
"""

import json
import requests
import re
import time
from pathlib import Path
from typing import Dict

class SimpleConductorAgent:
    """Simplified agent showing the core Conductor pattern"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model = "deepseek-coder-v2:16b"  # Can be upgraded to any model
    
    def analyze_project(self, project_path: str, task_type: str) -> Dict:
        """
        Core Conductor Pattern:
        1. Read from filesystem
        2. Process locally when possible  
        3. Use LLM for complex analysis
        4. Return structured result
        """
        
        print(f"🔍 {self.agent_name} analyzing: {project_path}")
        
        # STEP 1: READ FROM FILESYSTEM
        files_content = self._read_project_files(project_path, task_type)
        
        if not files_content:
            return self._error_result("No relevant files found")
        
        # STEP 2: LOCAL PROCESSING (fast, free, reliable)
        local_result = self._process_locally(files_content, task_type)
        
        if local_result["confidence"] >= 0.9:
            print(f"   ✅ Local processing sufficient: {local_result['result']}")
            return local_result
        
        # STEP 3: LLM ANALYSIS (when needed)
        print(f"   🤖 Using {self.model} for analysis...")
        llm_result = self._analyze_with_llm(files_content, task_type)
        
        # STEP 4: COMBINE RESULTS
        final_result = self._combine_results(local_result, llm_result, task_type)
        
        print(f"   🎯 Final result: {final_result['result']} ({final_result['confidence']:.0%})")
        return final_result
    
    def _read_project_files(self, project_path: str, task_type: str) -> Dict[str, str]:
        """Read relevant files based on task type"""
        
        files = {}
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            return {}
        
        # Define which files to read based on task type
        file_patterns = {
            "gradle_version": ["gradle/wrapper/gradle-wrapper.properties", "build.gradle*"],
            "test_status": ["src/test/**/*.java", "src/test/**/*.kt"],
            "security_check": ["src/**/*.java", "src/**/*.kt", "pom.xml", "build.gradle*"],
            "dependency_check": ["pom.xml", "build.gradle*", "package.json", "requirements.txt"]
        }
        
        patterns = file_patterns.get(task_type, ["**/*"])
        
        for pattern in patterns:
            for file_path in project_dir.glob(pattern):
                if file_path.is_file() and file_path.stat().st_size < 100000:  # Max 100KB
                    try:
                        files[str(file_path)] = file_path.read_text(encoding='utf-8')
                    except:
                        continue
                        
                if len(files) >= 5:  # Limit to avoid overload
                    break
        
        return files
    
    def _process_locally(self, files_content: Dict[str, str], task_type: str) -> Dict:
        """Fast local processing using regex/parsing"""
        
        if task_type == "gradle_version":
            return self._extract_gradle_version_locally(files_content)
        elif task_type == "test_status":
            return self._check_test_status_locally(files_content)
        elif task_type == "dependency_check":
            return self._check_dependencies_locally(files_content)
        else:
            return {"result": "UNKNOWN", "confidence": 0.0, "method": "local"}
    
    def _extract_gradle_version_locally(self, files_content: Dict[str, str]) -> Dict:
        """Extract Gradle version using regex"""
        
        for file_path, content in files_content.items():
            if "gradle-wrapper.properties" in file_path:
                # Look for: distributionUrl=.../gradle-7.4-bin.zip
                match = re.search(r'gradle-(\d+\.\d+(?:\.\d+)?)-(?:bin|all)\.zip', content)
                if match:
                    return {
                        "result": match.group(1),
                        "confidence": 0.95,
                        "method": "regex_local",
                        "source": "gradle-wrapper.properties"
                    }
        
        return {"result": "UNKNOWN", "confidence": 0.0, "method": "local"}
    
    def _check_test_status_locally(self, files_content: Dict[str, str]) -> Dict:
        """Check if tests exist using simple patterns"""
        
        test_count = 0
        for file_path, content in files_content.items():
            if "/test/" in file_path:
                # Count @Test annotations
                test_count += len(re.findall(r'@Test', content))
        
        if test_count > 0:
            return {
                "result": f"FOUND_{test_count}_TESTS",
                "confidence": 0.85,
                "method": "regex_local"
            }
        
        return {"result": "NO_TESTS_FOUND", "confidence": 0.7, "method": "local"}
    
    def _check_dependencies_locally(self, files_content: Dict[str, str]) -> Dict:
        """Check dependencies using simple parsing"""
        
        dependencies = []
        
        for file_path, content in files_content.items():
            if "pom.xml" in file_path:
                # Simple XML dependency extraction
                deps = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
                dependencies.extend(deps[:10])  # Limit to 10
            elif "build.gradle" in file_path:
                # Simple Gradle dependency extraction  
                deps = re.findall(r'implementation ["\']([^"\']+)["\']', content)
                dependencies.extend(deps[:10])
        
        if dependencies:
            return {
                "result": f"FOUND_{len(dependencies)}_DEPENDENCIES",
                "confidence": 0.8,
                "method": "regex_local",
                "details": dependencies[:5]  # Show first 5
            }
        
        return {"result": "NO_DEPENDENCIES_FOUND", "confidence": 0.6, "method": "local"}
    
    def _analyze_with_llm(self, files_content: Dict[str, str], task_type: str) -> Dict:
        """Use LLM for complex analysis"""
        
        # Prepare content for LLM (limit size)
        combined_content = self._prepare_content_for_llm(files_content, task_type)
        
        # Create task-specific prompts
        prompts = {
            "gradle_version": {
                "system": "You are a Gradle version extractor. Find the Gradle version number and respond with only the version (e.g., 7.4) or UNKNOWN.",
                "user": f"Extract Gradle version from:\n{combined_content}\nVersion:"
            },
            "test_status": {
                "system": "You are a test analyzer. Count the number of test methods and respond with TEST_COUNT_X or NO_TESTS.",
                "user": f"Count test methods in:\n{combined_content}\nResult:"
            },
            "security_check": {
                "system": "You are a security scanner. Look for common security issues and respond with SECURE or VULNERABLE_X_ISSUES.",
                "user": f"Scan for security issues:\n{combined_content}\nResult:"
            }
        }
        
        prompt = prompts.get(task_type, {
            "system": "You are a code analyzer. Analyze the code and provide a brief assessment.",
            "user": f"Analyze:\n{combined_content}\nResult:"
        })
        
        try:
            start_time = time.time()
            
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 20,
                    "stop": ["\n", "```"]
                }
            }, timeout=30)
            
            end_time = time.time()
            
            if response.status_code == 200:
                result_data = response.json()
                raw_result = result_data["message"]["content"].strip()
                
                return {
                    "result": raw_result,
                    "confidence": 0.8,
                    "method": "llm",
                    "time_ms": int((end_time - start_time) * 1000),
                    "model": self.model
                }
            else:
                return {"result": "LLM_ERROR", "confidence": 0.0, "method": "llm"}
                
        except Exception as e:
            return {"result": f"LLM_ERROR: {str(e)}", "confidence": 0.0, "method": "llm"}
    
    def _prepare_content_for_llm(self, files_content: Dict[str, str], task_type: str) -> str:
        """Prepare and limit content for LLM analysis"""
        
        relevant_content = []
        total_chars = 0
        max_chars = 2000  # Limit context size
        
        for file_path, content in files_content.items():
            file_name = Path(file_path).name
            
            # Add file header
            relevant_content.append(f"=== {file_name} ===")
            
            # Add content (truncated if needed)
            if total_chars + len(content) > max_chars:
                remaining = max_chars - total_chars
                content = content[:remaining] + "..."
                relevant_content.append(content)
                break
            else:
                relevant_content.append(content)
                total_chars += len(content)
        
        return "\n".join(relevant_content)
    
    def _combine_results(self, local_result: Dict, llm_result: Dict, task_type: str) -> Dict:
        """Combine local and LLM results intelligently"""
        
        # If local processing had high confidence, prefer it
        if local_result.get("confidence", 0) >= 0.9:
            return {**local_result, "strategy": "local_preferred"}
        
        # If LLM succeeded and local failed, use LLM
        if (llm_result.get("confidence", 0) > local_result.get("confidence", 0) and 
            "ERROR" not in llm_result.get("result", "")):
            return {**llm_result, "strategy": "llm_preferred"}
        
        # Default to local result
        return {**local_result, "strategy": "local_fallback"}
    
    def _error_result(self, message: str) -> Dict:
        """Standard error result format"""
        return {
            "result": "ERROR",
            "message": message,
            "confidence": 0.0,
            "method": "error"
        }

def demo_simple_conductor():
    """Demonstrate the simple Conductor agent"""
    
    print("🤖 SIMPLE CONDUCTOR AGENT DEMO")
    print("=" * 50)
    
    agent = SimpleConductorAgent("demo-agent")
    
    # Test different task types
    test_cases = [
        {
            "project": "/mnt/ramdisk/primoia-main/codenoob-social-profile",
            "task": "gradle_version",
            "description": "Extract Gradle version"
        },
        {
            "project": "/mnt/ramdisk/primoia-main/codenoob-social-profile", 
            "task": "dependency_check",
            "description": "Check project dependencies"
        },
        {
            "project": "/tmp/nonexistent",
            "task": "gradle_version", 
            "description": "Handle non-existent project"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ TEST: {test_case['description']}")
        print("-" * 30)
        
        result = agent.analyze_project(test_case["project"], test_case["task"])
        
        print(f"   📊 Result: {result.get('result', 'UNKNOWN')}")
        print(f"   🎯 Confidence: {result.get('confidence', 0):.0%}")
        print(f"   ⚙️ Method: {result.get('method', 'unknown')}")
        if result.get('time_ms'):
            print(f"   ⏱️ Time: {result['time_ms']}ms")

if __name__ == "__main__":
    demo_simple_conductor()

