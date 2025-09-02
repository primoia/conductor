#!/usr/bin/env python3
"""
Teste do Rate Limiting - Proteção Anti-Spam
Testa se o sistema bloqueia tentativas muito rápidas (< 1 segundo)
"""

import time
from unittest.mock import Mock
from src.cli.shared.repl_manager import REPLManager


def test_rate_limiting():
    """Testa o mecanismo de rate limiting."""
    print("⚡ TESTE DO RATE LIMITING (ANTI-SPAM)")
    print("=" * 50)
    
    # Mock do CLI
    mock_cli = Mock()
    mock_cli.embodied = True
    mock_cli.agent_logic.get_current_agent.return_value = "TestAgent"
    
    # Criar REPLManager
    repl = REPLManager("test", mock_cli)
    
    print(f"Configuração: min {repl.min_interaction_interval}s entre interações")
    print()
    
    # Teste 1: Primeira interação (deve passar)
    print("1. 🟢 Testando primeira interação (deve passar)")
    rate_check = repl._check_rate_limiting()
    print(f"   Resultado: {rate_check} ✅")
    assert rate_check == True, "Primeira interação deve sempre passar"
    
    # Simular primeira interação processada com sucesso
    repl.last_interaction_time = time.time()
    
    # Teste 2: Segunda interação imediata (deve bloquear)
    print("\n2. 🔴 Testando interação imediata (deve bloquear)")
    rate_check = repl._check_rate_limiting()
    print(f"   Resultado: {rate_check} ✅")
    assert rate_check == False, "Interação imediata deve ser bloqueada"
    
    # Teste 3: Aguardar 2s (ainda deve bloquear)
    print("\n3. 🟡 Testando após 2s (deve bloquear)")
    time.sleep(2.0)
    rate_check = repl._check_rate_limiting()
    print(f"   Resultado: {rate_check} ✅")
    assert rate_check == False, "Interação após 2s deve ser bloqueada"
    
    # Teste 4: Aguardar mais 3.1s (total 5.1s, deve passar)
    print("\n4. 🟢 Testando após 5.1s total (deve passar)")
    time.sleep(3.1)  # Total: 5.1s
    rate_check = repl._check_rate_limiting()
    print(f"   Resultado: {rate_check} ✅")
    assert rate_check == True, "Interação após 5.1s deve passar"
    
    print("\n🎯 RATE LIMITING FUNCIONANDO PERFEITAMENTE!")
    print("✅ Primeira interação: PASSOU")
    print("✅ Interação imediata: BLOQUEADA") 
    print("✅ Interação após 2s: BLOQUEADA")
    print("✅ Interação após 5.1s: PASSOU")
    print("=" * 50)
    
    return True


def test_rate_limiting_with_other_limits():
    """Testa rate limiting em conjunto com outras proteções."""
    print("\n🛡️ TESTE DE INTEGRAÇÃO COM OUTRAS PROTEÇÕES")
    print("-" * 50)
    
    mock_cli = Mock()
    mock_cli.embodied = True
    mock_cli.agent_logic.get_current_agent.return_value = "TestAgent"
    
    repl = REPLManager("test", mock_cli)
    
    # Simular 3 erros consecutivos para ativar circuit breaker
    repl.consecutive_errors = 3
    repl.last_error_time = time.time()
    
    # Verificar que circuit breaker tem prioridade
    print("1. Circuit breaker ativo + rate limiting")
    safety_check = repl._check_safety_limits()
    print(f"   Circuit breaker bloqueia: {not safety_check} ✅")
    assert safety_check == False, "Circuit breaker deve bloquear"
    
    # Reset circuit breaker
    repl.consecutive_errors = 0
    repl.last_error_time = 0
    
    # Testar apenas rate limiting
    repl.last_interaction_time = time.time()
    safety_check = repl._check_safety_limits()
    print(f"   Rate limiting bloqueia: {not safety_check} ✅")
    assert safety_check == False, "Rate limiting deve bloquear"
    
    print("\n✅ Integração funcionando - múltiplas proteções ativas")
    
    return True


if __name__ == "__main__":
    try:
        success1 = test_rate_limiting()
        success2 = test_rate_limiting_with_other_limits()
        
        print(f"\n🚀 RATE LIMITING IMPLEMENTADO COM SUCESSO!")
        print("   Agora tentativas < 1s são bloqueadas automaticamente")
        print("   Sistema protegido contra spam e automação maliciosa")
        print("   Integração perfeita com outras proteções")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        raise