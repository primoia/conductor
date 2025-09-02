"""
REPL Manager - Shared REPL Session Handling

Provides unified interactive session management for all CLI interfaces.
Includes circuit breaker and safety mechanisms to prevent infinite loops.
"""

import time
from typing import Dict, Callable, Any


class REPLManager:
    """Manages REPL sessions with customizable commands and behavior."""
    
    def __init__(self, agent_name: str, cli_instance: Any):
        """
        Initialize REPL manager with circuit breaker protection.
        
        Args:
            agent_name: Display name for the REPL prompt
            cli_instance: CLI instance that provides agent interaction methods
        """
        self.agent_name = agent_name
        self.cli_instance = cli_instance
        self.custom_commands = {}
        
        # Circuit Breaker Protection
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        self.error_reset_time = 30  # seconds
        self.last_error_time = 0
        self.total_interactions = 0
        self.max_interactions_per_session = 100
        self.session_start_time = time.time()
        self.max_session_duration = 3600  # 1 hour
        
        # Rate Limiting Protection (Anti-Spam)
        self.last_interaction_time = 0
        self.min_interaction_interval = 5.0  # minimum 5 seconds between interactions
        
        # Emergency stop flag
        self.emergency_stop = False
        
        self._setup_default_commands()
    
    def _get_multiline_input(self) -> str:
        """
        Get multi-line input from user. Supports pasting text with line breaks.
        Continues reading until user presses Enter on an empty line or types a command.
        """
        lines = []
        first_prompt = True
        
        while True:
            try:
                if first_prompt:
                    prompt = f"\n[{self.agent_name}]> "
                    first_prompt = False
                else:
                    prompt = f"[{self.agent_name}]... "
                
                line = input(prompt).rstrip()
                
                # If empty line, finish input (unless it's the very first line)
                if not line and lines:
                    break
                
                # If first line is empty, just wait for real input
                if not line and not lines:
                    continue
                    
                # Single command words should be processed immediately
                if not lines and line.lower() in ['exit', 'quit', 'sair', 'help', 'status', 'reset', 'emergency', 'clear', 'save', 'tools', 'scope', 'debug', 'state', 'history']:
                    return line
                
                # Add line to collection
                lines.append(line)
                
                # If this looks like a single-line command, process immediately
                if len(lines) == 1 and not self._looks_like_multiline_content(line):
                    break
                    
            except EOFError:
                # Ctrl+D pressed, treat as completion
                break
            except KeyboardInterrupt:
                # Ctrl+C pressed, clear current input and start over
                print("\n^C")
                return ""
        
        # Join all lines with newlines
        result = "\n".join(lines).strip()
        return result
    
    def _looks_like_multiline_content(self, line: str) -> bool:
        """
        Determine if a line suggests multi-line content is coming.
        This helps decide whether to wait for more input.
        """
        # Code indicators
        code_indicators = [
            'import ', 'def ', 'class ', 'if ', 'for ', 'while ', 'try:',
            'headers = {', 'data = {', 'config = {', 'response = requests.',
            '= {', '= [', 'function ', 'const ', 'let ', 'var '
        ]
        
        # Check if line contains code patterns that often continue
        for indicator in code_indicators:
            if indicator in line.lower():
                return True
        
        # Lines ending with certain characters suggest continuation
        continuation_endings = ['{', '[', '(', '=', 'import', ',']
        for ending in continuation_endings:
            if line.strip().endswith(ending):
                return True
                
        return False
    
    def _setup_default_commands(self):
        """Setup default REPL commands."""
        self.custom_commands = {
            'state': self._show_agent_state,
            'history': self._show_conversation_history,
            'clear': self._clear_conversation_history,
            'save': self._save_agent_state,
            'tools': self._show_available_tools,
            'scope': self._show_output_scope,
            'debug': self._show_debug_info,
            'status': self._show_safety_status,
            'reset': self._reset_circuit_breaker,
            'emergency': self._emergency_stop,
        }
    
    def add_custom_command(self, command: str, handler: Callable):
        """Add a custom command to the REPL."""
        self.custom_commands[command] = handler
    
    def start_session(self, custom_help: str = None):
        """Start interactive REPL session."""
        print(f"\n🤖 Iniciando sessão REPL para {self.agent_name}")
        print("💬 Digite 'exit', 'quit' ou 'sair' para encerrar")
        print("📝 Digite 'state' para ver o estado atual")
        print("📊 Digite 'history' para ver histórico de conversa")
        print("🗑️  Digite 'clear' para limpar todo o histórico")
        print("💾 Digite 'save' para salvar estado manualmente")
        print("🔧 Digite 'tools' para ver ferramentas disponíveis")
        print("🎯 Digite 'scope' para ver escopo de output")
        print("🔍 Digite 'debug' para ver informações de debug")
        print("🛡️ Digite 'status' para ver status de segurança")
        print("🔄 Digite 'reset' para reiniciar proteções")
        print("🚨 Digite 'emergency' para parada de emergência")
        print("")
        print("📋 ENTRADA MULTI-LINHA:")
        print("   • Cole código com múltiplas linhas normalmente")
        print("   • Pressione Enter em linha vazia para enviar")
        print("   • Comandos simples são enviados imediatamente")
        
        if custom_help:
            print(custom_help)
        
        # Check for simulation mode
        if hasattr(self.cli_instance, 'simulate_mode') and self.cli_instance.simulate_mode:
            print("🎭 MODO SIMULAÇÃO ATIVO - respostas simuladas, contexto mantido")
        
        print("=" * 60)
        print(f"🛡️ Proteção ativa: max {self.max_consecutive_errors} erros consecutivos, {self.max_interactions_per_session} interações/sessão")
        print(f"⚡ Rate Limit: min {self.min_interaction_interval}s entre interações (anti-spam)")
        print("=" * 60)
        
        while True and not self.emergency_stop:
            try:
                # Multi-line input support
                user_input = self._get_multiline_input()
                
                if user_input.lower() in ['exit', 'quit', 'sair']:
                    print("👋 Encerrando sessão REPL...")
                    break
                
                # Check other safety limits (NOT rate limiting yet)
                if not self._check_non_rate_limits():
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in self.custom_commands:
                    self.custom_commands[user_input.lower()]()
                    continue
                
                # Check rate limiting only for actual chat interactions
                if not self._check_rate_limiting():
                    continue  # Return to prompt, don't break
                
                # Normal chat with circuit breaker protection
                print("🤔 Processando...")
                self.total_interactions += 1
                
                try:
                    response = self.cli_instance.chat(user_input)
                    
                    # Check if response indicates error
                    if response and "❌" in response:
                        self._handle_error()
                    else:
                        self._handle_success()
                    
                    # Update rate limiting timestamp ONLY after successful processing
                    self.last_interaction_time = time.time()
                    
                    # Check for simulation mode in response display
                    if hasattr(self.cli_instance, 'simulate_mode') and self.cli_instance.simulate_mode:
                        print("🎭 Resposta Simulada:")
                    else:
                        print("🤖 Resposta:")
                    print("-" * 40)
                    print(response)
                    print("-" * 40)
                    
                except Exception as chat_error:
                    self._handle_error()
                    print(f"❌ Erro crítico no chat: {chat_error}")
                    print("🛡️ Proteção ativada - use 'reset' para tentar novamente")
                
            except KeyboardInterrupt:
                print("\n\n⚡ Interrompido pelo usuário. Use 'exit' para sair.")
                continue
            except EOFError:
                print("\n👋 Sessão REPL encerrada.")
                break
            except Exception as e:
                print(f"❌ Erro na sessão REPL: {e}")
    
    def _show_agent_state(self):
        """Show current agent state."""
        print("\n📊 === ESTADO ATUAL DO AGENTE ===")
        print(f"🆔 Agent ID: {self.cli_instance.agent_logic.get_current_agent()}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")
        
        # Show environment/project if available
        if hasattr(self.cli_instance.agent_logic, 'environment'):
            print(f"🌐 Environment: {self.cli_instance.agent_logic.environment}")
        if hasattr(self.cli_instance.agent_logic, 'project'):
            print(f"📦 Project: {self.cli_instance.agent_logic.project}")
        
        print(f"📂 Working Dir: {self.cli_instance.agent_logic.working_directory}")
        print("=" * 40)
    
    def _show_conversation_history(self):
        """Show conversation history."""
        print("\n💬 === HISTÓRICO DE CONVERSAS ===")
        
        if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
            history = self.cli_instance.agent_logic.llm_client.conversation_history
            if not history:
                print("📭 Nenhuma mensagem no histórico")
            else:
                for i, msg in enumerate(history, 1):
                    print(f"\n--- Mensagem {i} ---")
                    print(f"👤 User: {msg.get('prompt', 'N/A')}")
                    response = msg.get('response', 'N/A')
                    print(f"🤖 Assistant: {response[:200]}{'...' if len(response) > 200 else ''}")
        else:
            print("❌ Histórico não disponível")
        
        print("=" * 50)
    
    def _check_rate_limiting(self) -> bool:
        """Check only rate limiting (separate from other safety limits)."""
        if self.last_interaction_time > 0:  # Skip check for first interaction
            current_time = time.time()
            time_since_last = current_time - self.last_interaction_time
            if time_since_last < self.min_interaction_interval:
                remaining = self.min_interaction_interval - time_since_last
                print(f"⚡ RATE LIMIT: Aguarde {remaining:.1f}s - interações muito rápidas não são humanas")
                return False
        return True
    
    def _check_non_rate_limits(self) -> bool:
        """Check safety limits excluding rate limiting."""
        current_time = time.time()
        
        # Check session duration
        if current_time - self.session_start_time > self.max_session_duration:
            print(f"🚨 LIMITE DE SESSÃO EXCEDIDO ({self.max_session_duration/60:.0f} min)")
            print("   Sessão encerrada por segurança. Reinicie para continuar.")
            return False
        
        # Check total interactions
        if self.total_interactions >= self.max_interactions_per_session:
            print(f"🚨 LIMITE DE INTERAÇÕES EXCEDIDO ({self.max_interactions_per_session})")
            print("   Sessão encerrada por segurança. Reinicie para continuar.")
            return False
        
        # Check consecutive errors (circuit breaker)
        if self.consecutive_errors >= self.max_consecutive_errors:
            time_since_error = current_time - self.last_error_time
            if time_since_error < self.error_reset_time:
                remaining = self.error_reset_time - time_since_error
                print(f"🛡️ CIRCUIT BREAKER ATIVO - aguarde {remaining:.0f}s ou use 'reset'")
                return False
            else:
                # Auto-reset after timeout
                self.consecutive_errors = 0
                print("🔄 Circuit breaker resetado automaticamente")
        
        return True
    
    def _handle_error(self):
        """Handle error occurrence for circuit breaker."""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            print(f"🚨 CIRCUIT BREAKER ATIVADO após {self.consecutive_errors} erros consecutivos")
            print(f"   Aguarde {self.error_reset_time}s ou use 'reset' para continuar")
    
    def _handle_success(self):
        """Handle successful interaction."""
        self.consecutive_errors = 0  # Reset error counter on success
    
    def _show_safety_status(self):
        """Show current safety status."""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        print("\n🛡️ === STATUS DE SEGURANÇA ===")
        print(f"⏱️ Duração da sessão: {session_duration/60:.1f}/{self.max_session_duration/60:.0f} min")
        print(f"💬 Interações: {self.total_interactions}/{self.max_interactions_per_session}")
        print(f"❌ Erros consecutivos: {self.consecutive_errors}/{self.max_consecutive_errors}")
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            remaining = self.error_reset_time - (current_time - self.last_error_time)
            if remaining > 0:
                print(f"🚨 Circuit Breaker ATIVO - {remaining:.0f}s restantes")
            else:
                print("✅ Circuit Breaker pode ser resetado")
        else:
            print("✅ Todos os sistemas operacionais")
        
        print(f"🚨 Emergency Stop: {'ATIVO' if self.emergency_stop else 'Desativado'}")
        print("=" * 40)
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker and safety counters."""
        print("\n🔄 === RESETANDO PROTEÇÕES ===")
        print(f"Erros consecutivos resetados: {self.consecutive_errors} → 0")
        self.consecutive_errors = 0
        self.last_error_time = 0
        print("✅ Circuit breaker resetado com sucesso")
        print("=" * 40)
    
    def _emergency_stop(self):
        """Activate emergency stop."""
        print("\n🚨 === PARADA DE EMERGÊNCIA ATIVADA ===")
        print("Sistema interrompido imediatamente por comando do usuário")
        print("Use 'exit' para sair definitivamente")
        self.emergency_stop = True
        print("=" * 50)
    
    def _clear_conversation_history(self):
        """Clear conversation history."""
        print("\n🗑️ === LIMPANDO HISTÓRICO ===")
        
        if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
            history_count = len(self.cli_instance.agent_logic.llm_client.conversation_history)
            self.cli_instance.agent_logic.llm_client.conversation_history.clear()
            self.cli_instance.agent_logic.save_agent_state()
            print(f"✅ Histórico limpo: {history_count} mensagens removidas")
        else:
            print("❌ Histórico não disponível para limpeza")
        
        print("=" * 40)
    
    def _save_agent_state(self):
        """Save agent state."""
        self.cli_instance.save_agent_state()
    
    def _show_available_tools(self):
        """Show available tools."""
        print("\n🔧 === FERRAMENTAS DISPONÍVEIS ===")
        tools = self.cli_instance.get_available_tools()
        if tools:
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool}")
        else:
            print("🚫 Nenhuma ferramenta configurada")
        print("=" * 40)
    
    def _show_output_scope(self):
        """Show output scope restrictions."""
        print("\n🎯 === ESCOPO DE OUTPUT ===")
        
        if hasattr(self.cli_instance, 'get_output_scope'):
            scope = self.cli_instance.get_output_scope()
            if scope:
                print("📝 Este agente está restrito aos seguintes arquivos/diretórios:")
                for i, path in enumerate(scope, 1):
                    print(f"{i}. {path}")
            else:
                print("🔓 Sem restrições de escopo (meta-agent)")
        else:
            print("🔓 Sem restrições de escopo (meta-agent)")
        
        print("=" * 40)
    
    def _show_debug_info(self):
        """Show debug information."""
        print("\n🔍 === DEBUG: INFORMAÇÕES DO AGENTE ===")
        print(f"🆔 Agent ID: {self.cli_instance.agent_logic.get_current_agent()}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")
        print(f"🔧 Available Tools: {self.cli_instance.get_available_tools()}")
        
        if hasattr(self.cli_instance, 'simulate_mode'):
            print(f"🎭 Simulation Mode: {self.cli_instance.simulate_mode}")
        
        print("=" * 50)
    
    def _handle_error(self):
        """Handle error occurrence for circuit breaker."""
        self.consecutive_errors += 1
        self.last_error_time = time.time()
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            print(f"🚨 CIRCUIT BREAKER ATIVADO após {self.consecutive_errors} erros consecutivos")
            print(f"   Aguarde {self.error_reset_time}s ou use 'reset' para continuar")
    
    def _handle_success(self):
        """Handle successful interaction."""
        self.consecutive_errors = 0  # Reset error counter on success
    
    def _show_safety_status(self):
        """Show current safety status."""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        print("\n🛡️ === STATUS DE SEGURANÇA ===")
        print(f"⏱️ Duração da sessão: {session_duration/60:.1f}/{self.max_session_duration/60:.0f} min")
        print(f"💬 Interações: {self.total_interactions}/{self.max_interactions_per_session}")
        print(f"❌ Erros consecutivos: {self.consecutive_errors}/{self.max_consecutive_errors}")
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            remaining = self.error_reset_time - (current_time - self.last_error_time)
            if remaining > 0:
                print(f"🚨 Circuit Breaker ATIVO - {remaining:.0f}s restantes")
            else:
                print("✅ Circuit Breaker pode ser resetado")
        else:
            print("✅ Todos os sistemas operacionais")
        
        print(f"🚨 Emergency Stop: {'ATIVO' if self.emergency_stop else 'Desativado'}")
        print("=" * 40)
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker and safety counters."""
        print("\n🔄 === RESETANDO PROTEÇÕES ===")
        print(f"Erros consecutivos resetados: {self.consecutive_errors} → 0")
        self.consecutive_errors = 0
        self.last_error_time = 0
        print("✅ Circuit breaker resetado com sucesso")
        print("=" * 40)
    
    def _emergency_stop(self):
        """Activate emergency stop."""
        print("\n🚨 === PARADA DE EMERGÊNCIA ATIVADA ===")
        print("Sistema interrompido imediatamente por comando do usuário")
        print("Use 'exit' para sair definitivamente")
        self.emergency_stop = True
        print("=" * 50)