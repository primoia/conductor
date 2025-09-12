#!/usr/bin/env python3
"""
Conductor Orchestrator - Phase 1: Centralized Agent Coordination
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any
import os


class KotlinTestOrchestrator:
    """
    Orchestrator that coordinates Strategy → Creator → Executor
    """

    def __init__(self):
        # These paths should ideally be configurable, e.g., via environment variables or CLI args
        self.project_root = Path(os.getenv("PROJECT_ROOT", "/tmp/desafio-meli"))
        self.agents_root = Path(
            os.getenv("AGENTS_ROOT", ".conductor_workspace/agents")
        )
        self.workflow_state = {}

    def execute_full_pipeline(self, target_kotlin_file: str) -> Dict[str, Any]:
        """
        Executes full pipeline: Strategy → Creator → Executor
        """
        print("🚀 STARTING KOTLIN TEST PIPELINE")
        print("=" * 60)

        start_time = time.time()
        self.workflow_state = {
            "workflow_id": f"kotlin-test-{int(start_time)}",
            "target_file": target_kotlin_file,
            "phases": {},
        }

        try:
            # PHASE 1: Strategy Agent
            strategy_result = self._execute_strategy_agent(target_kotlin_file)
            self.workflow_state["phases"]["strategy"] = strategy_result

            if strategy_result["status"] != "SUCCESS":
                return self._finalize_workflow("FAILED", "Strategy agent failed")

            # PHASE 2: Creator Agent
            creator_result = self._execute_creator_agent(
                target_kotlin_file, strategy_result
            )
            self.workflow_state["phases"]["creator"] = creator_result

            if creator_result["status"] != "SUCCESS":
                return self._finalize_workflow("FAILED", "Creator agent failed")

            # PHASE 3: Executor Agent
            executor_result = self._execute_executor_agent(creator_result["test_file"])
            self.workflow_state["phases"]["executor"] = executor_result

            return self._finalize_workflow("SUCCESS", "All phases completed")

        except Exception as e:
            return self._finalize_workflow("ERROR", f"Pipeline error: {str(e)}")

    def _execute_strategy_agent(self, target_file: str) -> Dict[str, Any]:
        """PHASE 1: Analysis and test specifications"""
        print("\n🧠 PHASE 1: STRATEGY AGENT")
        print("-" * 40)

        prompt = f"""
I am the Unit Test Strategy Agent in the Conductor framework.

My role: Analyze Kotlin classes and generate comprehensive test specifications.

Target class for analysis:
{open(target_file).read()}

Environment: develop (70% coverage threshold, moderate strictness)

Please analyze and provide:
1. All public methods requiring tests
2. Test scenarios (happy path + error cases)
3. Dependencies that need mocking
4. Expected coverage analysis

Output structured analysis covering all testable scenarios.
"""

        result = self._call_llm_agent("Strategy Agent", prompt)

        if result["status"] == "SUCCESS":
            # Extract key information from analysis
            result["methods_identified"] = self._extract_methods_count(result["output"])
            result["scenarios_count"] = self._extract_scenarios_count(result["output"])

        return result

    def _execute_creator_agent(
        self, target_file: str, strategy_output: Dict
    ) -> Dict[str, Any]:
        """PHASE 2: Test implementation"""
        print("\n💻 PHASE 2: CREATOR AGENT")
        print("-" * 40)

        # Determine test path
        test_path = target_file.replace("src/main/kotlin", "src/test/kotlin").replace(
            ".kt", "Test.kt"
        )
        Path(test_path).parent.mkdir(parents=True, exist_ok=True)

        prompt = f"""
I am the Kotlin Test Creator Agent in the Conductor framework.

My role: Transform test specifications into compilable Kotlin test code.

Based on strategy analysis:
{strategy_output["output"]}

Original class to test:
{open(target_file).read()}

Generate comprehensive JUnit 5 + AssertJ tests with:
- @Nested classes for organization
- Happy path + error scenarios  
- Clear naming: should_action_when_condition
- Proper imports and package declaration
- Edge cases and boundary testing

