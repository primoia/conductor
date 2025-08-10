#!/usr/bin/env python3
"""
Test Gemini CLI that's actually working
"""

import subprocess
import time

def test_gemini_simple():
    """Test 1: Simple math"""
    print("🔍 TESTE 1: Gemini CLI matemática simples")
    
    try:
        cmd = ["npx", "--yes", "@google/gemini-cli", "--prompt", "What is 5+5?"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ FAILED: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT")
        return False

def test_gemini_kotlin_analysis():
    """Test 2: Analyze Kotlin code directly"""
    print("\n🔍 TESTE 2: Análise de código Kotlin")
    
    kotlin_code = '''
    fun convertDateToLocalDateTime(date: Date): LocalDateTime {
        return date.toInstant()
            .atZone(ZoneId.systemDefault())
            .toLocalDateTime()
    }
    '''
    
    prompt = f"Analyze this Kotlin function and suggest 2 test cases: {kotlin_code}"
    
    try:
        cmd = ["npx", "--yes", "@google/gemini-cli", "--prompt", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Gemini pode analisar Kotlin")
            print(f"📄 Output: {result.stdout[:300]}...")
            return True
        else:
            print(f"❌ FAILED: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - análise de código demorou muito")
        return False

def test_gemini_test_generation():
    """Test 3: Generate simple test"""
    print("\n🔍 TESTE 3: Geração de teste simples")
    
    prompt = '''Generate a JUnit 5 test for this function:
    
fun formatDate(date: Date): String {
    val formatter = SimpleDateFormat("dd/MM/yyyy")
    return formatter.format(date)
}

Just output the test code.'''
    
    try:
        cmd = ["npx", "--yes", "@google/gemini-cli", "--prompt", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Gemini pode gerar testes")
            print(f"📄 Output: {result.stdout[:400]}...")
            return True
        else:
            print(f"❌ FAILED: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - geração de teste demorou muito")
        return False

def test_gemini_with_project_context():
    """Test 4: Project analysis with explicit file content"""
    print("\n🔍 TESTE 4: Análise com contexto do projeto")
    
    # Read DateHelpers content
    try:
        with open('/mnt/ramdisk/develop/nex-web-backend/src/main/kotlin/br/com/nextar/web/utils/DateHelpers.kt', 'r') as f:
            file_content = f.read()
    except:
        print("❌ Could not read DateHelpers.kt")
        return False
    
    prompt = f'''Analyze this Kotlin utility class and recommend 3 test scenarios:

{file_content[:500]}...

Focus on the most important test cases.'''
    
    try:
        cmd = ["npx", "--yes", "@google/gemini-cli", "--prompt", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: Gemini analisou DateHelpers")
            print(f"📄 Output: {result.stdout[:350]}...")
            return True
        else:
            print(f"❌ FAILED: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - análise complexa demorou muito")
        return False

if __name__ == "__main__":
    print("🧪 GEMINI CLI WORKING TESTS")
    print("=" * 60)
    
    tests = [
        test_gemini_simple,
        test_gemini_kotlin_analysis, 
        test_gemini_test_generation,
        test_gemini_with_project_context
    ]
    
    results = []
    for test in tests:
        results.append(test())
        time.sleep(2)  # Pause between tests
    
    success_count = sum(results)
    print(f"\n🎯 RESULTADO FINAL:")
    print(f"Testes bem sucedidos: {success_count}/{len(results)}")
    
    if success_count >= 3:
        print("✅ Gemini está funcionando bem - podemos implementar o orchestrator real!")
    elif success_count >= 2:
        print("⚠️ Gemini funciona mas pode ser instável - usar com timeouts maiores")
    else:
        print("❌ Gemini não está funcionando consistentemente - manter simulação")