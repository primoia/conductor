#!/usr/bin/env python3
"""
Debug: Testar se Claude CLI pede autorização para executar Gradle
"""

import subprocess
import time

def test_claude_gradle_permissions():
    """Testa se Claude pede autorização para executar Gradle"""
    
    print("🔍 TESTE 1: Claude CLI com comando Gradle simples")
    
    prompt = """
I need to check if a Gradle project compiles.

Project path: /mnt/ramdisk/develop/nex-web-backend

Please analyze if running this command would work:
./gradlew compileTestKotlin --no-daemon

Don't actually execute it - just analyze the approach and tell me what would happen.
"""
    
    start_time = time.time()
    
    try:
        cmd = ["claude", "--print", prompt]
        print(f"⚡ Executando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Tempo: {execution_time:.1f}s")
        print(f"📤 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print(f"✅ SUCCESS")
            print(f"📄 Output (primeiras 300 chars):")
            print(result.stdout[:300] + "..." if len(result.stdout) > 300 else result.stdout)
        else:
            print(f"❌ FAILED")
            print(f"📄 Error: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT após 60s")
        print("🤔 Isso indica que Claude pode estar pedindo autorização interativa")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

def test_claude_simple_analysis():
    """Testa Claude com análise simples (sem comandos de execução)"""
    
    print("\n🔍 TESTE 2: Claude CLI com análise simples")
    
    prompt = """
Analyze this Kotlin test file structure and tell me if it looks correct:

class DateUtilsTest {
    @Test
    fun should_returnDate_when_validInput() {
        // test code
    }
}

Just analyze the structure - don't execute anything.
"""
    
    start_time = time.time()
    
    try:
        cmd = ["claude", "--print", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Tempo: {execution_time:.1f}s")
        print(f"📤 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print(f"✅ SUCCESS - Claude responde rapidamente para análise simples")
        else:
            print(f"❌ FAILED: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - Até análise simples está travando")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

def test_claude_with_bash_simulation():
    """Testa se Claude pede autorização para simular bash"""
    
    print("\n🔍 TESTE 3: Claude CLI simulando execução bash")
    
    prompt = """
I want to simulate running a Gradle command.

Command to simulate: ./gradlew compileTestKotlin --no-daemon

Please simulate what would happen if I ran this command in /mnt/ramdisk/develop/nex-web-backend

Do NOT actually execute anything - just tell me what the expected output would be.
"""
    
    start_time = time.time()
    
    try:
        cmd = ["claude", "--print", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️  Tempo: {execution_time:.1f}s")
        
        if result.returncode == 0:
            print(f"✅ SUCCESS - Claude pode simular comandos sem pedir autorização")
        else:
            print(f"❌ FAILED - Talvez Claude detecte intenção de execução")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - Claude trava quando vê comandos, mesmo para simulação")

if __name__ == "__main__":
    print("🧪 DEBUG: Claude CLI + Gradle Permissions")
    print("=" * 60)
    
    test_claude_simple_analysis()
    test_claude_gradle_permissions() 
    test_claude_with_bash_simulation()
    
    print("\n🎯 CONCLUSÃO:")
    print("Se TESTE 2 funciona mas TESTE 1 e 3 dão timeout,")
    print("então Claude pede autorização interativa para comandos de execução.")