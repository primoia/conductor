"""
REPL Manager - Shared REPL Session Handling

Provides unified interactive session management for all CLI interfaces.
"""

from typing import Dict, Callable, Any


class REPLManager:
    """Manages REPL sessions with customizable commands and behavior."""
    
    def __init__(self, agent_name: str, cli_instance: Any):
        """
        Initialize REPL manager.
        
        Args:
            agent_name: Display name for the REPL prompt
            cli_instance: CLI instance that provides agent interaction methods
        """
        self.agent_name = agent_name
        self.cli_instance = cli_instance
        self.custom_commands = {}
        self._setup_default_commands()
    
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
        
        if custom_help:
            print(custom_help)
        
        # Check for simulation mode
        if hasattr(self.cli_instance, 'simulate_mode') and self.cli_instance.simulate_mode:
            print("🎭 MODO SIMULAÇÃO ATIVO - respostas simuladas, contexto mantido")
        
        print("=" * 60)
        
        while True:
            try:
                user_input = input(f"\n[{self.agent_name}]> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'sair']:
                    print("👋 Encerrando sessão REPL...")
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in self.custom_commands:
                    self.custom_commands[user_input.lower()]()
                    continue
                
                # Normal chat
                print("🤔 Processando...")
                response = self.cli_instance.chat(user_input)
                
                # Check for simulation mode in response display
                if hasattr(self.cli_instance, 'simulate_mode') and self.cli_instance.simulate_mode:
                    print("🎭 Resposta Simulada:")
                else:
                    print("🤖 Resposta:")
                print("-" * 40)
                print(response)
                print("-" * 40)
                
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