INSTRUCTIONS:
1. Try to save the test file directly to: {test_path}
2. If you cannot save the file, return the complete Kotlin code in a ```kotlin code block.

Do NOT use Gradle, IntelliJ, or build tools. Only create the test file.
"""

        result = self._call_llm_agent("Creator Agent", prompt)

        if result["status"] == "SUCCESS":
            # First, check if the agent created the file directly
            if Path(test_path).exists():
                # Agent used Write tool and created the file!
                file_size = Path(test_path).stat().st_size
                result["test_file"] = test_path
                result["test_file_size"] = file_size
                result["code_saved"] = True
                result["agent_used_write_tool"] = True

                print(f"   ✅ Test file created by agent: {test_path}")
                print(f"   📏 File size: {file_size} bytes")

            else:
                # Fallback: try to extract code from the response
                kotlin_code = self._extract_kotlin_code(result["output"])

                if kotlin_code and len(kotlin_code) > 100:  # Must be substantial
                    with open(test_path, "w", encoding="utf-8") as f:
                        f.write(kotlin_code)

                    result["test_file"] = test_path
                    result["test_file_size"] = len(kotlin_code)
                    result["code_saved"] = True
                    result["agent_used_write_tool"] = False

                    print(f"   ✅ Test file saved from extraction: {test_path}")
                    print(f"   📏 File size: {len(kotlin_code)} bytes")
                else:
                    result["status"] = "ERROR"
                    result["error"] = (
                        "Could not extract Kotlin code and no file was created"
                    )

        return result

    def _execute_executor_agent(self, test_file: str) -> Dict[str, Any]:
        """PHASE 3: Test execution and analysis"""
        print("\n🔧 PHASE 3: EXECUTOR AGENT")
        print("-" * 40)

        # Convert to project relative path
        relative_test_path = test_file.replace(str(self.project_root) + "/", "")

        prompt = f"""
I am the Unit Test Executor Agent in the Conductor framework.

My role: Execute tests, analyze results, and generate quality metrics.

Test file to analyze: {relative_test_path}

INSTRUCTIONS:
1. Try to execute the tests directly using Gradle if possible
2. If you cannot execute directly, provide analysis and recommendations

Project context: 
- This is a Gradle-based Kotlin project
- Test framework: JUnit 5 + AssertJ
- Environment: develop (70% coverage threshold)

Tasks to perform:
- Check if the test file compiles
- Analyze test structure and quality
- Assess coverage completeness
- Execute tests if possible, otherwise recommend execution approach

Do NOT use IntelliJ or IDE integrations. Use command line tools.
"""

        result = self._call_llm_agent("Executor Agent", prompt)

        if result["status"] == "SUCCESS":
            # Try to execute real test via Gradle
            try:
                compile_result = self._compile_test_file(test_file)
                result["compilation"] = compile_result

                if compile_result["success"]:
                    print(f"   ✅ Test compilation: SUCCESS")
                else:
                    print(f"   ⚠️ Test compilation: {compile_result['output']}")

            except Exception as e:
                result["compilation"] = {"success": False, "error": str(e)}

        return result

    def _call_llm_agent(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """Executes LLM CLI for a specific agent"""
        print(f"   🤖 Executing {agent_name}...")

        start_time = time.time()

        try:
            # This part needs to be generalized to use the Conductor's LLM client
            # For now, it's a placeholder for calling an LLM agent
            # Example: using a subprocess call to src/cli/agent.py or a direct LLM API call
            # For demonstration, let's simulate a successful call
            # In a real scenario, this would involve calling the Conductor's agent CLI
            # e.g., subprocess.run(["poetry", "run", "python", "src/cli/agent.py", "--agent", agent_name, "--input", prompt], ...)

            # Placeholder for actual LLM call
            simulated_output = f"Simulated output for {agent_name} with prompt: {prompt}"
            simulated_status = "SUCCESS"

            end_time = time.time()
            execution_time = end_time - start_time

            if simulated_status == "SUCCESS":
                print(f"   ✅ {agent_name}: SUCCESS ({execution_time:.1f}s)")
                return {
                    "status": "SUCCESS",
                    "output": simulated_output,
                    "execution_time": execution_time,
                    "agent": agent_name,
                }
            else:
                print(f"   ❌ {agent_name}: FAILED")
                return {
                    "status": "ERROR",
                    "error": "Simulated error",
                    "execution_time": execution_time,
                    "agent": agent_name,
                }

        except subprocess.TimeoutExpired:
            print(f"   ⏰ {agent_name}: TIMEOUT")
            return {"status": "TIMEOUT", "agent": agent_name}
        except Exception as e:
            print(f"   💥 {agent_name}: EXCEPTION")
            return {"status": "ERROR", "error": str(e), "agent": agent_name}

    def _extract_kotlin_code(self, llm_output: str) -> str:
        """Extracts Kotlin code from LLM response"""
        import re

        # Try to extract from markdown block
        kotlin_match = re.search(r"```kotlin\n(.*?)```", llm_output, re.DOTALL)
        if kotlin_match:
            return kotlin_match.group(1).strip()

        # Try to extract code that starts with package
        lines = llm_output.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith("package "):
                # Get from package until end (or until end indicator)
                code_lines = []
                for j in range(i, len(lines)):
                    if lines[j].strip() in ["```", "---", "Note:", "The test"]:
                        break
                    code_lines.append(lines[j])

                if len(code_lines) > 10:  # Substantial code
                    return "\n".join(code_lines).strip()

        return ""

    def _extract_methods_count(self, analysis: str) -> int:
        """Extracts number of identified methods"""
        import re

        methods = re.findall(r"\bfun\s+\w+", analysis)
        return len(methods)

    def _extract_scenarios_count(self, analysis: str) -> int:
        """Extracts number of test scenarios"""
        import re

        scenarios = re.findall(r"scenario|test.*case|should_", analysis, re.IGNORECASE)
        return len(scenarios)

    def _compile_test_file(self, test_file: str) -> Dict[str, Any]:
        """Tries to compile the test file"""
        try:
            cmd = [
                str(self.project_root / "gradlew"),
                "-p",
                str(self.project_root),
                "compileTestKotlin",
                "--no-daemon",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            return {
                "success": result.returncode == 0,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "command": " ".join(cmd),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _finalize_workflow(self, status: str, message: str) -> Dict[str, Any]:
        """Finalizes workflow and generates report"""
        start_time = self.workflow_state.get("start_time", time.time())
        end_time = time.time()

        self.workflow_state.update(
            {
                "final_status": status,
                "final_message": message,
                "total_duration": end_time - start_time,
                "summary": self._generate_summary(),
            }
        )

        print(f"\n🏁 PIPELINE COMPLETED: {status}")
        print(f"📝 {message}")
        print("=" * 60)

        return self.workflow_state

    def _generate_summary(self) -> Dict[str, Any]:
        """Generates workflow summary"""
        phases = self.workflow_state.get("phases", {})

        summary = {
            "phases_completed": len(
                [p for p in phases.values() if p.get("status") == "SUCCESS"]
            ),
            "total_phases": 3,
            "success_rate": f"{(len([p for p in phases.values() if p.get('status') == 'SUCCESS']) / 3) * 100:.1f}%",
        }

        if "creator" in phases and phases["creator"].get("code_saved"):
            summary["test_file_created"] = phases["creator"]["test_file"]

        if "executor" in phases and "compilation" in phases["executor"]:
            summary["compilation_success"] = phases["executor"]["compilation"][
                "success"
            ]

        return summary


def main():
    """Executes the orchestrator with DateHelpers.kt"""

    orchestrator = KotlinTestOrchestrator()

    target_file = os.getenv("TARGET_KOTLIN_FILE", "/tmp/DateHelpers.kt")

    if not Path(target_file).exists():
        print(f"❌ Target file not found: {target_file}")
        return

    # Clean up previous test file if exists
    test_file = target_file.replace("src/main/kotlin", "src/test/kotlin").replace(
        ".kt", "Test.kt"
    )
    if Path(test_file).exists():
        print(f"🗑️  Removing previous test: {test_file}")
        Path(test_file).unlink()

    result = orchestrator.execute_full_pipeline(target_file)

    # Final report
    print("\n📊 FINAL REPORT")
    print("=" * 50)
    print(f"Status: {result['final_status']}")
    print(f"Message: {result['final_message']}")

    summary = result.get("summary", {})
    print(f"Phases: {summary.get('phases_completed', 0)}/3 completed")
    print(f"Success Rate: {summary.get('success_rate', '0%')}")

    if "test_file_created" in summary:
        print(f"Test File: {summary['test_file_created']}")

    if "compilation_success" in summary:
        status = "✅" if summary["compilation_success"] else "❌"
        print(f"Compilation: {status}")

    # Save detailed report
    report_file = f"/tmp/kotlin_test_report_{int(time.time())}.json"
    try:
        with open(report_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📄 Detailed report saved: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")


if __name__ == "__main__":
    main()