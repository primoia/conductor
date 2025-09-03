#!/usr/bin/env python3
"""
Análise detalhada da comunicação com Ollama API + DeepSeek Coder V2 16B
Mostra exatamente o que enviamos e o que recebemos
"""

import json
import requests
import time


def test_ollama_api_detailed():
    """Testa diferentes tipos de comunicação com Ollama API"""

    print("🔍 ANÁLISE DETALHADA: OLLAMA API + DEEPSEEK CODER V2 16B")
    print("=" * 70)

    base_url = "http://localhost:11434"
    model = "deepseek-coder-v2:16b"

    # Teste 1: API Generate (modo simples)
    print("\n1️⃣ TESTE: API GENERATE (Modo Simples)")
    print("-" * 50)

    prompt = "Execute unit test: TestUserService.shouldValidateEmail(). Return only PASS or FAIL."

    generate_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "max_tokens": 10},
    }

    print("📤 REQUEST (Generate API):")
    print(json.dumps(generate_payload, indent=2))

    try:
        response = requests.post(
            f"{base_url}/api/generate", json=generate_payload, timeout=30
        )
        print(f"\n📥 RESPONSE STATUS: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("📥 RESPONSE BODY:")
            print(json.dumps(result, indent=2))
            print(f"\n🎯 EXTRACTED ANSWER: '{result['response'].strip()}'")
        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

    # Teste 2: API Chat (modo estruturado)
    print("\n\n2️⃣ TESTE: API CHAT (Modo Estruturado)")
    print("-" * 50)

    chat_payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a JUnit test executor. Respond only with PASS or FAIL.",
            },
            {
                "role": "user",
                "content": "Execute test TestUserService.shouldValidateEmail() with input 'user@example.com'. This is a valid email format test.",
            },
        ],
        "stream": False,
        "options": {"temperature": 0.1, "max_tokens": 5},
    }

    print("📤 REQUEST (Chat API):")
    print(json.dumps(chat_payload, indent=2))

    try:
        response = requests.post(f"{base_url}/api/chat", json=chat_payload, timeout=30)
        print(f"\n📥 RESPONSE STATUS: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("📥 RESPONSE BODY:")
            print(json.dumps(result, indent=2))

            message_content = result.get("message", {}).get("content", "")
            print(f"\n🎯 EXTRACTED ANSWER: '{message_content.strip()}'")

            # Mostrar métricas de performance
            print(f"\n📊 PERFORMANCE METRICS:")
            print(
                f"   Total Duration: {result.get('total_duration', 0) / 1_000_000:.0f}ms"
            )
            print(
                f"   Load Duration: {result.get('load_duration', 0) / 1_000_000:.0f}ms"
            )
            print(
                f"   Prompt Eval: {result.get('prompt_eval_duration', 0) / 1_000_000:.0f}ms"
            )
            print(
                f"   Eval Duration: {result.get('eval_duration', 0) / 1_000_000:.0f}ms"
            )
            print(f"   Prompt Tokens: {result.get('prompt_eval_count', 0)}")
            print(f"   Completion Tokens: {result.get('eval_count', 0)}")

        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")

    # Teste 3: Diferentes tipos de tarefa
    print("\n\n3️⃣ TESTE: DIFERENTES TIPOS DE TAREFA")
    print("-" * 50)

    test_cases = [
        {
            "name": "Syntax Check",
            "system": "You are a Java syntax validator. Respond only with VALID or INVALID.",
            "user": "Check syntax: public class UserService { private String name; }",
        },
        {
            "name": "Gradle Version",
            "system": "You are a Gradle version extractor. Respond only with the version number (e.g., 7.5.1).",
            "user": "Extract Gradle version from: gradle wrapper version 7.5.1",
        },
        {
            "name": "Code Review",
            "system": "You are a code reviewer. Respond only with OK or ISSUES.",
            "user": "Quick review: public void processPayment() { /* missing validation */ }",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n3.{i} {test_case['name']}:")
        print(f"System: {test_case['system']}")
        print(f"User: {test_case['user']}")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": test_case["system"]},
                {"role": "user", "content": test_case["user"]},
            ],
            "stream": False,
            "options": {"temperature": 0.1, "max_tokens": 10},
        }

        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/api/chat", json=payload, timeout=30)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "").strip()

                # Limpar resposta de markdown
                import re

                clean_content = re.sub(r"```\w*\n?", "", content)
                clean_content = re.sub(r"```", "", clean_content).strip()

                print(f"   📥 Raw Response: '{content}'")
                print(f"   🎯 Clean Answer: '{clean_content}'")
                print(f"   ⏱️ Time: {int((end_time - start_time) * 1000)}ms")
                print(
                    f"   🔤 Tokens: {result.get('prompt_eval_count', 0)}+{result.get('eval_count', 0)}"
                )

            else:
                print(f"   ❌ Error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")


def analyze_response_patterns():
    """Analisa padrões nas respostas do DeepSeek"""

    print("\n\n🔬 ANÁLISE DE PADRÕES NAS RESPOSTAS")
    print("=" * 50)

    # Exemplos de respostas reais que recebemos
    real_responses = [
        {
            "task": "Unit Test",
            "request": "Execute test TestUserService.shouldValidateEmail() with 'user@example.com'",
            "raw_response": "```java\nPASS\n```",
            "extracted": "PASS",
        },
        {
            "task": "Syntax Check",
            "request": "Check syntax: public class UserService { private String name; }",
            "raw_response": "VALID",
            "extracted": "VALID",
        },
        {
            "task": "Gradle Version",
            "request": "Extract version from: gradle wrapper version 7.5.1",
            "raw_response": "7.5.1",
            "extracted": "7.5.1",
        },
        {
            "task": "Code Review",
            "request": "Review: public void processPayment() { /* missing validation */ }",
            "raw_response": "ISSUES\n\nThe method `processPayment()` lacks input validation...",
            "extracted": "ISSUES",
        },
    ]

    print("📊 PADRÕES IDENTIFICADOS:")
    print()

    for i, example in enumerate(real_responses, 1):
        print(f"{i}. {example['task']}:")
        print(f"   📤 Request: {example['request']}")
        print(f"   📥 Raw Response: {example['raw_response'][:60]}...")
        print(f"   🎯 Extracted: {example['extracted']}")
        print(
            f"   ✅ Success: {'Yes' if example['extracted'] in ['PASS', 'FAIL', 'VALID', 'INVALID', 'OK', 'ISSUES'] or example['extracted'].replace('.', '').replace('-', '').isdigit() else 'No'}"
        )
        print()

    print("🎯 CONCLUSÕES:")
    print("• DeepSeek às vezes inclui blocos de código markdown (```)")
    print("• Respostas podem ter texto adicional após a resposta principal")
    print("• System messages funcionam bem para instruções específicas")
    print("• max_tokens baixo (5-10) força respostas concisas")
    print("• temperature=0.1 dá resultados mais consistentes")

    print("\n💡 ESTRATÉGIAS DE OTIMIZAÇÃO:")
    print("• Usar Chat API em vez de Generate API")
    print("• System message claro com formato esperado")
    print("• Regex para extrair padrões específicos (versões, PASS/FAIL)")
    print("• Remover markdown com re.sub()")
    print("• Primeira linha/palavra geralmente contém a resposta")


if __name__ == "__main__":
    test_ollama_api_detailed()
    analyze_response_patterns()
