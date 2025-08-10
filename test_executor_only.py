#!/usr/bin/env python3
"""
Test apenas o Executor Agent com CD approach
"""

import subprocess
import time
from pathlib import Path

def test_executor_with_cd():
    """Testa Executor Agent com cd para projeto"""
    
    project_root = Path("/mnt/ramdisk/develop/nex-web-backend")
    
    prompt = '''
I am the Unit Test Executor Agent in the Conductor framework.

My role: Execute tests, analyze results, and generate quality metrics.

Test file to analyze: src/test/kotlin/br/com/nextar/web/utils/DateHelpersTest.kt

I need to:
1. Check if the test file exists and analyze its structure  
2. Assess the project structure (build.gradle, dependencies)
3. Recommend compilation approach
4. Provide quality assessment

Project context: 
- This is a Gradle-based Kotlin project
- Test framework: JUnit 5 + AssertJ
- Environment: develop (70% coverage threshold)

Please analyze the test file and project structure to provide compilation recommendations.
You can access project files to understand the context.
'''
    
    print("🔍 TESTE: Executor Agent com CD approach")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # CD para o projeto antes de chamar Claude (padrão Gemini)
        cmd = f"cd {project_root} && claude --print '{prompt.replace(chr(39), chr(34))}'"
        print(f"⚡ Executando: cd {project_root} && claude --print [prompt]")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Tempo: {execution_time:.1f}s")
        print(f"📤 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print(f"✅ SUCCESS!")
            print(f"📄 Output (primeiras 400 chars):")
            print(result.stdout[:400] + "..." if len(result.stdout) > 400 else result.stdout)
        else:
            print(f"❌ FAILED")
            print(f"📄 Error: {result.stderr[:300]}")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT após 60s - ainda trava mesmo com CD")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

if __name__ == "__main__":
    test_executor_with_cd()