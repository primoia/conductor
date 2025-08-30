#!/usr/bin/env python3
"""
Admin CLI - Meta-Agent Management

This CLI provides access to meta-agents for framework management.
It acts as a thin interface that delegates to the core business logic.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.container import container
from src.core.observability import configure_logging
from src.core.agent_logic import AgentLogic
from src.core.domain import AgentNotEmbodied
from src.core.exceptions import (
    ConductorException, AgentNotFoundError, LLMClientError, StatePersistenceError
)


class AdminCLI:
    """
    Admin CLI class that provides a thin interface to agent logic.
    
    This class handles:
    - Argument parsing
    - Logging setup  
    - Delegation to AgentLogic
    - Error handling and user feedback
    """
    
    def __init__(self, agent_id: str, ai_provider: str = None, timeout: int = 90, 
                 state_provider: str = 'file', debug_mode: bool = False):
        """Initialize Admin CLI."""
        self.logger = configure_logging(debug_mode, f"admin_{agent_id}")
        self.debug_mode = debug_mode
        
        # Get agent logic from container
        self.agent_logic = container.create_agent_logic(
            state_provider=state_provider,
            ai_provider=ai_provider or 'claude',
            timeout=timeout
        )
        
        # Store CLI-specific state
        self.destination_path = None
        self.simulate_mode = False
        
        # Embody the meta-agent
        self._embody_meta_agent(agent_id)
    
    def _embody_meta_agent(self, agent_id: str):
        """Embody a meta-agent using the container."""
        try:
            # Resolve paths for meta-agent
            agent_home_path, project_root_path = container.resolve_agent_paths(
                "_common", "_common", agent_id
            )
            
            # Embody the agent
            success = self.agent_logic.embody_agent(
                environment="_common",
                project="_common", 
                agent_id=agent_id,
                agent_home_path=agent_home_path,
                project_root_path=project_root_path
            )
            
            if success:
                print(f"✅ Successfully embodied meta-agent: {agent_id}")
                self.logger.info(f"Embodied meta-agent: {agent_id}")
                
                # Setup LLM client reference for tools access
                if hasattr(self.agent_logic.llm_client, 'genesis_agent'):
                    # For compatibility with existing tooling
                    self.agent_logic.llm_client.genesis_agent = self.agent_logic
                
            else:
                raise Exception("Failed to embody meta-agent")
                
        except Exception as e:
            self.logger.error(f"Failed to embody meta-agent {agent_id}: {e}")
            raise
    
    @property
    def embodied(self) -> bool:
        """Check if agent is embodied."""
        return self.agent_logic.is_embodied()
    
    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Send a message to the meta-agent."""
        if not self.embodied:
            return "❌ No agent embodied."
        
        try:
            # Add destination path if available
            enhanced_message = message
            if self.destination_path:
                enhanced_message = f"DESTINATION_PATH={self.destination_path}\n\n{message}"
                self.logger.info(f"Enhanced message with destination path: {self.destination_path}")
            
            # Handle debug mode - save input without calling provider
            if debug_save_input:
                self._save_debug_input(enhanced_message)
                return "✅ DEBUG MODE: Input captured and saved. Provider NOT called."
            
            # Handle simulation mode
            if self.simulate_mode:
                return self._simulate_response(enhanced_message)
            
            # Normal chat interaction
            self.logger.info(f"Processing chat message: {message[:100]}...")
            response = self.agent_logic.chat(enhanced_message)
            self.logger.info(f"Chat response received: {len(response) if response else 0} chars")
            
            return response
            
        except AgentNotEmbodied as e:
            return f"❌ {str(e)}"
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"❌ Error in chat: {e}"
    
    def save_agent_state(self):
        """Save agent state."""
        if not self.embodied:
            print("⚠️  No agent state to save")
            return
        
        try:
            success = self.agent_logic.save_agent_state()
            if success:
                self.logger.info("Agent state saved successfully")
            else:
                print("❌ Failed to save state")
                self.logger.error("Failed to save agent state")
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
            self.logger.error(f"Failed to save state: {e}")
    
    def get_available_tools(self) -> list:
        """Get available tools from agent logic."""
        return self.agent_logic.get_available_tools()
    
    def _save_debug_input(self, message: str):
        """Save debug input to file for analysis."""
        import os
        from datetime import datetime
        
        debug_dir = "/tmp/admin_debug"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"{debug_dir}/input_final_{timestamp}.txt"
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=== DEBUG: INPUT COMPLETO PARA PROVIDER ===\n\n")
            f.write(f"Enhanced Input: {message}\n\n")
            # Add more context as needed
        
        self.logger.info(f"DEBUG: Input completo salvo em {debug_file}")
        print(f"🔍 DEBUG: Contexto completo salvo em {debug_file}")
    
    def _simulate_response(self, message: str) -> str:
        """Generate simulated response."""
        # Add to conversation history to maintain context
        if hasattr(self.agent_logic.llm_client, 'conversation_history'):
            import time
            self.agent_logic.llm_client.conversation_history.append({
                'prompt': message,
                'response': f"[SIMULATED] Resposta simulada para: {message}",
                'timestamp': time.time()
            })
            
            # Save state automatically
            try:
                self.agent_logic.save_agent_state()
                self.logger.debug("State saved automatically in simulation mode")
            except Exception as save_error:
                self.logger.warning(f"Failed to save state in simulation mode: {save_error}")
        
        return f"""🎭 [MODO SIMULAÇÃO] 

Olá! Sou o {self.agent_logic.get_current_agent() or 'AgentCreator_Agent'} em modo simulação.

Recebi sua mensagem: "{message}"

Esta é uma resposta simulada que não chama o provider real. O contexto da conversa está sendo mantido para que você possa usar o comando 'debug' para ver todo o histórico acumulado.

Para ver o contexto completo, digite 'debug' no REPL.

---
💡 Dica: Use 'debug' para ver todo o contexto que seria enviado ao provider
📊 Use 'history' para ver o histórico de conversas simuladas
"""


