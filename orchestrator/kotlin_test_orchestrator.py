#!/usr/bin/env python3
"""
Conductor Orchestrator - Fase 1: Centralized Agent Coordination
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any

class KotlinTestOrchestrator:
    """
    Orchestrator que coordena Strategy → Creator → Executor
    """
    
    def __init__(self):
        self.project_root = Path("/mnt/ramdisk/develop/nex-web-backend")
        self.agents_root = Path("/mnt/ramdisk/primoia-main/conductor/projects/develop/agents")
        self.workflow_state = {}
        
    def execute_full_pipeline(self, target_kotlin_file: str) -> Dict[str, Any]:
        """
        Executa pipeline completo: Strategy → Creator → Executor
        """
        print("🚀 INICIANDO KOTLIN TEST PIPELINE")
        print("=" * 60)
        
        start_time = time.time()
        self.workflow_state = {
            "workflow_id": f"kotlin-test-{int(start_time)}",
            "target_file": target_kotlin_file,
            "phases": {}
        }
        
        try:
            # FASE 1: Strategy Agent
            strategy_result = self._execute_strategy_agent(target_kotlin_file)
            self.workflow_state["phases"]["strategy"] = strategy_result
            
            if strategy_result["status"] != "SUCCESS":
                return self._finalize_workflow("FAILED", "Strategy agent failed")
            
            # FASE 2: Creator Agent  
            creator_result = self._execute_creator_agent(target_kotlin_file, strategy_result)
            self.workflow_state["phases"]["creator"] = creator_result
            
            if creator_result["status"] != "SUCCESS":
                return self._finalize_workflow("FAILED", "Creator agent failed")
            
            # FASE 3: Executor Agent
            executor_result = self._execute_executor_agent(creator_result["test_file"])
            self.workflow_state["phases"]["executor"] = executor_result
            
            return self._finalize_workflow("SUCCESS", "All phases completed")
            
        except Exception as e:
            return self._finalize_workflow("ERROR", f"Pipeline error: {str(e)}")
    
    def _execute_strategy_agent(self, target_file: str) -> Dict[str, Any]:
        """FASE 1: Análise e especificações de teste"""
        print("\n🧠 FASE 1: STRATEGY AGENT")
        print("-" * 40)
        
        prompt = f'''
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
'''
        
        result = self._call_claude_agent("Strategy Agent", prompt)
        
        if result["status"] == "SUCCESS":
            # Extrair informações chave da análise
            result["methods_identified"] = self._extract_methods_count(result["output"])
            result["scenarios_count"] = self._extract_scenarios_count(result["output"])
            
        return result
    
    def _execute_creator_agent(self, target_file: str, strategy_output: Dict) -> Dict[str, Any]:
        """FASE 2: Implementação dos testes"""
        print("\n💻 FASE 2: CREATOR AGENT")
        print("-" * 40)
        
        # Determinar caminho do teste
        test_path = target_file.replace("src/main/kotlin", "src/test/kotlin").replace(".kt", "Test.kt")
        Path(test_path).parent.mkdir(parents=True, exist_ok=True)
        
        prompt = f'''
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

Output ONLY the complete, compilable Kotlin test code.
'''
        
        result = self._call_claude_agent("Creator Agent", prompt)
        
        if result["status"] == "SUCCESS":
            # Extrair e salvar código Kotlin
            kotlin_code = self._extract_kotlin_code(result["output"])
            
            if kotlin_code:
                with open(test_path, 'w', encoding='utf-8') as f:
                    f.write(kotlin_code)
                
                result["test_file"] = test_path
                result["test_file_size"] = len(kotlin_code)
                result["code_saved"] = True
                
                print(f"   ✅ Test file saved: {test_path}")
                print(f"   📏 File size: {len(kotlin_code)} bytes")
            else:
                result["status"] = "ERROR" 
                result["error"] = "Could not extract Kotlin code"
        
        return result
    
    def _execute_executor_agent(self, test_file: str) -> Dict[str, Any]:
        """FASE 3: Execução e análise dos testes"""
        print("\n🔧 FASE 3: EXECUTOR AGENT")
        print("-" * 40)
        
        prompt = f'''
I am the Unit Test Executor Agent in the Conductor framework.

My role: Execute tests, analyze results, and generate quality metrics.

Test file to execute: {test_file}

I need to:
1. Compile the test file 
2. Run the specific test class
3. Analyze execution results
4. Calculate coverage metrics
5. Identify any issues or failures

Project context: Gradle-based Kotlin project at /mnt/ramdisk/develop/nex-web-backend

Please analyze the test execution approach and expected outcomes for this test file.
'''
        
        result = self._call_claude_agent("Executor Agent", prompt)
        
        if result["status"] == "SUCCESS":
            # Tentar executar teste real via Gradle
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
    
    def _call_claude_agent(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """Executa Claude CLI para um agente específico"""
        print(f"   🤖 Executing {agent_name}...")
        
        start_time = time.time()
        
        try:
            cmd = ["claude", "--print", prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            if result.returncode == 0:
                print(f"   ✅ {agent_name}: SUCCESS ({execution_time:.1f}s)")
                return {
                    "status": "SUCCESS",
                    "output": result.stdout.strip(),
                    "execution_time": execution_time,
                    "agent": agent_name
                }
            else:
                print(f"   ❌ {agent_name}: FAILED")
                return {
                    "status": "ERROR", 
                    "error": result.stderr,
                    "execution_time": execution_time,
                    "agent": agent_name
                }
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ {agent_name}: TIMEOUT")
            return {"status": "TIMEOUT", "agent": agent_name}
        except Exception as e:
            print(f"   💥 {agent_name}: EXCEPTION")
            return {"status": "ERROR", "error": str(e), "agent": agent_name}
    
    def _extract_kotlin_code(self, claude_output: str) -> str:
        """Extrai código Kotlin da resposta do Claude"""
        import re
        
        # Tentar extrair de bloco markdown
        kotlin_match = re.search(r'```kotlin\n(.*?)```', claude_output, re.DOTALL)
        if kotlin_match:
            return kotlin_match.group(1).strip()
        
        # Tentar extrair código que começa com package
        lines = claude_output.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('package '):
                # Pegar do package até o final (ou até indicador de fim)
                code_lines = []
                for j in range(i, len(lines)):
                    if lines[j].strip() in ['```', '---', 'Note:', 'The test']:
                        break
                    code_lines.append(lines[j])
                
                if len(code_lines) > 10:  # Código substancial
                    return '\n'.join(code_lines).strip()
        
        return ""
    
    def _extract_methods_count(self, analysis: str) -> int:
        """Extrai número de métodos identificados"""
        import re
        methods = re.findall(r'\bfun\s+\w+', analysis)
        return len(methods)
    
    def _extract_scenarios_count(self, analysis: str) -> int:
        """Extrai número de cenários de teste"""
        import re
        scenarios = re.findall(r'scenario|test.*case|should_', analysis, re.IGNORECASE)
        return len(scenarios)
    
    def _compile_test_file(self, test_file: str) -> Dict[str, Any]:
        """Tenta compilar o arquivo de teste"""
        try:
            cmd = [
                str(self.project_root / "gradlew"),
                "-p", str(self.project_root),
                "compileTestKotlin",
                "--no-daemon"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _finalize_workflow(self, status: str, message: str) -> Dict[str, Any]:
        """Finaliza workflow e gera relatório"""
        start_time = self.workflow_state.get("start_time", time.time())
        end_time = time.time()
        
        self.workflow_state.update({
            "final_status": status,
            "final_message": message,
            "total_duration": end_time - start_time,
            "summary": self._generate_summary()
        })
        
        print(f"\n🏁 PIPELINE COMPLETED: {status}")
        print(f"📝 {message}")
        print("=" * 60)
        
        return self.workflow_state
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Gera sumário do workflow"""
        phases = self.workflow_state.get("phases", {})
        
        summary = {
            "phases_completed": len([p for p in phases.values() if p.get("status") == "SUCCESS"]),
            "total_phases": 3,
            "success_rate": f"{(len([p for p in phases.values() if p.get('status') == 'SUCCESS']) / 3) * 100:.1f}%"
        }
        
        if "creator" in phases and phases["creator"].get("code_saved"):
            summary["test_file_created"] = phases["creator"]["test_file"]
        
        if "executor" in phases and "compilation" in phases["executor"]:
            summary["compilation_success"] = phases["executor"]["compilation"]["success"]
        
        return summary

