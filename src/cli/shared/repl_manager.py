"""
REPL Manager - Shared REPL Session Handling

Provides unified interactive session management for all CLI interfaces.
Includes circuit breaker and safety mechanisms to prevent infinite loops.
"""

import time
import os
import glob
from typing import Dict, Callable, Any, List
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from pygments.lexers.python import PythonLexer


class FileCompleter(Completer):
    """Autocompletar para arquivos quando usar @"""

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        # Verifica se estamos completando após um @
        if '@' in text:
            # Encontra a última ocorrência de @
            at_index = text.rfind('@')
            if at_index >= 0:
                # Extrai o texto após o @
                file_path = text[at_index + 1:]

                # Se não há espaço após @, estamos completando o arquivo
                if ' ' not in file_path:
                    try:
                        # Se o caminho é vazio, busca no diretório atual
                        if not file_path:
                            pattern = "*"
                            base_dir = "."
                        elif file_path.endswith('/'):
                            # Se termina com /, busca dentro do diretório
                            pattern = file_path + "*"
                            base_dir = "."
                        else:
                            # Busca arquivos que começam com o texto digitado
                            pattern = file_path + "*"
                            base_dir = "."

                        # Busca arquivos e diretórios
                        matches = glob.glob(pattern)

                        for match in sorted(matches):
                            # Remove o prefixo já digitado
                            completion_text = match[len(file_path):]
                            if os.path.isdir(match):
                                completion_text += "/"

                            yield Completion(
                                completion_text,
                                start_position=0,
                                display=match,
                                display_meta="📁 Diretório" if os.path.isdir(match) else "📄 Arquivo"
                            )
                    except Exception:
                        # Em caso de erro, não mostra completions
                        pass


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
        Captura input multi-linha com edição rica usando prompt_toolkit.
        Pressione Ctrl+D para enviar.
        """
        # Define que a submissão será APENAS com Ctrl+D
        bindings = KeyBindings()

        @bindings.add('c-d')
        def _(event):
            """Ctrl+D submete o input"""
            event.app.current_buffer.validate_and_handle()

        @bindings.add('enter')
        def _(event):
            """Enter submete, Shift+Enter adiciona nova linha"""
            event.app.current_buffer.validate_and_handle()

        @bindings.add('escape', 'enter')  # Alt+Enter (mais compatível)
        def _(event):
            """Alt+Enter adiciona nova linha"""
            event.app.current_buffer.insert_text('\n')

        # Define o caminho do histórico dentro do workspace
        history_path = os.path.join('.conductor_workspace', '.repl_history.txt')

        try:
            # Exibe o prompt e aguarda a submissão
            user_input = prompt(
                f"[{self.agent_name}]> ",
                multiline=True,
                key_bindings=bindings,
                history=FileHistory(history_path),
                lexer=PygmentsLexer(PythonLexer),
                prompt_continuation=" " * (len(self.agent_name) + 5),  # Espaços em vez de texto
                wrap_lines=True,  # Permite wrap de linhas longas
                mouse_support=True,  # Habilita suporte a mouse
                complete_style='column',  # Estilo de autocompletar mais limpo
                completer=FileCompleter(),  # Autocompletar para arquivos com @
                complete_while_typing=True  # Mostra sugestões enquanto digita
            )
            # Processa referências de arquivo antes de retornar
            return self._process_file_references(user_input)
        except (EOFError, KeyboardInterrupt):
            # Trata Ctrl+D em linha vazia ou Ctrl+C como um comando de saída
            return "exit"

    def _process_file_references(self, text: str) -> str:
        """
        Processa referências de arquivo no formato @arquivo e expande o conteúdo.
        Similar ao comportamento @ do Gemini/Claude.
        """
        import re

        # Padrão para encontrar @arquivo (não seguido de espaço)
        file_pattern = r'@([^\s@]+)'

        def replace_file_ref(match):
            file_path = match.group(1)
            try:
                # Verifica se o arquivo existe
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Limita o tamanho do arquivo (máximo 2000 caracteres para não sobrecarregar)
                    if len(content) > 2000:
                        content = content[:2000] + "\n... [arquivo truncado]"

                    # Formata o conteúdo do arquivo
                    return f"\n📎 **Arquivo: {file_path}**\n```\n{content}\n```\n"
                else:
                    return f"\n❌ **Arquivo não encontrado: {file_path}**\n"
            except Exception as e:
                return f"\n❌ **Erro ao ler arquivo {file_path}: {str(e)}**\n"

        # Substitui todas as referências @arquivo pelo conteúdo
        processed_text = re.sub(file_pattern, replace_file_ref, text)

        return processed_text

    def _looks_like_multiline_content(self, line: str) -> bool:
        """
        Determine if a line suggests multi-line content is coming.
        This helps decide whether to wait for more input.
        """
        # Code indicators
        code_indicators = [
            "import ",
            "def ",
            "class ",
            "if ",
            "for ",
            "while ",
            "try:",
            "headers = {",
            "data = {",
            "config = {",
            "response = requests.",
            "= {",
            "= [",
            "function ",
            "const ",
            "let ",
            "var ",
        ]

        # Check if line contains code patterns that often continue
        for indicator in code_indicators:
            if indicator in line.lower():
                return True

        # Lines ending with certain characters suggest continuation
        continuation_endings = ["{", "[", "(", "=", "import", ","]
        for ending in continuation_endings:
            if line.strip().endswith(ending):
                return True

        return False

    def _setup_default_commands(self):
        """Setup default REPL commands."""
        self.custom_commands = {
            "state": self._show_agent_state,
            "history": self._show_conversation_history,
            "clear": self._clear_conversation_history,
            "save": self._save_agent_state,
            "tools": self._show_available_tools,
            "scope": self._show_output_scope,
            "debug": self._show_debug_info,
            "prompt": self._show_full_prompt,
            "status": self._show_safety_status,
            "reset": self._reset_circuit_breaker,
            "emergency": self._emergency_stop,
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
        print("📝 Digite 'prompt' para ver prompt completo enviado para IA")
        print("💾 Digite 'prompt save' para ver e salvar prompt em arquivo .md")
        print("🛡️ Digite 'status' para ver status de segurança")
        print("🔄 Digite 'reset' para reiniciar proteções")
        print("🚨 Digite 'emergency' para parada de emergência")
        print("")
        print("💡 Pressione Enter para ENVIAR, Alt+Enter para nova linha")
        print("🔧 Use setas ↑↓ para navegar entre linhas, ←→ para mover o cursor")
        print("🖱️  Use o mouse para posicionar o cursor em qualquer lugar")
        print("📎 Digite '@' seguido do nome do arquivo para referenciar (ex: @config.yaml)")
        print("🔍 Tab para autocompletar arquivos após @")

        if custom_help:
            print(custom_help)

        # Check for simulation mode
        if (
            hasattr(self.cli_instance, "simulate_mode")
            and self.cli_instance.simulate_mode
        ):
            print("🎭 MODO SIMULAÇÃO ATIVO - respostas simuladas, contexto mantido")

        print("=" * 60)
        print(
            f"🛡️ Proteção ativa: max {self.max_consecutive_errors} erros consecutivos, {self.max_interactions_per_session} interações/sessão"
        )
        print(
            f"⚡ Rate Limit: min {self.min_interaction_interval}s entre interações (anti-spam)"
        )
        print("=" * 60)

        while True and not self.emergency_stop:
            try:
                # Multi-line input support
                user_input = self._get_multiline_input()

                if user_input.lower() in ["exit", "quit", "sair"]:
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
                
                # Handle compound commands like "prompt save"
                if user_input.lower().startswith("prompt "):
                    self._handle_prompt_command(user_input.lower())
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
                    if (
                        hasattr(self.cli_instance, "simulate_mode")
                        and self.cli_instance.simulate_mode
                    ):
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
        print(f"🆔 Agent ID: {self.cli_instance.agent_id}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")

        # Show environment/project if available
        if hasattr(self.cli_instance, "environment"):
            print(f"🌐 Environment: {self.cli_instance.environment}")
        if hasattr(self.cli_instance, "project"):
            print(f"📦 Project: {self.cli_instance.project}")

        # working_directory não é mais um atributo direto do cli_instance para todos os casos
        # Pode ser obtido via ConductorService se necessário, mas para o REPL, pode ser simplificado
        print("📂 Working Dir: N/A (gerenciado pelo ConductorService)")
        print("=" * 40)

    def _show_conversation_history(self):
        """Show conversation history."""
        print("\n💬 === HISTÓRICO DE CONVERSAS ===")

        # Obter histórico diretamente do cli_instance (que delega ao ConductorService)
        history = self.cli_instance.get_conversation_history()
        if not history:
            print("📭 Nenhuma mensagem no histórico")
        else:
            # SAFETY: Ensure chronological order (oldest first, newest last)
            # Sort by timestamp if available, otherwise keep original order
            try:
                # Try to sort by timestamp if available
                sorted_history = sorted(history, key=lambda x: x.get("timestamp", 0) or 0)
            except (TypeError, ValueError):
                # If sorting fails, keep original order
                sorted_history = history

            for i, msg in enumerate(sorted_history, 1):
                print(f"\n--- Mensagem {i} ---")

                # Get user input with fallbacks (same as PromptEngine)
                user_input = (
                    msg.get("user_input", "") or
                    msg.get("prompt", "") or
                    msg.get("user", "") or
                    "N/A"
                )

                # Get AI response with fallbacks (same as PromptEngine)
                ai_response = (
                    msg.get("ai_response", "") or
                    msg.get("response", "") or
                    msg.get("assistant", "") or
                    msg.get("output", "") or
                    msg.get("summary", "") or
                    "N/A"
                )

                print(f"👤 User: {user_input}")
                print(f"🤖 Assistant: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
        print("=" * 50)

    def _check_rate_limiting(self) -> bool:
        """Check only rate limiting (separate from other safety limits)."""
        if self.last_interaction_time > 0:  # Skip check for first interaction
            current_time = time.time()
            time_since_last = current_time - self.last_interaction_time
            if time_since_last < self.min_interaction_interval:
                remaining = self.min_interaction_interval - time_since_last
                print(
                    f"⚡ RATE LIMIT: Aguarde {remaining:.1f}s - interações muito rápidas não são humanas"
                )
                return False
        return True

    def _check_non_rate_limits(self) -> bool:
        """Check safety limits excluding rate limiting."""
        current_time = time.time()

        # Check session duration
        if current_time - self.session_start_time > self.max_session_duration:
            print(
                f"🚨 LIMITE DE SESSÃO EXCEDIDO ({self.max_session_duration/60:.0f} min)"
            )
            print("   Sessão encerrada por segurança. Reinicie para continuar.")
            return False

        # Check total interactions
        if self.total_interactions >= self.max_interactions_per_session:
            print(
                f"🚨 LIMITE DE INTERAÇÕES EXCEDIDO ({self.max_interactions_per_session})"
            )
            print("   Sessão encerrada por segurança. Reinicie para continuar.")
            return False

        # Check consecutive errors (circuit breaker)
        if self.consecutive_errors >= self.max_consecutive_errors:
            time_since_error = current_time - self.last_error_time
            if time_since_error < self.error_reset_time:
                remaining = self.error_reset_time - time_since_error
                print(
                    f"🛡️ CIRCUIT BREAKER ATIVO - aguarde {remaining:.0f}s ou use 'reset'"
                )
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
            print(
                f"🚨 CIRCUIT BREAKER ATIVADO após {self.consecutive_errors} erros consecutivos"
            )
            print(f"   Aguarde {self.error_reset_time}s ou use 'reset' para continuar")

    def _handle_success(self):
        """Handle successful interaction."""
        self.consecutive_errors = 0  # Reset error counter on success

    def _show_safety_status(self):
        """Show current safety status."""
        current_time = time.time()
        session_duration = current_time - self.session_start_time

        print("\n🛡️ === STATUS DE SEGURANÇA ===")
        print(
            f"⏱️ Duração da sessão: {session_duration/60:.1f}/{self.max_session_duration/60:.0f} min"
        )
        print(
            f"💬 Interações: {self.total_interactions}/{self.max_interactions_per_session}"
        )
        print(
            f"❌ Erros consecutivos: {self.consecutive_errors}/{self.max_consecutive_errors}"
        )

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

        # Delegar limpeza ao cli_instance
        if self.cli_instance.clear_conversation_history():
            print("✅ Histórico limpo")
        else:
            print("❌ Falha ao limpar histórico")

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

        if hasattr(self.cli_instance, "get_output_scope"):
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
        print(f"🆔 Agent ID: {self.cli_instance.agent_id}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")
        print(f"🔧 Available Tools: {self.cli_instance.get_available_tools()}")

        if hasattr(self.cli_instance, "simulate_mode"):
            print(f"🎭 Simulation Mode: {self.cli_instance.simulate_mode}")

        print("=" * 50)

    def _show_full_prompt(self):
        """Show the complete prompt that would be sent to the AI provider."""
        self._show_prompt_internal(save_to_file=False)

    def _handle_prompt_command(self, command: str):
        """Handle prompt-related commands like 'prompt save'."""
        parts = command.split()
        if len(parts) == 2 and parts[1] == "save":
            self._show_full_prompt_and_save()
        else:
            print("❌ Comando desconhecido. Use:")
            print("   • prompt - Ver prompt completo")
            print("   • prompt save - Ver e salvar prompt em arquivo .md")

    def _show_full_prompt_and_save(self):
        """Show the complete prompt and save to file."""
        self._show_prompt_internal(save_to_file=True)
    
    def _show_prompt_internal(self, save_to_file: bool = False):
        """Internal method to show prompt with optional saving."""
        title = "PROMPT COMPLETO (SALVANDO)" if save_to_file else "PROMPT COMPLETO"
        print(f"\n📝 === {title} ===")
        
        try:
            from src.container import container
            agent_discovery_service = container.get_agent_discovery_service()
            
            # First show the conversation history count
            history = self.cli_instance.get_conversation_history()
            print(f"\n💬 Histórico: {len(history)} interações anteriores salvas")
            
            # Get agent_id from CLI instance
            agent_id = getattr(self.cli_instance, 'agent_id', 'unknown_agent')
            meta = getattr(self.cli_instance, 'meta', False)
            new_agent_id = getattr(self.cli_instance, 'new_agent_id', None)
            
            if not save_to_file:
                print("\n💡 Dica: Use 'prompt save' para salvar em arquivo .md")
            
            # Get the complete prompt using the unified function
            prompt = agent_discovery_service.get_full_prompt(
                agent_id=agent_id,
                sample_message="exemplo de mensagem para demonstração do prompt",
                meta=meta,
                new_agent_id=new_agent_id,
                current_message=None,  # Use sample message for display
                save_to_file=save_to_file
            )
            
            print("\n🤖 Este é o prompt completo que seria enviado para Claude/Gemini:")
            print("-" * 80)
            print(prompt)
            print("-" * 80)
            print(f"📊 Tamanho do prompt: {len(prompt)} caracteres")
            
        except Exception as e:
            print(f"❌ Erro ao gerar prompt: {e}")
            print("💡 Talvez o agente não esteja configurado corretamente")
        
        print("=" * 50)

    def _handle_error(self):
        """Handle error occurrence for circuit breaker."""
        self.consecutive_errors += 1
        self.last_error_time = time.time()

        if self.consecutive_errors >= self.max_consecutive_errors:
            print(
                f"🚨 CIRCUIT BREAKER ATIVADO após {self.consecutive_errors} erros consecutivos"
            )
            print(f"   Aguarde {self.error_reset_time}s ou use 'reset' para continuar")

    def _handle_success(self):
        """Handle successful interaction."""
        self.consecutive_errors = 0  # Reset error counter on success

    def _show_safety_status(self):
        """Show current safety status."""
        current_time = time.time()
        session_duration = current_time - self.session_start_time

        print("\n🛡️ === STATUS DE SEGURANÇA ===")
        print(
            f"⏱️ Duração da sessão: {session_duration/60:.1f}/{self.max_session_duration/60:.0f} min"
        )
        print(
            f"💬 Interações: {self.total_interactions}/{self.max_interactions_per_session}"
        )
        print(
            f"❌ Erros consecutivos: {self.consecutive_errors}/{self.max_consecutive_errors}"
        )

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