def start_repl_session(admin_cli: AdminCLI):
    """Start interactive REPL session."""
    print(f"\n🤖 Iniciando sessão REPL para admin")
    print("💬 Digite 'exit', 'quit' ou 'sair' para encerrar")
    print("🔍 Digite 'debug' para ver contexto completo")
    print("📝 Digite 'state' para ver o estado atual")
    print("📊 Digite 'history' para ver histórico de conversa") 
    print("🗑️  Digite 'clear' para limpar todo o histórico")
    print("💾 Digite 'save' para salvar estado manualmente")
    
    if admin_cli.simulate_mode:
        print("🎭 MODO SIMULAÇÃO ATIVO - respostas simuladas, contexto mantido")
    
    print("=" * 60)
    
    while True:
        try:
            user_input = input(f"\n[admin]> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'sair']:
                print("👋 Encerrando sessão REPL...")
                break
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() == 'debug':
                _show_debug_info(admin_cli)
                continue
            elif user_input.lower() == 'state': 
                _show_agent_state(admin_cli)
                continue
            elif user_input.lower() == 'history':
                _show_conversation_history(admin_cli)
                continue
            elif user_input.lower() == 'clear':
                _clear_conversation_history(admin_cli)
                continue
            elif user_input.lower() == 'save':
                admin_cli.save_agent_state()
                continue
            
            # Normal chat
            print("🤔 Processando...")
            response = admin_cli.chat(user_input)
            
            if admin_cli.simulate_mode:
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


def _show_debug_info(admin_cli: AdminCLI):
    """Show debug information."""
    print("\n🔍 === DEBUG: INFORMAÇÕES DO AGENTE ===")
    print(f"🆔 Agent ID: {admin_cli.agent_logic.get_current_agent()}")
    print(f"✅ Embodied: {admin_cli.embodied}")
    print(f"🔧 Available Tools: {admin_cli.get_available_tools()}")
    print(f"🎭 Simulation Mode: {admin_cli.simulate_mode}")
    print("=" * 50)


def _show_agent_state(admin_cli: AdminCLI):
    """Show current agent state."""
    print("\n📊 === ESTADO ATUAL DO AGENTE ===")
    print(f"🆔 Agent ID: {admin_cli.agent_logic.get_current_agent()}")
    print(f"✅ Embodied: {admin_cli.embodied}")
    print(f"📂 Working Dir: {admin_cli.agent_logic.working_directory}")
    print("=" * 40)


def _show_conversation_history(admin_cli: AdminCLI):
    """Show conversation history."""
    print("\n💬 === HISTÓRICO DE CONVERSAS ===")
    
    if hasattr(admin_cli.agent_logic.llm_client, 'conversation_history'):
        history = admin_cli.agent_logic.llm_client.conversation_history
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


def _clear_conversation_history(admin_cli: AdminCLI):
    """Clear conversation history."""
    print("\n🗑️ === LIMPANDO HISTÓRICO ===")
    
    if hasattr(admin_cli.agent_logic.llm_client, 'conversation_history'):
        history_count = len(admin_cli.agent_logic.llm_client.conversation_history)
        admin_cli.agent_logic.llm_client.conversation_history.clear()
        admin_cli.agent_logic.save_agent_state()
        print(f"✅ Histórico limpo: {history_count} mensagens removidas")
    else:
        print("❌ Histórico não disponível para limpeza")
    
    print("=" * 40)


def main():
    """Main function for admin CLI."""
    parser = argparse.ArgumentParser(
        description='Admin CLI - Meta-Agent Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.cli.admin --agent AgentCreator_Agent --repl
    python -m src.cli.admin --agent AgentCreator_Agent --input "Create an agent"
        """
    )
    
    parser.add_argument('--agent', type=str, required=True,
                        help='Meta-agent ID to embody (required)')
    parser.add_argument('--ai-provider', type=str, default=None, 
                        choices=['claude', 'gemini'], 
                        help='AI provider override')
    parser.add_argument('--repl', action='store_true', 
                        help='Start interactive REPL')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--input', type=str, default=None,
                        help='Input message to send to agent')
    parser.add_argument('--destination-path', type=str, default=None,
                        help='Destination path for agent creation')
    parser.add_argument('--timeout', type=int, default=90,
                        help='Timeout in seconds for AI operations')
    parser.add_argument('--debug-input', action='store_true',
                        help='DEBUG: Save input without calling provider')
    parser.add_argument('--simulate-chat', action='store_true',
                        help='Simulate responses without calling provider')
    parser.add_argument('--state-provider', type=str, default='file', 
                        choices=['file', 'mongo'],
                        help='State persistence provider')
    
    args = parser.parse_args()
    
    if args.simulate_chat:
        print("""
🎭 MODO SIMULAÇÃO ATIVADO

Este modo permite simular conversas sem chamar o provider real,
mantendo o contexto da conversa para análise.
""")
    
    try:
        print(f"🚀 Iniciando Admin CLI")
        print(f"   Meta-agent: {args.agent}")
        if args.debug:
            print(f"   Debug mode: enabled")
        
        # Initialize admin CLI
        admin_cli = AdminCLI(
            agent_id=args.agent,
            ai_provider=args.ai_provider,
            timeout=args.timeout,
            state_provider=args.state_provider,
            debug_mode=args.debug
        )
        
        if not admin_cli.embodied:
            print(f"❌ Failed to embody meta-agent: {args.agent}")
            sys.exit(1)
        
        # Configure simulation mode
        if args.simulate_chat:
            admin_cli.simulate_mode = True
            print(f"🎭 Modo simulação ativado")
        
        # Set destination path for AgentCreator_Agent
        if args.destination_path:
            admin_cli.destination_path = args.destination_path
        
        print(f"🔓 No output restrictions (meta-agent)")
        
        # Handle different execution modes
        if args.repl:
            start_repl_session(admin_cli)
        elif args.input:
            print(f"\n🤖 Processing input for {args.agent}:")
            print(f"📝 Input: {args.input}")
            if args.destination_path:
                print(f"📍 Destination: {args.destination_path}")
            print("-" * 60)
            
            response = admin_cli.chat(args.input, debug_save_input=args.debug_input)
            print("\n📄 Response:")
            print("=" * 60)
            print(response)
            print("=" * 60)
            
            admin_cli.save_agent_state()
        else:
            print("\n💡 Tip: Use --repl for interactive mode or --input for single message")
            print("🤖 Meta-agent ready for programmatic use")
        
        print("\n👋 Admin CLI session completed")
        
    except AgentNotFoundError as e:
        print(f"❌ ERRO: {e}", file=sys.stderr)
        sys.exit(1)
    except LLMClientError as e:
        print(f"❌ ERRO DE COMUNICAÇÃO COM IA: {e}", file=sys.stderr)
        sys.exit(1)
    except StatePersistenceError as e:
        print(f"❌ ERRO DE PERSISTÊNCIA: {e}", file=sys.stderr)
        sys.exit(1)
    except ConductorException as e:
        print(f"❌ ERRO INESPERADO: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()