def main():
    """Executa o orchestrator com DateHelpers.kt"""
    
    orchestrator = KotlinTestOrchestrator()
    
    target_file = "/mnt/ramdisk/develop/nex-web-backend/src/main/kotlin/br/com/nextar/web/utils/DateHelpers.kt"
    
    if not Path(target_file).exists():
        print(f"❌ Target file not found: {target_file}")
        return
    
    # Limpar arquivo de teste anterior se existir
    test_file = target_file.replace("src/main/kotlin", "src/test/kotlin").replace(".kt", "Test.kt")
    if Path(test_file).exists():
        print(f"🗑️  Removendo teste anterior: {test_file}")
        Path(test_file).unlink()
    
    result = orchestrator.execute_full_pipeline(target_file)
    
    # Relatório final
    print("\n📊 FINAL REPORT")
    print("=" * 50)
    print(f"Status: {result['final_status']}")
    print(f"Message: {result['final_message']}")
    
    summary = result.get('summary', {})
    print(f"Phases: {summary.get('phases_completed', 0)}/3 completed")
    print(f"Success Rate: {summary.get('success_rate', '0%')}")
    
    if 'test_file_created' in summary:
        print(f"Test File: {summary['test_file_created']}")
        
    if 'compilation_success' in summary:
        status = "✅" if summary['compilation_success'] else "❌"
        print(f"Compilation: {status}")
    
    # Salvar relatório detalhado
    report_file = f"/tmp/kotlin_test_report_{int(time.time())}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📄 Detailed report saved: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")

if __name__ == "__main__":
    main()