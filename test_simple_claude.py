#!/usr/bin/env python3
"""
Test Claude com prompts progressivamente mais simples
"""

import subprocess
import time
from pathlib import Path

def test_claude_simple():
    """Teste 1: Prompt super simples"""
    
    print("🔍 TESTE 1: Prompt super simples")
    
    prompt = "What is 2+2?"
    
    try:
        cmd = ["claude", "--print", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {result.stdout.strip()}")
        else:
            print(f"❌ FAILED: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - até matemática simples trava")

def test_claude_with_cd():
    """Teste 2: Prompt simples com CD"""
    
    print("\n🔍 TESTE 2: Prompt simples com CD")
    
    project_root = "/mnt/ramdisk/develop/nex-web-backend"
    prompt = "List the files in this directory."
    
    try:
        cmd = f"cd {project_root} && claude --print '{prompt}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Claude pode acessar arquivos com CD")
            print(f"📄 Output: {result.stdout[:200]}...")
        else:
            print(f"❌ FAILED: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - CD + file access trava")

def test_claude_kotlin_analysis():
    """Teste 3: Análise de arquivo Kotlin específico"""
    
    print("\n🔍 TESTE 3: Análise Kotlin específica")
    
    project_root = "/mnt/ramdisk/develop/nex-web-backend"
    prompt = "Analyze the file src/test/kotlin/br/com/nextar/web/utils/DateHelpersTest.kt if it exists."
    
    try:
        cmd = f"cd {project_root} && claude --print '{prompt}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=45)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Claude pode analisar arquivos Kotlin")
            print(f"📄 Output: {result.stdout[:200]}...")
        else:
            print(f"❌ FAILED: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - análise de arquivo específico trava")

def test_claude_role_based():
    """Teste 4: Prompt com role (como no orchestrator)"""
    
    print("\n🔍 TESTE 4: Prompt com role-based approach")
    
    project_root = "/mnt/ramdisk/develop/nex-web-backend"
    prompt = """I am a test analysis agent. 

Please analyze the project structure and tell me:
1. If this is a Gradle project
2. What test frameworks are used
3. Basic recommendations

Keep the response brief."""
    
    try:
        cmd = f"cd {project_root} && claude --print '{prompt}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Role-based prompts funcionam")
            print(f"📄 Output: {result.stdout[:300]}...")
        else:
            print(f"❌ FAILED: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - role-based analysis trava")

if __name__ == "__main__":
    print("🧪 DEBUG: Claude CLI Progressive Testing")
    print("=" * 60)
    
    test_claude_simple()
    test_claude_with_cd()
    test_claude_kotlin_analysis()
    test_claude_role_based()
    
    print("\n🎯 CONCLUSÃO:")
    print("Se só o primeiro teste funciona, o problema é file access.")
    print("Se nenhum funciona, o problema é o Claude CLI em si.")