#!/usr/bin/env python3
"""
Agent CLI - Project Agent Management

This CLI provides access to project-specific agents.
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


class AgentCLI:
    """
    Agent CLI class for project agents.
    
    This class handles:
    - Argument parsing
    - Logging setup
    - Delegation to AgentLogic
    - Error handling and user feedback
    """
    
    def __init__(self, environment: str, project: str, agent_id: str, 
                 ai_provider: str = None, timeout: int = 120, 
                 state_provider: str = 'file', debug_mode: bool = False):
        """Initialize Agent CLI."""
        self.logger = configure_logging(debug_mode, f"agent_{agent_id}")
        self.debug_mode = debug_mode
        
        # Get agent logic from container
        self.agent_logic = container.create_agent_logic(
            state_provider=state_provider,
            ai_provider=ai_provider or 'claude',
            timeout=timeout
        )
        
        # Embody the project agent
        self._embody_project_agent(environment, project, agent_id)
    
    def _embody_project_agent(self, environment: str, project: str, agent_id: str):
        """Embody a project agent using the container."""
        try:
            # Resolve paths for project agent
            agent_home_path, project_root_path = container.resolve_agent_paths(
                environment, project, agent_id
            )
            
            # Embody the agent
            success = self.agent_logic.embody_agent(
                environment=environment,
                project=project,
                agent_id=agent_id,
                agent_home_path=agent_home_path,
                project_root_path=project_root_path
            )
            
            if success:
                print(f"✅ Successfully embodied project agent: {agent_id}")
                print(f"📍 Environment: {environment}")
                print(f"📦 Project: {project}")
                print(f"📂 Working Directory: {project_root_path}")
                self.logger.info(f"Embodied project agent: {agent_id}")
                
                # Setup LLM client reference for tools access
                if hasattr(self.agent_logic.llm_client, 'genesis_agent'):
                    self.agent_logic.llm_client.genesis_agent = self.agent_logic
                
            else:
                raise Exception("Failed to embody project agent")
                
        except Exception as e:
            self.logger.error(f"Failed to embody project agent {agent_id}: {e}")
            raise
    
    @property
    def embodied(self) -> bool:
        """Check if agent is embodied."""
        return self.agent_logic.is_embodied()
    
    def chat(self, message: str) -> str:
        """Send a message to the project agent."""
        if not self.embodied:
            return "❌ No agent embodied."
        
        try:
            self.logger.info(f"Processing chat message: {message[:100]}...")
            response = self.agent_logic.chat(message)
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
    
    def get_output_scope(self) -> list:
        """Get output scope restrictions."""
        return self.agent_logic.output_scope or []


def start_repl_session(agent_cli: AgentCLI, agent_name: str):
    """Start interactive REPL session."""
    print(f"\n🤖 Iniciando sessão REPL para {agent_name}")
    print("💬 Digite 'exit', 'quit' ou 'sair' para encerrar")
    print("📝 Digite 'state' para ver o estado atual")
    print("📊 Digite 'history' para ver histórico de conversa")
    print("🗑️  Digite 'clear' para limpar todo o histórico")
    print("💾 Digite 'save' para salvar estado manualmente")
    print("🔧 Digite 'tools' para ver ferramentas disponíveis")
    print("🎯 Digite 'scope' para ver escopo de output")
    print("=" * 60)
    
    while True:
        try:
            user_input = input(f"\n[{agent_name}]> ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'sair']:
                print("👋 Encerrando sessão REPL...")
                break
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() == 'state':
                _show_agent_state(agent_cli)
                continue
            elif user_input.lower() == 'history':
                _show_conversation_history(agent_cli)
                continue
            elif user_input.lower() == 'clear':
                _clear_conversation_history(agent_cli)
                continue
            elif user_input.lower() == 'save':
                agent_cli.save_agent_state()
                continue
            elif user_input.lower() == 'tools':
                _show_available_tools(agent_cli)
                continue
            elif user_input.lower() == 'scope':
                _show_output_scope(agent_cli)
                continue
            
            # Normal chat
            print("🤔 Processando...")
            response = agent_cli.chat(user_input)
            
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


def _show_agent_state(agent_cli: AgentCLI):
    """Show current agent state."""
    print("\n📊 === ESTADO ATUAL DO AGENTE ===")
    print(f"🆔 Agent ID: {agent_cli.agent_logic.get_current_agent()}")
    print(f"✅ Embodied: {agent_cli.embodied}")
    print(f"🌐 Environment: {agent_cli.agent_logic.environment}")
    print(f"📦 Project: {agent_cli.agent_logic.project}")
    print(f"📂 Working Dir: {agent_cli.agent_logic.working_directory}")
    print("=" * 40)


def _show_conversation_history(agent_cli: AgentCLI):
    """Show conversation history."""
    print("\n💬 === HISTÓRICO DE CONVERSAS ===")
    
    if hasattr(agent_cli.agent_logic.llm_client, 'conversation_history'):
        history = agent_cli.agent_logic.llm_client.conversation_history
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


def _clear_conversation_history(agent_cli: AgentCLI):
    """Clear conversation history."""
    print("\n🗑️ === LIMPANDO HISTÓRICO ===")
    
    if hasattr(agent_cli.agent_logic.llm_client, 'conversation_history'):
        history_count = len(agent_cli.agent_logic.llm_client.conversation_history)
        agent_cli.agent_logic.llm_client.conversation_history.clear()
        agent_cli.agent_logic.save_agent_state()
        print(f"✅ Histórico limpo: {history_count} mensagens removidas")
    else:
        print("❌ Histórico não disponível para limpeza")
    
    print("=" * 40)


def _show_available_tools(agent_cli: AgentCLI):
    """Show available tools."""
    print("\n🔧 === FERRAMENTAS DISPONÍVEIS ===")
    tools = agent_cli.get_available_tools()
    if tools:
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool}")
    else:
        print("🚫 Nenhuma ferramenta configurada")
    print("=" * 40)


def _show_output_scope(agent_cli: AgentCLI):
    """Show output scope restrictions.""" 
    print("\n🎯 === ESCOPO DE OUTPUT ===")
    scope = agent_cli.get_output_scope()
    if scope:
        print("📝 Este agente está restrito aos seguintes arquivos/diretórios:")
        for i, path in enumerate(scope, 1):
            print(f"{i}. {path}")
    else:
        print("🔓 Sem restrições de escopo (meta-agent)")
    print("=" * 40)


def main():
    """Main function for agent CLI."""
    parser = argparse.ArgumentParser(
        description='Agent CLI - Project Agent Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.cli.agent --environment develop --project myproject --agent MyAgent --repl
    python -m src.cli.agent --environment develop --project myproject --agent MyAgent --input "Hello"
        """
    )
    
    parser.add_argument('--environment', type=str, required=True,
                        help='Environment name (develop, main, etc.)')
    parser.add_argument('--project', type=str, required=True,
                        help='Project name')
    parser.add_argument('--agent', type=str, required=True,
                        help='Agent ID to embody')
    parser.add_argument('--ai-provider', type=str, default=None,
                        choices=['claude', 'gemini'],
                        help='AI provider override')
    parser.add_argument('--repl', action='store_true',
                        help='Start interactive REPL')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--input', type=str, default=None,
                        help='Input message to send to agent')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Timeout in seconds for AI operations')
    parser.add_argument('--state-provider', type=str, default='file',
                        choices=['file', 'mongo'],
                        help='State persistence provider')
    
    args = parser.parse_args()
    
    try:
        print(f"🚀 Iniciando Agent CLI")
        print(f"   Environment: {args.environment}")
        print(f"   Project: {args.project}")
        print(f"   Agent: {args.agent}")
        if args.debug:
            print(f"   Debug mode: enabled")
        
        # Initialize agent CLI
        agent_cli = AgentCLI(
            environment=args.environment,
            project=args.project,
            agent_id=args.agent,
            ai_provider=args.ai_provider,
            timeout=args.timeout,
            state_provider=args.state_provider,
            debug_mode=args.debug
        )
        
        if not agent_cli.embodied:
            print(f"❌ Failed to embody agent: {args.agent}")
            sys.exit(1)
        
        # Show output scope if restricted
        scope = agent_cli.get_output_scope()
        if scope:
            print(f"🎯 Output scope: {', '.join(scope)}")
        else:
            print(f"🔓 No output restrictions")
        
        # Handle different execution modes
        if args.repl:
            start_repl_session(agent_cli, args.agent)
        elif args.input:
            print(f"\n🤖 Processing input for {args.agent}:")
            print(f"📝 Input: {args.input}")
            print("-" * 60)
            
            response = agent_cli.chat(args.input)
            print("\n📄 Response:")
            print("=" * 60)
            print(response)
            print("=" * 60)
            
            agent_cli.save_agent_state()
        else:
            print("\n💡 Tip: Use --repl for interactive mode or --input for single message")
            print("🤖 Agent ready for programmatic use")
        
        print("\n👋 Agent CLI session completed")
        
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
        if 'args' in locals() and args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()