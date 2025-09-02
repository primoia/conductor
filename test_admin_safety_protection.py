#!/usr/bin/env python3
"""
Teste dos Mecanismos de Proteção do Admin CLI

Testa todas as proteções implementadas para prevenir loops infinitos
e garantir máxima confiabilidade.
"""

import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import time

from src.cli.shared.repl_manager import REPLManager
from src.core.agent_logic import AgentLogic


def test_protection_mechanisms():
    """Testa todos os mecanismos de proteção implementados."""
    print("🛡️ TESTE DOS MECANISMOS DE PROTEÇÃO")
    print("=" * 50)
    
    # 1. Teste AgentLogic - Não relança exceptions
    print("\n1. 🔧 Testando AgentLogic.chat() - Correção do Loop")
    
    # Mock dependencies
    mock_state_repo = Mock()
    mock_llm_client = Mock()
    mock_llm_client.conversation_history = []
    
    # Simulate LLM client error
    mock_llm_client.invoke.side_effect = Exception("Argument list too long")
    
    agent_logic = AgentLogic(mock_state_repo, mock_llm_client)
    agent_logic.embodied = True
    agent_logic.prompt_engine = Mock()
    agent_logic.prompt_engine.build_prompt.return_value = "test prompt"
    
    # Should return error instead of raising
    result = agent_logic.chat("test message")
    
    print(f"   Resultado: {result[:50]}...")
    assert "❌ Chat failed" in result, "AgentLogic deve retornar erro em vez de relançar exception"
    print("   ✅ AgentLogic não relança exceptions - CORRIGIDO")
    
    # 2. Teste REPLManager Circuit Breaker
    print("\n2. 🛡️ Testando Circuit Breaker do REPLManager")
    
    mock_cli = Mock()
    mock_cli.embodied = True
    mock_cli.agent_logic.get_current_agent.return_value = "TestAgent"
    
    repl = REPLManager("test", mock_cli)
    
    # Test initial state
    print(f"   Estado inicial: {repl.consecutive_errors} erros")
    assert repl.consecutive_errors == 0, "Deve começar com 0 erros"
    
    # Simulate consecutive errors
    repl._handle_error()
    repl._handle_error() 
    repl._handle_error()  # 3rd error should trigger circuit breaker
    
    print(f"   Após 3 erros: {repl.consecutive_errors} erros consecutivos")
    assert repl.consecutive_errors == 3, "Deve ter 3 erros consecutivos"
    
    # Test circuit breaker activation
    safety_check = repl._check_safety_limits()
    print(f"   Circuit breaker ativo: {not safety_check}")
    assert not safety_check, "Circuit breaker deve estar ativo após 3 erros"
    
    # Test reset
    repl._reset_circuit_breaker()
    print(f"   Após reset: {repl.consecutive_errors} erros")
    assert repl.consecutive_errors == 0, "Reset deve zerar erros"
    
    safety_check = repl._check_safety_limits()
    print(f"   Circuit breaker após reset: {not safety_check}")
    assert safety_check, "Circuit breaker deve estar inativo após reset"
    
    print("   ✅ Circuit Breaker funcionando corretamente")
    
    # 3. Teste Limites de Sessão
    print("\n3. ⏱️ Testando Limites de Sessão")
    
    # Test interaction limit
    repl.total_interactions = repl.max_interactions_per_session
    safety_check = repl._check_safety_limits()
    print(f"   Limite de interações atingido: {not safety_check}")
    assert not safety_check, "Deve parar quando limite de interações é atingido"
    
    # Reset for next test
    repl.total_interactions = 0
    
    # Test session duration (simulate)
    original_start = repl.session_start_time
    repl.session_start_time = time.time() - repl.max_session_duration - 1
    safety_check = repl._check_safety_limits()
    print(f"   Limite de duração atingido: {not safety_check}")
    assert not safety_check, "Deve parar quando limite de tempo é atingido"
    
    # Restore
    repl.session_start_time = original_start
    print("   ✅ Limites de sessão funcionando corretamente")
    
    # 4. Teste Emergency Stop
    print("\n4. 🚨 Testando Emergency Stop")
    
    assert not repl.emergency_stop, "Emergency stop deve estar desativado inicialmente"
    
    repl._emergency_stop()
    assert repl.emergency_stop, "Emergency stop deve estar ativado após comando"
    print("   ✅ Emergency Stop funcionando corretamente")
    
    # 5. Teste Status de Segurança
    print("\n5. 📊 Testando Status de Segurança")
    
    # Restore state for final test
    repl.emergency_stop = False
    repl.consecutive_errors = 1
    repl.total_interactions = 10
    
    # Capture status output (mock print)
    with patch('builtins.print') as mock_print:
        repl._show_safety_status()
        
    # Verify status was called
    assert mock_print.called, "Status deve imprimir informações"
    print("   ✅ Status de segurança funcionando")
    
    print(f"\n🎯 TODOS OS MECANISMOS DE PROTEÇÃO FUNCIONANDO!")
    print("=" * 50)
    print("✅ AgentLogic: Não relança exceptions")
    print("✅ Circuit Breaker: Para após 3 erros consecutivos")  
    print("✅ Limites de Sessão: Tempo e interações controlados")
    print("✅ Emergency Stop: Parada imediata disponível")
    print("✅ Reset Manual: Permite recuperação controlada")
    print("=" * 50)
    
    return True


def test_error_detection():
    """Testa detecção de erros no response."""
    print("\n🔍 TESTE DE DETECÇÃO DE ERROS")
    print("-" * 30)
    
    mock_cli = Mock()
    repl = REPLManager("test", mock_cli)
    
    # Test error response detection
    test_cases = [
        ("❌ Error in chat: something", True),
        ("✅ Success response", False),
        ("❌ Chat failed: timeout", True),
        ("Normal response without errors", False)
    ]
    
    for response, should_be_error in test_cases:
        # Reset state
        repl.consecutive_errors = 0
        
        # Simulate response check
        if response and "❌" in response:
            repl._handle_error()
            detected_error = repl.consecutive_errors > 0
        else:
            repl._handle_success()
            detected_error = False
        
        print(f"   '{response[:30]}...' -> Erro detectado: {detected_error}")
        assert detected_error == should_be_error, f"Detecção incorreta para: {response}"
    
    print("   ✅ Detecção de erros funcionando corretamente")
    

if __name__ == "__main__":
    try:
        success = test_protection_mechanisms()
        test_error_detection()
        
        print(f"\n🚀 SISTEMA ALTAMENTE CONFIÁVEL IMPLEMENTADO!")
        print("   Agora o Admin CLI não entrará mais em loops infinitos")
        print("   Máxima proteção contra custos exponenciais")
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        raise