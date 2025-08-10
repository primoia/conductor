#!/usr/bin/env python3
"""
Test Gemini CLI integration
"""

import subprocess
import time
from pathlib import Path

def test_gemini_simple():
    """Teste 1: Gemini CLI básico"""
    
    print("🔍 TESTE 1: Gemini CLI básico")
    
    try:
        cmd = "npx https://github.com/google-gemini/gemini-cli --prompt 'What is 2+2?'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Gemini CLI funciona")
            print(f"📄 Output: {result.stdout[:200]}...")
        else:
            print(f"❌ FAILED: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - Gemini CLI pode não estar disponível")

def test_gemini_with_cd():
    """Teste 2: Gemini com CD para projeto"""
    
    print("\n🔍 TESTE 2: Gemini CLI com CD")
    
    project_root = "/mnt/ramdisk/develop/nex-web-backend"
    
    try:
        cmd = f"cd {project_root} && npx https://github.com/google-gemini/gemini-cli --prompt 'Analyze this project structure briefly.'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Gemini pode acessar projeto com CD")
            print(f"📄 Output: {result.stdout[:300]}...")
        else:
            print(f"❌ FAILED: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - Gemini demora mais que esperado")

def test_gemini_stdin():
    """Teste 3: Gemini com stdin (como no orchestrator)"""
    
    print("\n🔍 TESTE 3: Gemini CLI com stdin")
    
    project_root = "/mnt/ramdisk/develop/nex-web-backend"
    prompt = "Analyze this Kotlin project and identify the build tool used."
    
    try:
        cmd = f"cd {project_root} && npx https://github.com/google-gemini/gemini-cli --prompt"
        result = subprocess.run(
            cmd, 
            shell=True, 
            input=prompt,
            text=True,
            capture_output=True, 
            timeout=90
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Gemini stdin approach funciona")
            print(f"📄 Output: {result.stdout[:250]}...")
        else:
            print(f"❌ FAILED: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - stdin approach não funciona")

if __name__ == "__main__":
    print("🧪 DEBUG: Gemini CLI Testing")
    print("=" * 60)
    
    test_gemini_simple()
    test_gemini_with_cd()
    test_gemini_stdin()
    
    print("\n🎯 CONCLUSÃO:")
    print("Se todos funcionam, podemos executar o orchestrator Gemini.")
    print("Se falham, precisamos ajustar a integração.")