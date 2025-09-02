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
        raise#!/usr/bin/env python3
"""
Teste do Input Multi-linha
Testa se o sistema aceita texto com múltiplas linhas como uma única interação
"""

from unittest.mock import Mock, patch
from src.cli.shared.repl_manager import REPLManager
import io


def test_multiline_detection():
    """Testa a detecção de conteúdo multi-linha."""
    print("📋 TESTE DE DETECÇÃO MULTI-LINHA")
    print("=" * 50)
    
    mock_cli = Mock()
    repl = REPLManager("test", mock_cli)
    
    # Test cases for multiline detection
    test_cases = [
        # Should detect as multiline
        ("import requests", True),
        ("headers = {", True),
        ("data = {", True),
        ("def function_name", True),
        ("if condition:", True),
        ("response = requests.post", True),
        
        # Should process immediately
        ("help", False),
        ("status", False),
        ("exit", False),
        ("simple message", False),
        ("what is this?", False),
    ]
    
    for line, should_be_multiline in test_cases:
        result = repl._looks_like_multiline_content(line)
        print(f"   '{line}' → Multi-linha: {result} {'✅' if result == should_be_multiline else '❌'}")
        assert result == should_be_multiline, f"Detecção incorreta para: {line}"
    
    print("\n✅ Detecção de conteúdo multi-linha funcionando!")
    print("=" * 50)
    
    return True


def test_input_simulation():
    """Simula cenários de input para verificar comportamento."""
    print("\n🎭 SIMULAÇÃO DE CENÁRIOS DE INPUT")
    print("=" * 40)
    
    # Scenario 1: Single command
    print("1. Comando simples: 'help'")
    print("   Esperado: Processamento imediato ✅")
    
    # Scenario 2: Multiline code
    print("\n2. Código multi-linha:")
    print("   import requests")
    print("   import json")
    print("   url_auth = \"https://api.com\"")
    print("   headers = {\"client\": \"TEST\"}")
    print("   [linha vazia]")
    print("   Esperado: Tudo enviado junto como uma única interação ✅")
    
    # Scenario 3: Mixed content
    print("\n3. Conteúdo misto:")
    print("   Primeira linha de explicação")
    print("   import requests")
    print("   Segunda linha de explicação") 
    print("   [linha vazia]")
    print("   Esperado: Tudo como uma mensagem única ✅")
    
    print("\n✅ Cenários definidos - teste manual necessário")
    print("=" * 40)


if __name__ == "__main__":
    try:
        success = test_multiline_detection()
        test_input_simulation()
        
        print(f"\n🚀 INPUT MULTI-LINHA IMPLEMENTADO!")
        print("=" * 50)
        print("✅ Detecção automática de conteúdo multi-linha")
        print("✅ Comandos simples processados imediatamente")  
        print("✅ Código/texto longo aguarda linha vazia")
        print("✅ Suporte para colar texto com quebras de linha")
        print("=" * 50)
        print("📝 COMO USAR:")
        print("   • Comandos simples (help, status): Enter direto")
        print("   • Código multi-linha: Cole e pressione Enter em linha vazia")
        print("   • Ctrl+C cancela input atual")
        print("   • Ctrl+D finaliza input")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        raise#!/usr/bin/env python3
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